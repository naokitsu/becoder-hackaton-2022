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
    gr = Git("/home/narinai/Downloads/memos")

    email_files = {}

    for commit in Repository('/home/narinai/Downloads/memos').traverse_commits():
        if not ("fix" in commit.msg):
            continue

        gr_commit = gr.get_commit(commit.hash)
        buggy_commits = gr.get_commits_last_modified_lines(gr_commit)
        for i in buggy_commits:
            for j in buggy_commits[i]:
                buggy_commit = gr.get_commit(j)
                if not(buggy_commit.author.email in email_files):
                    email_files[buggy_commit.author.email] = {}
                if not(i in email_files[buggy_commit.author.email]):
                    email_files[buggy_commit.author.email][i] = 0
                email_files[buggy_commit.author.email][i] += 1

    for user in email_files:
        print(f"\nCommits by {user} that were fixed:")
        for file in email_files[user]:
            print(f"{email_files[user][file]} times \t\t\t {file}")


if __name__ == '__main__':
    main()