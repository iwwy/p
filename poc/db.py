"""
User Session Database Support
=============================

Tables
------

site_user

+---+----+----+------+
|uid|sha1|name|access|
+---+----+----+------+

site_session

+-------+-------+----+----+
|session|expires|data|user|
+-------+-------+----+----+

site_user_data

+---+----+
|uid|data|
+---+----+
"""

import datetime
import hashlib
import json
import sqlite3
import uuid


MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


class User(object):

    def __init__(self, uid, name, access):
        self.uid = uid
        self.name = name
        self.access = access


class Database(object):

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        try:
            self.c.execute("SELECT * FROM site_user LIMIT 1")
        except sqlite3.OperationalError as error:
            if error.args[0] == "no such table: site_user":
                self.c.execute("CREATE TABLE site_user "
                               "(uid text, sha1 text, name text, access text)")
                self.c.execute("CREATE TABLE site_session (session text, "
                               "expires text, data text, user text)")
                self.c.execute("CREATE TABLE site_user_data "
                               "(uid text, data text)")

    def _parse_expire(self, expire):
        parts = expire.split()
        date = datetime.datetime(
            int(parts[3]), MONTHS[parts[2]], int(parts[1]),
            *map(int, parts[4].split(":")), tzinfo=datetime.timezone.utc)
        return date

    def get_session(self, session_id):
        self.c.execute("SELECT expires, data FROM site_session "
                       "WHERE session = ?", (session_id,))
        session_data = self.c.fetchone()
        if not session_data:
            self.insert_session(session_id)
            return {}, datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc)
        if session_data[0]:
            date = self._parse_expire(session_data[0])
        else:
            date = datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc)
        return json.loads(session_data[1]), date

    def get_user_by_session(self, session_id):
        self.c.execute("SELECT user FROM site_session "
                       "WHERE session = ?", (session_id,))
        user_id = (self.c.fetchone() or [None])[0]
        if not user_id:
            return
        self.c.execute("SELECT uid, name, access FROM site_user "
                       "WHERE uid = ?", (user_id,))
        data = self.c.fetchone()
        if data:
            return User(uid=data[0], name=data[1], access=data[2].split(","))

    def get_user_by_name_salt_hash(self, username, salt, hash_):
        self.c.execute("SELECT uid, sha1, name, access FROM site_user "
                       "WHERE name = ?", (username,))
        data = self.c.fetchone()
        if data:
            algorithm = hashlib.sha1()
            algorithm.update(data[1].encode("utf-8") + salt.encode("utf-8"))
            if algorithm.hexdigest() == hash_:
                return User(uid=data[0], name=data[2],
                            access=data[3].split(","))

    def insert_session(self, session_id):
        self.c.execute("INSERT INTO site_session VALUES (?, ?, ?, ?)",
                       (session_id, "", json.dumps({}), ""))

    def logout_session(self, session_id):
        self.c.execute("UPDATE site_session SET user = ? WHERE session = ?",
                       ("", session_id))

    def update_session(self, session_id, cookie):
        self.c.execute("UPDATE site_session SET expires = ?"
                       "WHERE session = ?", (cookie, session_id))

    def save_session(self, session_id, data):
        self.c.execute("UPDATE site_session SET data = ? WHERE session = ?",
                       (json.dumps(data), session_id))

    def set_user_session(self, uid, session_id):
        self.c.execute("UPDATE site_session SET user = ? WHERE session = ?",
                       (uid, session_id))

    def signup(self, username, password):
        uid = uuid.uuid4().hex
        algorithm = hashlib.sha1()
        algorithm.update(password.encode("utf-8"))
        sha1 = algorithm.hexdigest()
        self.c.execute("INSERT INTO site_user VALUES (?, ?, ?, ?)",
                       (uid, sha1, username, "user"))

    def get_user_data(self, uid):
        self.c.execute("SELECT data FROM site_user_data WHERE uid = ?", (uid,))
        data = self.c.fetchone()
        return data and json.loads(data[0]) or {}

    def save_user_data(self, uid, data):
        self.c.execute("SELECT data FROM site_user_data WHERE uid = ?", (uid,))
        exists = self.c.fetchone()
        if exists:
            self.c.execute("UPDATE site_user_data SET data = ? WHERE uid = ?",
                           (json.dumps(data), uid))
        else:
            self.c.execute("INSERT INTO site_user_data VALUES (?, ?)",
                           (uid, json.dumps(data)))

    def close(self):
        self.conn.commit()
        self.conn.close()

    def clean_expired_sessions(self):
        delete = []
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        for r in self.c.execute("SELECT session, expires FROM site_session"):
            if self._parse_expire(r[1]) < now:
                delete.append(r[0])
        for session_id in delete:
            self.c.execute("DELETE FROM site_session WHERE session = ?",
                           (session_id,))
        return len(delete)
