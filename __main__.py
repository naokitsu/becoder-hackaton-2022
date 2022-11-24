import sys

from pydriller import Repository, Git, Commit


def increment_commit_count(gr_commit: Commit, email_files: {str, dict}, element):
    if not (gr_commit.author.name in email_files):
        email_files[gr_commit.author.name] = {}
    for files in gr_commit.modified_files:
        if not (files.new_path in email_files[gr_commit.author.name]):
            email_files[gr_commit.author.name][files.new_path] = [0, 0, gr_commit.hash]
        email_files[gr_commit.author.name][files.new_path][element] += 1

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

    # dict {name: str, dict {file: str, [errors: int, total: int] } }
    email_files = {}

    for commit in Repository('/home/narinai/Downloads/memos').traverse_commits():
        gr_commit = gr.get_commit(commit.hash)
        increment_commit_count(gr_commit, email_files, 1)

        if not ("fix" in commit.msg):
            continue

        for fixed_file in commit.modified_files:
            buggy_commits = gr.get_commits_last_modified_lines(gr_commit, fixed_file)
            for buggy_commit in buggy_commits:
                for i in buggy_commits[buggy_commit]:
                    increment_commit_count(gr.get_commit(i), email_files, 0)

    for user in email_files:
        print(f"\nCommits by {user} that were fixed:")
        for file in email_files[user]:
            print(f"{email_files[user][file]} \t {email_files[user][file][0] > email_files[user][file][1]} \t\t\t {file}")


if __name__ == '__main__':
    main()