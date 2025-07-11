#!/usr/bin/evn python
# --coding:utf-8---
# brief: connect db & execute sql
# author: thomas
# date: 2016.8.1

from __future__ import print_function
from __future__ import division
import sys
import psycopg2
import psycopg2.extras

def batch_insert(conn, sql: str, lst_dict: list, commit=True, page_size=100):
    cursor1 = conn.cursor()
    psycopg2.extras.execute_batch(cursor1, sql, lst_dict, page_size)
    if commit:
        conn.commit()
        cursor1.close()


def cursor(conn, sql: str, commit=False, ret=False):
    cursor1 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # cursor1 = conn.cursor()

    cursor1.execute(sql)
    if commit:
        conn.commit()
    if ret:
        rows = cursor1.fetchall()
        cursor1.close()
        return rows
    else:
        cursor1.close()


def db_conn(host: str, port: int, user: str, pw: str, db: str):
    try:
        conn = psycopg2.connect(host=host, port=port, user=user,
                                password=pw, database=db)
    except Exception as e:
        print(e.args[0])
        print("db connect error, exit")
        sys.exit()

    return conn


def db_conn_dict(db_info:dict):
    host = db_info.get("host", "127.0.0.1")
    port = db_info.get("port", 5432)
    user = db_info.get("user", "postgres")
    pw = db_info.get("pw", "mapabc")
    db = db_info.get("dbname", "postgres")
    try:
        conn = psycopg2.connect(host=host, port=port, user=user,
                                password=pw, database=db)
    except Exception as e:
        print(e.args[0])
        print("db connect error, exit")
        sys.exit()

    return conn


def main():

    db_info = {"host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "pw": "mapabc",
    "db": "postgis"}
    conn = db_conn_dict(db_info)
    conn.close()


if __name__ == '__main__':
    main()

