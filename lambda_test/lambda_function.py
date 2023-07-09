import sys
import logging
import pymysql
import json
import os

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_host = os.environ['RDS_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")


def lambda_handler(event, context):
    try:
        """
        This function creates a new RDS database table and writes records to it
        """

        message = event['Records'][0]['body']
        print(message)
        data = json.loads(message)
        CustID = data['CustID']
        Name = data['Name']

        item_count = 0
        sql_string = f"insert into CustomerTestSample (CustID, Name) values({CustID}, '{Name}')"

        with conn.cursor() as cur:
            cur.execute(
                "create table if not exists CustomerTestSample ( CustID  int NOT NULL, Name varchar(255) NOT NULL, PRIMARY KEY (CustID))")
            client_table_text = """create table if not exists Client ( 
                ID  int NOT NULL, 
                Name varchar(255), 
                Email varchar(255),
                Debit_balance DECIMAL(65, 2) NOT NULL,
                Credit_balance DECIMAL(65, 0) NOT NULL,
                PRIMARY KEY (ID)
                )"""

            cur.execute(client_table_text)
            conn.commit()
            transaction_table_text = """create table if not exists Transactions ( 
                ID  int NOT NULL, 
                Client_id int NOT NULL, 
                Date DATETIME,
                Type varchar(255),
                Ammount DECIMAL(65, 0) NOT NULL,
                PRIMARY KEY (ID)
                )"""

            cur.execute(transaction_table_text)
            conn.commit()

            cur.execute(sql_string)

            cur.execute("select * from CustomerTestSample")
            logger.info("The following items have been added to the database:")
            for row in cur:
                item_count += 1
                logger.info(row)
        conn.commit()

        return "Added %d items to RDS MySQL table" % (item_count)
    except Exception as ex:
        print("shit happens")
        print(list(event.keys()))
        message_val = event['Records'][0]['body']
        data = json.loads(message)
        message = 'Hello {} {}!'.format(data['first_name'], data['last_name'])
        return {
            'message': message
        }
