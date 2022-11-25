import os
import sys

from pydriller import Repository, Git, Commit, ModifiedFile
import matplotlib.pyplot as plt

class FileObserver:
    """
    Class that track filename changes and hold their **current** ids
    """
    _dictionary = {}
    _free_id = 0

    def _get_free_id(self):
        """
        Get free id for new file
        :return: Free id
        """
        self._free_id += 1
        return self._free_id

    def _add_file(self, name: str, file_id: int):
        """
        Add new entry in dictionary
        :param name: File name
        :param file_id: File id
        """
        if name in self._dictionary:
            return
        self._dictionary[name] = file_id

    def register_new_file(self, name: str):
        """
        Create new file with free id
        :param name: File name
        """
        self._add_file(name, self._get_free_id())

    def rename_file(self, old_name: str, new_name: str):
        """
        Rename file
        :param old_name: Old file name
        :param new_name: New File name
        """
        if old_name not in self._dictionary:
            self.register_new_file(new_name)
            return
        self._add_file(new_name, self._dictionary[old_name])
        self.remove_file(old_name)

    def remove_file(self, name: str):
        """
        Stop to track file
        :param name: File name
        """
        self._dictionary.pop(name)

    def get_id(self, name: str):
        return self._dictionary[name]

    def check_states(self, file: ModifiedFile):
        if file.old_path is None:
            self.register_new_file(file.new_path)
        elif file.new_path is None:
            return 1
        elif file.new_path != file.old_path:
            self.rename_file(file.old_path, file.new_path)
        else:
            if file.old_path not in self._dictionary:
                self.register_new_file(file.old_path)


class Footprint:
    """
    Structure to store data for analysis
    """
    author = ""
    file = 0
    mistakes = 0
    commits = 0

    def __init__(self, file, author, commits, mistakes):
        self.file = file
        self.author = author
        self.mistakes = mistakes
        self.commits = commits

    def print(self):
        print(f"{self.author} \t {self.file} \t {self.mistakes} \t {self.commits}")

class FileTracker:
    """
    Class that tracks commits and mistakes per file
    """
    _dictionary = None

    def __init__(self):
        self._dictionary = {}

    def new_commit(self, username: str, file_id: int):
        if username not in self._dictionary:
            self._dictionary[username] = {}
        if file_id not in self._dictionary[username]:
            self._dictionary[username][file_id] = [0, 0]
        self._dictionary[username][file_id][0] += 1

    def new_mistake(self, username: str, file_id: int):
        if username not in self._dictionary:
            self._dictionary[username] = {}
        if file_id not in self._dictionary[username]:
            self._dictionary[username][file_id] = [0, 0]
        self._dictionary[username][file_id][1] += 1

    def get_print(self, username: str, file_id: int):
        counter = self._dictionary[username][file_id]
        return Footprint(file_id, username, counter[0], counter[1])

    def try_to_make_print(self, username: str, file_id: int):
        counter = self._dictionary[username][file_id]
        if (counter[0]) % 1 == 0:
            return Footprint(file_id, username, counter[0], counter[1])
        else:
            return None


def get_latest_commit(gr: Git, commits: dict):
    """
    Get the latest commit from the list
    :param gr: Git wrapper
    :param commits: {'file': {'commit_hash', ... }}-like dictionary (output of get_commits_last_modified_lines)
    :return: latest commit from the list
    """
    # {'web/src/less/memo-editor.less': {'06f5a5788ed9e86edf5e2a4c4d418c1741c0a17d', ... }}
    latest_commit = None
    latest_date = None
    for i in commits:
        for j in commits[i]:
            commit = gr.get_commit(j)
            if latest_date is None or commit.committer_date > latest_date:
                latest_date = commit.committer_date
                latest_commit = j
    return latest_commit


def main(repo_str: str):
    """
    Точка входа
    """
    if repo_str.startswith("https://") or repo_str.startswith("git@github.com"):
        os.system(f"git clone {repo_str} cloned_repo")
        repo_str = "./cloned_repo"

    gr = Git(repo_str)
    repo = Repository(repo_str)
    file_observer = FileObserver()
    file_tracker = FileTracker()
    prints = []
    for commit in repo.traverse_commits():
        for file in commit.modified_files:
            result = file_observer.check_states(file)
            if file.new_path is None:
                continue
            file_tracker.new_commit(commit.author.name, file_observer.get_id(file.new_path))
            if "fix" in commit.msg:
                latest_hash = get_latest_commit(gr, gr.get_commits_last_modified_lines(commit, file))
                file_tracker.new_mistake(gr.get_commit(latest_hash).author.name, file_observer.get_id(file.new_path))
            attempt = file_tracker.try_to_make_print(commit.author.name, file_observer.get_id(file.new_path))
            if attempt is not None:
                prints.append(attempt)
            if result is not None:
                file_observer.remove_file(file.old_path)

    for i in prints:
        i.print()

    x = []
    y = []

    for i in prints:
        x.append(i.commits)
        y.append(i.mistakes)

    plt.plot(x, y, 'ro')
    #plt.axis([0, 6, 0, 20])
    plt.show()


if __name__ == '__main__':
    path = ""
    if len(sys.argv) != 2:
        print("Репозиторий не был передан первым аргументом, введите вручную:")
        path = input()
    else:
        path = sys.argv[1]
    main(path)
