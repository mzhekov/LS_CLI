"""
Database connection and session management
"""

from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from leadsauce.utils.config import get_config
from leadsauce.utils.constants import DATABASE_FILE

# Base class for models
Base = declarative_base()

# Global session factory
_session_factory: Optional[sessionmaker] = None
_engine: Optional[Engine] = None


def get_database_url() -> str:
    """Get database URL from configuration"""
    config = get_config()
    db_type = config.get('database.type', 'sqlite')

    if db_type == 'sqlite':
        db_path = config.get('database.path', str(DATABASE_FILE))
        return f"sqlite:///{db_path}"
    elif db_type == 'postgresql':
        host = config.get('database.host', 'localhost')
        port = config.get('database.port', 5432)
        name = config.get('database.name', 'leadsauce')
        user = config.get('database.user', 'leadsauce')
        password = config.get('database.password', '')
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    elif db_type == 'mysql':
        host = config.get('database.host', 'localhost')
        port = config.get('database.port', 3306)
        name = config.get('database.name', 'leadsauce')
        user = config.get('database.user', 'leadsauce')
        password = config.get('database.password', '')
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite"""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_engine(database_url: Optional[str] = None) -> Engine:
    """Initialize database engine"""
    global _engine

    if _engine is not None:
        return _engine

    url = database_url or get_database_url()

    # SQLite-specific settings
    if url.startswith('sqlite'):
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        _engine = create_engine(url, echo=False, pool_pre_ping=True)

    return _engine


def init_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """Initialize session factory"""
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    if engine is None:
        engine = init_engine()

    _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _session_factory


def get_session() -> Session:
    """Get database session"""
    if _session_factory is None:
        init_session_factory()

    return _session_factory()


def init_database(database_url: Optional[str] = None):
    """Initialize database and create all tables"""
    engine = init_engine(database_url)

    # Import all models to ensure they're registered
    from leadsauce.models import (
        profile, company, interaction,
        reminder, tag, team, document, activity, task, relationship
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Initialize session factory
    init_session_factory(engine)


def close_session(session: Session):
    """Close database session"""
    try:
        session.close()
    except Exception:
        pass


def drop_all_tables(engine: Optional[Engine] = None):
    """Drop all tables (use with caution!)"""
    if engine is None:
        engine = init_engine()

    Base.metadata.drop_all(engine)


def reset_database():
    """Reset database by dropping and recreating all tables"""
    engine = init_engine()
    drop_all_tables(engine)
    init_database()


class DatabaseSession:
    """Context manager for database sessions"""

    def __init__(self):
        self.session: Optional[Session] = None

    def __enter__(self) -> Session:
        self.session = get_session()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
