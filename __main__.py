from pydriller import Repository, Git, Commit, ModifiedFile


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
            print(f"File {name} exists")
            raise f"Error"
        self._dictionary[name] = id

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
            self.remove_file(file.old_path)
        elif file.new_path != file.old_path:
            self.rename_file(file.old_path, file.new_path)


class Mistake:
    """
    Structure to store data for analysis
    """
    commit_hash = ""
    author = ""
    nth_mistakes = 0

    def __init__(self, commit_hash, author, nth_mistakes):
        self.commit_hash = commit_hash
        self.author = author
        self.nth_mistakes = nth_mistakes

    def increment(self):
        self.nth_mistakes += 1


class MistakeTracker:
    """
    Class that tracks user mistakes per file
    """
    _dictionary = None

    def __init__(self):
        self._dictionary = {}

    def new_mistake(self, commit_hash: str, username: str, file_id: int):
        if username not in self._dictionary:
            self._dictionary[username] = {}
        if file_id not in self._dictionary[username]:
            self._dictionary[username][file_id] = Mistake(commit_hash, username, 0)
        self._dictionary[username][file_id].increment()


def main():
    """
    Точка входа
    """
    """
    if len(sys.argv) != 2:
        print("Передайте репозиторий первым аргументом")
        return
    """
    gr = Git("/home/narinai/Downloads/memos")
    repo = Repository('/home/narinai/Downloads/memos')
    file_observer = FileObserver()
    for commits in repo.traverse_commits():
        for file in commits.modified_files:
            file_observer.check_states(file)


if __name__ == '__main__':
    main()
