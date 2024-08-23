#
# Banana database
#

import re
import sqlite3 as sq3
import time
import uuid

from banana import error, log

LOG = log.logger(__name__)

TABLE_COMMON_COLS = ["id", "created_at", "updated_at"]

RE_ID = re.compile(r"^[0-9a-f]{40}$")


def now():
    """Return the current date/time in seconds since the Epoc"""
    return int(time.time())


def trace(func):
    """Tracing decorator"""

    def wrapper(self, *args, **kwargs):
        LOG.debug("Table(%s).%s(args=%s, kwargs=%s)", self.name, func.__name__, args, kwargs)
        return func(self, *args, **kwargs)

    return wrapper


class BaseTable:
    """Base table class"""

    name = None
    cols = None

    def __init__(self, db):
        self.db = db

    def kwargs_to_vals(self, kwargs):
        """Convert a dict to a table column list"""
        return [kwargs.get(c, "") for c in self.cols]

    def check_kwargs(self, kwargs):
        """Sanity check"""
        for key, val in kwargs.items():
            if key not in self.cols:
                raise error.InvalidColumnError(f"Table({self.name}): column={key}")
            if key.endswith("_id") and not RE_ID.match(val):
                raise error.InvalidIdError(f"Table({self.name}): {key}={val}")

    @trace
    def create(self):
        """Create the table"""
        # Convert the cols array to an sqlite formatting string
        cols = ",".join(self.cols)

        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            cur = con.cursor()
            cur.execute(f"CREATE TABLE {self.name} ({cols})")
            con.commit()

    @trace
    def exists(self):
        """Check if the table exists"""
        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            cur = con.cursor()
            cur.execute(f"SELECT name from sqlite_master WHERE type='table' AND name='{self.name}'")
            table = cur.fetchall()
        if table:
            return True
        return False

    @trace
    def dump(self):
        """Return all rows"""
        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            con.row_factory = sq3.Row  # dictionary cursor
            cur = con.cursor()
            cur.execute(f"SELECT * FROM {self.name}")
            for row in cur.fetchall():
                yield dict(zip(row.keys(), row))

    @trace
    def insert(self, **kwargs):
        """Insert a new row"""
        self.check_kwargs(kwargs)

        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            cur = con.cursor()

            # Check if the row exists already
            commit_id = kwargs.get("commit_id")
            if commit_id:
                cur.execute(f"SELECT * FROM {self.name} WHERE commit_id=?", [commit_id])
                if cur.fetchone():
                    raise error.CommitIdExistsError(f"Table({self.name}): commit_id={commit_id}")

            # Create row ID and timestamps
            kwargs["id"] = str(uuid.uuid4())
            kwargs["created_at"] = now()
            kwargs["updated_at"] = kwargs["created_at"]

            # Create the sqlite formatting string and values list
            fmt = ",".join(["?" for c in self.cols])
            vals = self.kwargs_to_vals(kwargs)

            # Insert the new row
            cur.execute(f"INSERT INTO {self.name} VALUES ({fmt})", vals)
            con.commit()

    @trace
    def select(self, **kwargs):
        """Return select rows"""
        self.check_kwargs(kwargs)

        # Create the sqlite query string
        # FIXME: Use fmt string and vals list (like in 'insert' above)
        queries = [f"{k}='{str(v)}'" for k, v in kwargs.items()]
        where = " AND ".join(queries)

        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            con.row_factory = sq3.Row  # dictionary cursor
            cur = con.cursor()
            cur.execute(f"SELECT * FROM {self.name} WHERE {where}")
            for row in cur.fetchall():
                yield dict(zip(row.keys(), row))


class PatchIdTable(BaseTable):
    """Table containing Patch IDs"""

    name = "_patch_id"
    cols = TABLE_COMMON_COLS + [
        "commit_id",
        "patch_id",
    ]


class CommitTable(BaseTable):
    """Table containing Commit details"""

    name = "_commit"
    cols = TABLE_COMMON_COLS + [
        "commit_id",
        "subject",
        "details",
        "committed_at",
        "author_name",
        "author_email",
        "authored_at",
    ]

    @staticmethod
    def dict_from_commit(commit):
        return {
            "commit_id": commit.hexsha,
            "subject": commit.message.split("\n")[0],
            "details": commit.message,
            "committed_at": commit.committed_date,
            "author_name": commit.author.name,
            "author_email": commit.author.email,
            "authored_at": commit.authored_date,
        }

    @trace
    def insert_commit(self, commit):
        """Insert a commit into the table"""
        self.insert(**self.dict_from_commit(commit))


class DataBase:
    def __init__(self, db_filename):
        self.patch_id = PatchIdTable(db_filename)
        self.commit = CommitTable(db_filename)

    def init(self):
        """Create all tables"""
        if not self.patch_id.exists():
            self.patch_id.create()
        if not self.commit.exists():
            self.commit.create()

    def dump(self):
        """Dump tables"""
        if self.patch_id.exists():
            print("Table(patch_id):")
            for row in self.patch_id.dump():
                print(row)
        if self.commit.exists():
            print("Table(commit):")
            for row in self.commit.dump():
                print(row)
