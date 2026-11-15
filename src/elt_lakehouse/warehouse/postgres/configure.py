import os
from pathlib import Path

import dotenv
import psycopg

dotenv.load_dotenv()

from elt_lakehouse.spark.common.paths import POSTGRES_DIR
from elt_lakehouse.spark.common.logger import get_logger

logger = get_logger(__name__)


POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
POSTGRES_HOSTNAME = os.getenv("POSTGRES_HOSTNAME")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")


def create_postgres_connection(
    port: str, host: str, user: str, password: str, database: str
) -> psycopg.Connection:
    """
    Create a connection to the PostgreSQL database.

    Args:
        port (int): The port number for the PostgreSQL server.
        host (str): The hostname or IP address of the PostgreSQL server.
        user (str): The username to connect to the PostgreSQL server.
        password (str): The password for the specified user.
        database (str): The name of the database to connect to.

    Returns:
        psycopg.Connection: A connection object to the PostgreSQL database.
    """
    try:
        logger.info(
            "Connecting to PostgreSQL: host=%s port=%s database=%s user=%s",
            host,
            port,
            database,
            user,
        )
        connection = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=database,
        )
        logger.info("PostgreSQL connection established: database=%s", database)
        return connection
    except psycopg.Error as error:
        logger.exception(
            "PostgreSQL connection failed: host=%s port=%s database=%s",
            host,
            port,
            database,
        )
        raise


def apply_postgres_schema(
    connection: psycopg.Connection, sql_files: list[Path]
) -> None:
    """
    Apply PostgreSQL schema scripts in one transaction.

    Args:
        connection (psycopg.Connection): A connection to the PostgreSQL database.
        sql_files (list[Path]): Paths to SQL files containing schema definitions.
    """
    try:
        logger.info("PostgreSQL setup started: sql_file_count=%d", len(sql_files))
        with connection.cursor() as cursor:
            for sql_file in sql_files:
                logger.info("Executing PostgreSQL SQL file: path=%s", sql_file)
                with sql_file.open(encoding="utf-8") as file:
                    sql_script = file.read()
                    cursor.execute(sql_script)
                logger.info("PostgreSQL SQL file completed: path=%s", sql_file)
        connection.commit()
        logger.info("PostgreSQL setup committed successfully")
    except Exception as error:
        connection.rollback()
        logger.exception(
            "PostgreSQL setup failed; transaction rolled back: error=%s", error
        )
        raise


def configure_postgres_from_environment() -> None:
    """
    Configure PostgreSQL using environment-based connection parameters.
    """
    sql_files = [
        POSTGRES_DIR / "setup.sql",
        POSTGRES_DIR / "create_tables.sql",
        POSTGRES_DIR / "create_indexes.sql",
    ]

    with create_postgres_connection(
        port=POSTGRES_PORT,
        host=POSTGRES_HOSTNAME,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DATABASE,
    ) as connection:
        apply_postgres_schema(connection=connection, sql_files=sql_files)

if __name__ == "__main__":
    configure_postgres_from_environment()
