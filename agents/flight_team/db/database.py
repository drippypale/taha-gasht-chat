import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List

from agents.flight_team.db.models import Flight


class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, in_memory: bool = True):
        """Initialize the database connection and tables"""
        if in_memory:
            self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            self.conn = sqlite3.connect("flights.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self._get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS flights (
                    airline TEXT NOT NULL,
                    departure_datetime TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    origin_city TEXT NOT NULL,
                    origin_code TEXT NOT NULL,
                    dest_city TEXT NOT NULL,
                    dest_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    @contextmanager
    def _get_cursor(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def insert_flights(self, flights: List[Flight]):
        """
        Insert a list of Flight objects into the database
        """
        with self._get_cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO flights (
                    airline, departure_datetime, flight_number, 
                    origin_city, origin_code, dest_city, dest_code, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        flight.airline,
                        flight.departure_datetime.isoformat(),
                        flight.flight_number,
                        flight.origin_city,
                        flight.origin_code,
                        flight.dest_city,
                        flight.dest_code,
                        flight.created_at.isoformat(),
                    )
                    for flight in flights
                ],
            )

    def query_flights(self, query: str) -> List[Dict[str, Any]]:
        """
        Query flights based on the given query
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    query,
                )

                results = cursor.fetchall()
                return [
                    Flight(
                        airline=row["airline"],
                        departure_datetime=datetime.fromisoformat(
                            row["departure_datetime"]
                        ),
                        flight_number=row["flight_number"],
                        origin_city=row["origin_city"],
                        origin_code=row["origin_code"],
                        dest_city=row["dest_city"],
                        dest_code=row["dest_code"],
                    ).to_dict()
                    for row in results
                ]
        except Exception as e:
            raise e

    def close(self):
        """
        Close the database connection
        """
        self.conn.close()
