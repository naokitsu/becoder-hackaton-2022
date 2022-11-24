from pydriller import Repository, Git, Commit

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
    tmp = Repository('/home/narinai/Downloads/memos')



if __name__ == '__main__':
    main()
