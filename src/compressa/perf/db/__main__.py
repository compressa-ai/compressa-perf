import sqlite3
from compressa.perf.db.create import create_request_table


def main():
    with sqlite3.connect('compressa-perf.db') as conn:
        create_request_table(conn)
    

if __name__ == '__main__':
    main()
