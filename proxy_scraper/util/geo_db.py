import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

class GeoDB:
    DB_NAME = "geo.db"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        if not os.path.exists(self.DB_NAME):
            with sqlite3.connect(self.DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """CREATE TABLE geo (
                                    ip TEXT PRIMARY KEY,
                                    country TEXT,
                                    countryCode TEXT)"""
                )
                conn.commit()
            logger.info(f"Initialized database {self.DB_NAME}")

    def get(self, ip: str) -> dict:
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM geo WHERE ip=?", (ip,))
            row = cursor.fetchone()
            if row:
                return {
                    "ip": row[0],
                    "country": row[1],
                    "countryCode": row[2],
                }
            return None

    def set(self, ip: str, data: dict):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO geo (ip, country, countryCode)
                VALUES (:ip, :country, :countryCode)""",
                data,
            )
            conn.commit()
            logger.info(f"Cached data for IP {ip}")
