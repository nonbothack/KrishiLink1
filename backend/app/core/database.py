import logging
import os
import sqlite3

from sqlalchemy import create_engine, event, text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine import Engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import ARRAY

try:
    import geoalchemy2.admin.dialects.sqlite as sqlite_admin
    from geoalchemy2 import Geography, Geometry

    sqlite_admin.after_create = lambda *args, **kwargs: None
    sqlite_admin.before_create = lambda *args, **kwargs: None
except ImportError:
    pass


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "VARCHAR(36)"


import uuid as _py_uuid

_orig_uuid_bind_processor = UUID.bind_processor


def _safe_uuid_bind_processor(self, dialect):
    proc = _orig_uuid_bind_processor(self, dialect)
    if proc:

        def _safe_proc(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return _py_uuid.UUID(value).hex
                except ValueError:
                    return value.replace("-", "")
            if hasattr(value, "hex"):
                return value.hex
            return str(value)

        return _safe_proc
    return proc


UUID.bind_processor = _safe_uuid_bind_processor


import json


@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(PG_ARRAY, "sqlite")
def compile_pg_array_sqlite(type_, compiler, **kw):
    return "TEXT"


_orig_array_bind_processor = ARRAY.bind_processor
def _safe_array_bind_processor(self, dialect):
    proc = _orig_array_bind_processor(self, dialect)
    if dialect.name == "sqlite":
        def _sqlite_proc(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple, set)):
                return json.dumps(list(value))
            return str(value)
        return _sqlite_proc
    return proc

ARRAY.bind_processor = _safe_array_bind_processor

_orig_array_result_processor = ARRAY.result_processor
def _safe_array_result_processor(self, dialect, coltype):
    proc = _orig_array_result_processor(self, dialect, coltype)
    if dialect.name == "sqlite":
        def _sqlite_res_proc(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return [value]
            return value
        return _sqlite_res_proc
    return proc

ARRAY.result_processor = _safe_array_result_processor

_orig_pg_array_bind_processor = PG_ARRAY.bind_processor
def _safe_pg_array_bind_processor(self, dialect):
    proc = _orig_pg_array_bind_processor(self, dialect)
    if dialect.name == "sqlite":
        def _sqlite_proc(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple, set)):
                return json.dumps(list(value))
            return str(value)
        return _sqlite_proc
    return proc

PG_ARRAY.bind_processor = _safe_pg_array_bind_processor

_orig_pg_array_result_processor = PG_ARRAY.result_processor
def _safe_pg_array_result_processor(self, dialect, coltype):
    proc = _orig_pg_array_result_processor(self, dialect, coltype)
    if dialect.name == "sqlite":
        def _sqlite_res_proc(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return [value]
            return value
        return _sqlite_res_proc
    return proc

PG_ARRAY.result_processor = _safe_pg_array_result_processor


try:

    @compiles(Geography, "sqlite")
    def compile_geography_sqlite(type_, compiler, **kw):
        return "TEXT"

    @compiles(Geometry, "sqlite")
    def compile_geometry_sqlite(type_, compiler, **kw):
        return "TEXT"
except NameError:
    pass


@event.listens_for(Engine, "connect")
def setup_sqlite_spatial_functions(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()
        dbapi_connection.create_function("AsBinary", 1, lambda x: x)
        dbapi_connection.create_function("AsGeoJSON", 1, lambda x: x)
        dbapi_connection.create_function("ST_AsGeoJSON", 1, lambda x: x)
        dbapi_connection.create_function("ST_AsBinary", 1, lambda x: x)
        dbapi_connection.create_function("ST_GeogFromText", 1, lambda x: x)
        dbapi_connection.create_function("ST_GeomFromText", 1, lambda x: x)
        dbapi_connection.create_function("ST_DWithin", 3, lambda a, b, d: 1)
        dbapi_connection.create_function("ST_MakePoint", 2, lambda x, y: f"POINT({x} {y})")
        dbapi_connection.create_function("ST_SetSRID", 2, lambda g, s: g)
        dbapi_connection.create_function("ST_Distance", 2, lambda a, b: 0.0)


from app.core.config import settings


class Base(DeclarativeBase):
    pass


def create_db_engine():
    db_url = settings.database_url_effective

    # SQLite is test/development-only. Production and staging must fail closed.
    if "sqlite" in db_url:
        if settings.env in ("production", "staging"):
            raise RuntimeError(f"SQLite database configuration is not permitted in {settings.env}")
        eng = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=settings.debug and settings.env == "development",
        )
        import app.models  # noqa: F401

        if os.getenv("KRISHILINK_ALEMBIC_RUNNING") != "1":
            Base.metadata.create_all(eng)
        return eng

    # Try PostgreSQL, fallback to local SQLite only in local development/test environments
    try:
        eng = create_engine(
            db_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2} if "psycopg" in db_url else {},
            echo=settings.debug and settings.env == "development",
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return eng
    except Exception as e:
        if settings.env in ("production", "staging"):
            logging.getLogger(__name__).critical(
                "PostgreSQL database connection failed in %s environment: %s",
                settings.env,
                e,
            )
            raise RuntimeError(
                f"Production database connection failure ({settings.env}): {e}. Refusing to fall back to SQLite."
            ) from e

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sqlite_path = os.path.join(base_dir, "krishilink.db")
        # Log fallback warning for development only
        logging.getLogger(__name__).warning(
            "PostgreSQL unavailable (%s). Falling back to SQLite at %s for local development.",
            e,
            sqlite_path,
        )
        sqlite_url = f"sqlite:///{sqlite_path}"
        eng = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
        )
        import app.models  # noqa: F401

        if os.getenv("KRISHILINK_ALEMBIC_RUNNING") != "1":
            Base.metadata.create_all(eng)
        return eng


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
