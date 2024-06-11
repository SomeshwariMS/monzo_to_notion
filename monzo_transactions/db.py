import logging
import os
from datetime import datetime

import pandas as pd
import sqlalchemy

from .utils import get_timestamp

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FinancesDb:
    def __init__(self):
        self.db_name = "Finances"
        self.conn = None
        self.sql_log_path = None
        self.start_ts = None
        self.end_ts = None
        self.mytstart = None
        self.mytend = None
        self.connect_to_db()

    def connect_to_db(self):
        username = os.environ.get("DB_USER")
        password = os.environ.get("DB_PASS")
        host = os.environ.get("DB_HOST")
        database = os.environ.get("DB_NAME")
        port = os.environ.get("DB_PORT")

        sql_string = "postgresql://{}:{}@{}:{}/{}".format(
            username, password, host, port, database
        )

        self.conn = sqlalchemy.create_engine(sql_string).connect()
        logger.info(f"Connecting to database: {self.db_name}")

    def query(
        self,
        sql=None,
        return_data=True,
    ):

        self._log_sql(sql=sql)
        self.start_ts = get_timestamp()

        logger.debug(f"Running SQL")
        if return_data:
            df = pd.read_sql_query(sql, self.conn)
            self.end_ts = get_timestamp()
            return df
        else:
            self.conn.execute(sql)
            self.end_ts = get_timestamp()

    def insert(
        self,
        table,
        df=None,
        sql=None,
        logname="insert",
        if_exists="append",
    ):

        if sql:
            insert_sql = f"INSERT into {table} (\n{sql}\n);"
            self.query(sql=insert_sql, return_data=False, logname=logname)
            logger.info(f"Data inserted into {table}")
        else:
            rows = len(df)
            chunksize = None
            if rows > 20000:
                chunksize = 20000
            schema1, table1 = table.split(".")
            df.to_sql(
                schema=schema1,
                name=table1,
                index=False,
                con=self.conn,
                if_exists=if_exists,
                method="multi",
                chunksize=chunksize,
            )
            logger.info(f"{rows} rows inserted into {schema1}.{table1}")

    def _log_sql(self, sql):
        today = datetime.today()
        year = today.strftime("%Y")
        month = "{}_{}".format(today.strftime("%m"), today.strftime("%b"))
        week = "wk_{}".format(today.strftime("%W"))
        day = today.strftime("%d")
        timestamp = today.strftime("%Y%m%d_%H%M%S")

        sql_log_filename = "{}_{}.sql".format(timestamp, self.db_name)

        sql_log_folder = os.path.join(
            os.getcwd(), "logs", "sql_log", year, month, week, day
        )
        os.makedirs(sql_log_folder, exist_ok=True)
        sql_log_path = os.path.join(sql_log_folder, sql_log_filename)

        with open(sql_log_path, "w") as sql_log:
            sql_log.write(sql)

        self.sql_log_path = sql_log_path
