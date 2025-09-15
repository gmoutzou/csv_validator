#
# project: sPAD
#
# pgdev
#
# georgios mountzouris 2025 (gmountzouris@efka.gov.gr)
#

import v_config as cfg
import pandas as pd
#import logging
#import traceback
import psycopg2
from sqlalchemy import create_engine


#logger = logging.getLogger(__name__)

def connection_test(config):
    test = 0
    dbconfig = {k: v for k, v in config.items() if k != "dbschema"}
    try:
        conn = psycopg2.connect(**dbconfig, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        row = cur.fetchone()
        if row is not None:
            test = row[0]
        conn.close()
    except:
        pass
    return (test == 1)

class Pgdev():
    def __init__(self, config):
        self.config = {k: v for k, v in config.items() if k != "dbschema"}
    def __enter__(self):
        """ Connect to the PostgreSQL database server """
        with psycopg2.connect(**self.config, connect_timeout=5) as conn:
            #logger.info('Connected to the PostgreSQL server')
            self.conn = conn
            return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Close the connection to PostgreSQL database server """
        if exc_type is not None:
            #traceback.print_exception(exc_type, exc_val, exc_tb)
            #logger.error(traceback.format_exc())
            pass
        self.conn.close()
        #logger.info('Database connection closed')
    
    def load_data(self, connection_string, csv, tablename):
        try:
            engine = create_engine(connection_string)
            with engine.connect() as connection:
                # Read the CSV file into a DataFrame (dtype=str -> columns datatype string to keep leading zeros)
                df = pd.read_csv(csv, dtype=str)
                # Perform the data loading operation
                df.to_sql(tablename, con=connection, if_exists='append', index=False)
                # Commit the changes
                #self.conn.commit()
                return True
        except:
            return False
        
    def fetch_data_all(self, sql):
        rows = []
        with self.conn.cursor() as cur:
            #logger.info('Fetch all data with SQL: ' + sql)
            cur.execute(sql)
            rows = cur.fetchall()
        return rows
    
    def fetch_data_all_descriptions(self, sql):
        rows = []
        with self.conn.cursor() as cur:
            #logger.info('Fetch all data and column names with SQL: ' + sql)
            cur.execute(sql)
            colnames = [descr[0] for descr in cur.description]
            rows = cur.fetchall()
        return colnames, rows
    
    def fetch_data_one_by_one(self, sql):
        with self.conn.cursor() as cur:
            #logger.info('Fetch data one by one with SQL: ' + sql)
            cur.execute(sql)
            row = cur.fetchone()
            while row:
                yield row
                row = cur.fetchone()

    def crud(self, query, data):
        with self.conn.cursor() as cur:
            cur.execute(query, data)
            self.conn.commit()

def main():
    try:
        config = cfg.load_config(section='postgresql')
        pg_con_str = cfg.get_connection_string()
        with Pgdev(config) as pgdev:
            pass
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

if __name__ == "__main__":
    main()
    