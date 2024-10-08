#
# Banana database
#

import re
import sqlite3 as sq3
import time
import uuid

from . import error, log

LOG = log.Logger(__name__)

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
    data_cols = None
    unique_cols = None
    all_cols = None

    def __init__(self, db):
        self.db = db

    def kwargs_to_vals(self, kwargs):
        """Convert a dict to a table column list"""
        return [kwargs.get(c, "") for c in self.all_cols]

    def check_kwargs_sane(self, kwargs):
        """Sanity check"""
        for key, val in kwargs.items():
            if key not in self.all_cols:
                raise error.InvalidColumnError(f"Table({self.name}): column={key}")
            if key.endswith("_id") and not RE_ID.match(val):
                raise error.InvalidIdError(f"Table({self.name}): {key}={val}")

        # for c in self.unique_cols:
        #     if c not in kwargs:
        #         raise error.MissingColumnError(f"Table({self.name}): column={c}")

    def check_row_exists(self, cur, kwargs):
        """Check if a row exists"""
        if not self.unique_cols:
            return

        queries = [f"{c}=?" for c in self.unique_cols]
        where = " AND ".join(queries)
        vals = [kwargs[c] for c in self.unique_cols]

        cur.execute(f"SELECT * FROM {self.name} WHERE {where}", vals)
        if cur.fetchone():
            raise error.RowExistsError(f"Table({self.name}): {where} -- {vals}")

    @trace
    def create(self):
        """Create the table"""
        # Convert the cols array to an sqlite formatting string
        cols = ",".join(self.all_cols)

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
        self.check_kwargs_sane(kwargs)

        with sq3.connect(self.db) as con:
            con.set_trace_callback(LOG.debug)
            cur = con.cursor()

            # Check if the row exists already
            self.check_row_exists(cur, kwargs)

            # Create row ID and timestamps
            kwargs["id"] = str(uuid.uuid4())
            kwargs["created_at"] = now()
            kwargs["updated_at"] = kwargs["created_at"]

            # Create the sqlite formatting string and values list
            fmt = ",".join(["?" for c in self.all_cols])
            vals = self.kwargs_to_vals(kwargs)

            # Insert the new row
            cur.execute(f"INSERT INTO {self.name} VALUES ({fmt})", vals)
            con.commit()

    @trace
    def select(self, **kwargs):
        """Return select rows"""
        self.check_kwargs_sane(kwargs)

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

    @trace
    def insert_commit(self, commit):
        """Insert a commit into the table"""
        self.insert(**commit.to_dict(self.data_cols))


class CommitTable(BaseTable):
    """Table containing Commit details"""

    name = "_commit"
    data_cols = [
        "commit_id",
        "subject",
        "details",
        "committed_at",
        "author_name",
        "author_email",
        "authored_at",
    ]
    unique_cols = ["commit_id"]
    all_cols = TABLE_COMMON_COLS + data_cols


class PatchIdTable(BaseTable):
    """Table containing Patch IDs"""

    name = "_patch_id"
    data_cols = [
        "commit_id",
        "patch_id",
    ]
    unique_cols = ["commit_id"]
    all_cols = TABLE_COMMON_COLS + data_cols


class FixesTable(BaseTable):
    """Table containing Fixes"""

    name = "_fixes"
    data_cols = [
        "commit_id",
        "fixes",
        "fixes_id",
    ]
    unique_cols = ["commit_id", "fixes"]
    all_cols = TABLE_COMMON_COLS + data_cols


class DataBase:
    def __init__(self, db_filename):
        self.commit = CommitTable(db_filename)
        self.patch_id = PatchIdTable(db_filename)
        self.fixes = FixesTable(db_filename)

    def init(self):
        """Create all tables"""
        if not self.commit.exists():
            self.commit.create()
        if not self.patch_id.exists():
            self.patch_id.create()
        if not self.fixes.exists():
            self.fixes.create()

    def dump(self):
        """Dump tables"""
        if self.commit.exists():
            print("Table(commit):")
            for row in self.commit.dump():
                print(row)
        if self.patch_id.exists():
            print("Table(patch_id):")
            for row in self.patch_id.dump():
                print(row)
        if self.fixes.exists():
            print("Table(fixes):")
            for row in self.fixes.dump():
                print(row)
