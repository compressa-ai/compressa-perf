import sqlite3
from compressa.perf.db.setup import setup_db


def main():
    with sqlite3.connect("compressa-perf.db") as conn:
        setup_db(conn)


if __name__ == "__main__":
    main()
