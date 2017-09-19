"""
Site and Data Management Module
===============================

Available commands
------------------

- db list
- table list <database>
- table rows <database table>
- user add <username password>
- session clean
"""

import argparse
import csv
from decimal import Decimal
import glob
from io import StringIO
import os
import shutil
import sqlite3
import stat

import settings
from db import Database


def list_dbs():
    for f in glob.iglob("**/*.db", recursive=True):
        print(f)


def list_tables(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    for row in c.execute("SELECT * FROM sqlite_master"):
        print(row[1])
    conn.close()


def table_rows(db, table):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    for k, row in enumerate(c.execute(f"SELECT * FROM {table}")):
        print(row)
        if k > 0 and k % 10 == 0:
            a = input(f"{k}> ")
            if a:
                break
    conn.close()


def add_user(options):
    username, password = options
    db = Database(settings.SQLITE_DBNAME)
    db.signup(username, password)
    db.close()
    print(f"Added user: {username}")


def clean_sessions():
    db = Database(settings.SQLITE_DBNAME)
    cleaned = db.clean_expired_sessions()
    db.close()
    print(f"Cleaned {cleaned} old sessions")


def show_help(options):
    if len(options) == 0:
        print(__doc__)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Site and Data Management")
    parser.add_argument("command", metavar="command", type=str,
                        help="for the list of commands type: show help")
    parser.add_argument("options", metavar="option", type=str, nargs="+")
    args = parser.parse_args()
    if args.command == "show" and args.options[0] == "help":
        show_help(args.options[1:])
    elif (args.command == "user" and args.options[0] == "add" and
        len(args.options) == 3):
            add_user(args.options[1:])
    elif (args.command == "session" and args.options[0] == "clean" and
        len(args.options) == 1):
            clean_sessions()
    elif (args.command == "db" and args.options[0] == "list" and
        len(args.options) == 1):
            list_dbs()
    elif (args.command == "table" and args.options[0] == "list" and
        len(args.options) == 2):
            list_tables(args.options[1])
    elif (args.command == "table" and args.options[0] == "rows" and
        len(args.options) == 3):
            table_rows(*args.options[1:])
    else:
        print(f"Invalid command: {args.command}")
        print(__doc__)
