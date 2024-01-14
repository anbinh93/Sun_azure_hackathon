from abc import ABC, abstractmethod
from datetime import datetime
import os
import json
import sys
import sqlite3
sys.path.append(os.getcwd())  # NOQA


class BaseCrawler(ABC):
    """
        Base class for all crawlers.
    """

    CONFIG_DIR = os.path.join(os.getcwd(), 'config')
    DATABASE_DIR = os.path.join(os.getcwd(), 'database')

    def load_config(self, filename) -> dict:
        """
            Load the config file from config directory.
        """
        with open(os.path.join(self.CONFIG_DIR, filename), 'r') as f:
            return json.load(f)

    def connect_db(self, filename) -> sqlite3.Connection:
        """
            Connect to the database.
        """
        db_path = os.path.join(self.DATABASE_DIR, filename)
        return sqlite3.connect(db_path)

    def log(self, msg):
        datefmt = datetime.strftime(datetime.now(), format='%Y-%m-%d %H:%M:%S')
        # Print to console
        print(f'[{datefmt}]: {msg}')

    def build_insert_query(self, table_name, item):
        columns = list(item.keys())
        vals = []

        for col in columns:
            if type(item[col]) == str:
                vals.append(f"'{item[col]}'")
            else:
                vals.append(str(item[col]))

        query = f"""
                insert into {table_name} ({','.join(columns)})
                values ({','.join(vals)})
            """

        return query
