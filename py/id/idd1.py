#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import argparse
import sqlite3
import typing as t
from pathlib import Path


def display_workers(people: t.List[t.Dict[str, t.Any]]) -> None:
    """
    Отобразить список работников.
    """
    # Проверить, что список работников не пуст.
    if people:
        # Заголовок таблицы.
        line = "+-{}-+-{}-+-{}-+-{}-+".format(
            "-" * 4,
            "-" * 30,
            "-" * 15,
            "-" * 15
        )
        print(line)
        print(
            "| {:^4} | {:^30} | {:^15} | {:^15} |".format(
                "№",
                "Фамилия и имя",
                "Номер",
                "День рождения"
            )
        )
        print(line)

        # Вывести данные о всех людях.
        for idx, worker in enumerate(people, 1):
            print(
                "| {:^4} | {:<30} | {:<15} | {:<15} |".format(
                    idx,
                    worker.get("name", ""),
                    worker.get("number", ""),
                    worker.get("birthday", "")
                )
            )
            print(line)

    else:
        print("Список пуст.")


def create_db(database_path: Path) -> None:
    """
    Создать базу данных.
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    # Создать таблицу с информацией о номерах телефонов.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS numbers (
            human_id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number INTEGER NOT NULL
        )
        """
    )
    # Создать таблицу с информацией о работниках.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS people (
            human_id INTEGER PRIMARY KEY AUTOINCREMENT,
            human_name TEXT NOT NULL,
            human_bd TEXT NOT NULL,
            FOREIGN KEY(human_id) REFERENCES numbers(human_id)
        )
        """
    )
    conn.close()


def add_worker(
    database_path: Path,
    name: str,
    number: int,
    birthday: str
) -> None:
    """
    Добавить человека в базу данных.
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT human_id FROM people WHERE human_name = ?
        """,
        (name,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            """
            INSERT INTO people (human_name, human_bd) VALUES (?, ?)
            """,
            (name, birthday)
        )
        worker_id = cursor.lastrowid

    else:
        worker_id = row[0]

    # Добавить информацию о новом человеке.
    cursor.execute(
        """
        INSERT INTO numbers (human_id, phone_number)
        VALUES (?, ?)
        """,
        (worker_id, number)
    )
    conn.commit()
    conn.close()


def select_all(database_path: Path) -> t.List[t.Dict[str, t.Any]]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT people.human_name, people.human_bd, numbers.phone
        FROM numbers
        INNER JOIN people ON people.human_id = numbers.human_id
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "name": row[0],
            "birthday": row[1],
            "number": row[2],
        }
        for row in rows
    ]


def find_worker(database_path: Path, name: str) -> t.List[t.Dict[str, t.Any]]:
    """
    Вывод на экран информации о человеке по фамилии.
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT people.human_name, people.human_bd, numbers.phone_number
        FROM numbers
        INNER JOIN people ON people.human_id = numbers.human_id
        WHERE people.human_name LIKE ? || '%'
        """,
        (name,)
    )
    rows = cursor.fetchall()
    conn.close()
    if len(rows) == 0:
        return []

    return [
        {
            "name": row[0],
            "birthday": row[1],
            "number": row[2],
        }
        for row in rows
    ]


def main(command_line=None):
    """
    Главная функция программы.
    """
    # Создать родительский парсер для определения имени файла.
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument(
        "--db",
        action="store",
        required=False,
        default=str(Path.cwd() / "workers.db"),
        help="The database file name"
    )

    # Создать основной парсер командной строки.
    parser = argparse.ArgumentParser("people")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Создать субпарсер для добавления работника.
    add = subparsers.add_parser(
        "add",
        parents=[file_parser],
        help="Add a new worker"
    )

    add.add_argument(
        "-na",
        "--name",
        action="store",
        required=True,
        help="The worker's name"
    )

    add.add_argument(
        "-n",
        "--number",
        type=int,
        action="store",
        help="The worker's number"
    )

    add.add_argument(
        "-bd",
        "--birthday",
        action="store",
        required=True,
        help="The worker's birthday"
    )

    # Создать субпарсер для отображения всех людей.
    display = subparsers.add_parser(
        "display",
        parents=[file_parser],
        help="Display all people"
    )

    # Создать субпарсер для поиска людей по имени.
    find = subparsers.add_parser(
        "find",
        parents=[file_parser],
        help="Find people by name"
    )

    find.add_argument(
        "-n",
        "--name",
        action="store",
        required=True,
        help="The name to search for"
    )

    # Выполнить разбор аргументов командной строки.
    args = parser.parse_args(command_line)

    # Получить путь к файлу базы данных.
    db_path = Path(args.db)
    create_db(db_path)

    if args.command == "add":
        add_worker(db_path, args.name, args.number, args.birthday
                   )
        # Отобразить всех работников.
    elif args.command == "display":
        display_workers(select_all(db_path))
    # Найти работников по имени.
    elif args.command == "find":
        display_workers(find_worker(db_path, args.name))


if __name__ == "__main__":
    main()

