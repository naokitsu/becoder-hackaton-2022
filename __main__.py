import sys

from pydriller import Repository, Git


def main():
    """
    Точка входа
    """
    """
    if len(sys.argv) != 2:
        print("Передайте репозиторий первым аргументом")
        return
    """
py
    gr = Git("/home/narinai/Downloads/memos")
    for commit in Repository('/home/narinai/Downloads/memos').traverse_commits():
        if not("fix" in commit.msg):
            continue
        print('Hash: {} \t\t\t Author:\t {} \t\t\t Message:\t {}'.format(commit.hash, commit.author.name, commit.msg))
        gr_commit = gr.get_commit(commit.hash)
        buggy_commits = gr.get_commits_last_modified_lines(gr_commit)
        print(buggy_commits)
        input()

if __name__ == '__main__':
    main()
