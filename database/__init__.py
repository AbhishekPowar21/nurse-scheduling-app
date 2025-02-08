# __init__.py

import mysql.connector
from .config import Config

def get_db_connection():
    """
    Establishes a connection to the MySQL database.
    """
    connection = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        database=Config.MYSQL_DATABASE,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD
    )
    return connection
