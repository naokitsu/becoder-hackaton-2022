import os
import shutil
import sys
from math import log2

import altair as alt
import plotly_express as px

import pandas as pd
import streamlit as st
from pandas import DataFrame

from pydriller import Repository, Git, ModifiedFile


class FileObserver:
    """
    Class that track filename changes and hold their **current** ids

    Класс, который отслеживает изменения имен файлов и хранит их **текущие** идентификаторы.
    """
    _dictionary = {}
    _free_id = 0

    def _get_free_id(self):
        """
        Get free id for new file

        Получить свободный идентификатор для нового файла
        :return: Free id
        """
        self._free_id += 1
        return self._free_id

    def _add_file(self, name: str, file_id: int):
        """
        Add new entry in dictionary

        Добавить новую запись в словарь
        :param name: File name
        :param file_id: File id
        """
        if name in self._dictionary:
            return
        self._dictionary[name] = file_id

    def register_new_file(self, name: str):
        """
        Register new file with free id

        Зарегистрировать новый файл со свободным идентификатором
        :param name: File name
        """
        self._add_file(name, self._get_free_id())

    def rename_file(self, old_name: str, new_name: str):
        """
        Rename file

        Переименовать файл
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

        Остановить отслеживание файла
        :param name: File name
        """
        self._dictionary.pop(name)

    def get_id(self, name: str):
        """
        Get id from dictionary by name

        Получить идентификатор из словаря по имени
        :param name: File name
        :return: Id of file
        """
        return self._dictionary[name]

    def update_states(self, file: ModifiedFile):
        """
        Update state of file

        Обновить состояние файла
        :param file: File
        :return: None or 1 (if file should be deleted after)
        """
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

    Структура для хранения данных для анализа
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

    Класс, который отслеживает коммиты и ошибки в файле
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
        """
        Create a Footprint object that represents current state

        Создать объект Footprint, представляющий текущее состояние.
        :param username: Username
        :param file_id: File id
        :return: Footprint (File id, Username, Commits elapsed, Mistakes elapsed)
        (След (идентификатор файла, имя пользователя, истекшие фиксации, истекшие ошибки))
        """
        counter = self._dictionary[username][file_id]
        return Footprint(file_id, username, counter[0], counter[1])

    def get_dictionary(self):
        """
        Get Disctionary file, that's shall be needed in the future to get final states

        Получить файл словаря, который понадобится в будущем для получения конечных состояний
        :return: dictionary
        """
        return self._dictionary


def get_latest_commit(gr: Git, commits: dict):
    """
    Get the latest commit from the list

    Получить последнюю фиксацию из списка
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


def repo_clone(repo_str: str):
    """
    Streamlit wrapper for git

    Обертка для Streamlit для git
    :param repo_str: repository link
    :return:
    """
    st.title('Получение исходного кода')
    st.write("Клонирование репозитория")
    downloading_progress = st.progress(33)
    os.system(f"git clone {repo_str} cloned_repo")
    downloading_progress.progress(100)
    return "./cloned_repo"


@st.cache
def get_dataframe(repo_str):
    """
    Repack Footprints objects into the dataframe

    Переупаковать объекты Footprints в dataframe
    :param repo_str: Repository to compute
    :return:
    """
    final_prints, prints, data_observer = git_computation(repo_str)
    df = rapack_prints_into_dataframe(prints)
    df_final = rapack_prints_into_dataframe(final_prints)

    return df, df_final, data_observer


def rapack_prints_into_dataframe(prints):
    """
    Repack one Footprint objects into the dataframe

    Переупаковать один объект Footprint в dataframe
    :param prints: Footprints to compute
    :return:
    """
    authors_pd = []
    files_pd = []
    mistakes_pd = []
    commits_pd = []
    percent_pd = []
    for i in prints:
        if i.commits == 0:
            continue
        authors_pd.append(i.author)
        files_pd.append(i.file)
        mistakes_pd.append(i.mistakes)
        commits_pd.append(i.commits)
        percent_pd.append(i.mistakes / i.commits)
    df = pd.DataFrame({
        'Автор': authors_pd,
        'Номера файлов': files_pd,
        'Общее число комитов': commits_pd,
        'Ошибки': mistakes_pd,
        'Частота ошибки': percent_pd
    })
    return df


@st.cache
def git_computation(repo_str):
    """
    Compute Footprints from git repository

    Вычислить Footprints из репозитория git
    :param repo_str: Repository to compute
    :return:
    """
    gr = Git(repo_str)
    repo = Repository(repo_str)
    file_observer = FileObserver()
    file_tracker = FileTracker()
    buggy_commits = []
    prints = []
    i = 0
    for commit in repo.traverse_commits():
        for file in commit.modified_files:
            result = file_observer.update_states(file)
            if file.new_path is None:
                continue
            file_tracker.new_commit(commit.author.name, file_observer.get_id(file.new_path))
            if "fix" in commit.msg:
                latest_hash = get_latest_commit(gr, gr.get_commits_last_modified_lines(commit, file))
                if (latest_hash, file_observer.get_id(file.new_path)) not in buggy_commits:
                    file_tracker.new_mistake(gr.get_commit(latest_hash).author.name, file_observer.get_id(file.new_path))
                    buggy_commits.append((latest_hash, file_observer.get_id(file.new_path)))
            value_to_print = file_tracker.get_print(commit.author.name, file_observer.get_id(file.new_path))
            if value_to_print.commits > 1:
                prints.append(value_to_print)
            if result is not None:
                file_observer.remove_file(file.old_path)
        i += 1
    users_files = file_tracker.get_dictionary()
    final_prints = []
    for user in users_files:
        for file in users_files[user]:
            value_to_print = file_tracker.get_print(user, file)
            if value_to_print.commits > 1:
                final_prints.append(value_to_print)

    return final_prints, prints, file_observer


def draw_scatter_plot(df: DataFrame, x_str: str, y_str: str):
    """
    Draw a scatter plot from dataframe and calculate correlation coefficients

    Отрисовка точечной диаграммы из фрейма данных и рассчет коэффициентов корреляции
    :param df: Dataframe
    :param x_str: x axis
    :param y_str: y axis
    """
    plot = px.scatter(df, y=y_str, x=x_str, color="Автор",
                      hover_data=['Автор', "Номера файлов", "Ошибки", 'Общее число комитов', 'Частота ошибки'])
    st.plotly_chart(plot)
    st.write(df[x_str].corr(df[y_str]))


def main(repo_str: str):
    """
    Entry point

    Tочка входа
    :param repo_str: Repository to compute
    """
    if repo_str == "":
        return
    repo_str = repo_clone(repo_str)

    st.title('Обработка истории коммитов')
    df, df_final, data_observer = get_dataframe(repo_str)
    st.write(df)

    draw_scatter_plot(df, 'Общее число комитов', "Ошибки")
    draw_scatter_plot(df, 'Общее число комитов', 'Частота ошибки')
    draw_scatter_plot(df, 'Номера файлов', 'Частота ошибки')

    all_authors = set(df["Автор"])
    selected = st.selectbox("Автор", all_authors, key=42)
    df_slice = df[df["Автор"] == selected]
    draw_scatter_plot(df_slice, 'Номера файлов', 'Частота ошибки')

    st.title('Только финальные состояния')
    st.write(df_final)
    draw_scatter_plot(df_final, 'Общее число комитов', "Ошибки")
    draw_scatter_plot(df_final, 'Общее число комитов', 'Частота ошибки')
    draw_scatter_plot(df_final, 'Номера файлов', 'Частота ошибки')

    all_authors_finals = set(df_final["Автор"])
    selected_finals = st.selectbox("Автор", all_authors_finals, key=32)
    df_slice_finals = df_final[df_final["Автор"] == selected_finals]
    draw_scatter_plot(df_slice_finals, 'Номера файлов', 'Частота ошибки')

    st.title("Оценка вероятности ошибки")
    all_authors_finals = set(df_final["Автор"])
    selected_est = st.selectbox("Автор", all_authors_finals, key=22)
    commited_file_path = st.text_input(label="Путь до файла")
    df_slice_est = df_final.loc[df_final['Автор'] == selected_est]
    df_slice_est = df_slice_est.loc[df_slice_est["Номера файлов"] == data_observer.get_id(commited_file_path)]
    error_chance = 0
    column = df_slice_est['Частота ошибки']
    st.text(f"Вероятность ошибки в файле {column.iat[0]*100}%")


if __name__ == '__main__':
    shutil.rmtree("./cloned_repo", True)
    st.title("Введите адрес репозитория (Локального или удаленного)")
    path = st.text_input(label="Адрес")
    main(path)
