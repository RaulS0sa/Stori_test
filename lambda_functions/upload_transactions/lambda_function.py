import sys
import logging
import pymysql
import os
from http import HTTPStatus
from datetime import datetime
from decimal import *

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_host = os.environ['RDS_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)
getcontext().prec = 2

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
    """
    This function stores a transaction record in the database
    """
    try:
        id_txt = event.get('Client_ID')
        date = event.get('Date')
        transaction = event.get('Transaction')
        amount_txt = event.get('Amount')

        client_id = int(id_txt)
        date_obj = datetime.strptime(date, '%m/%d/%y %H:%M:%S')
        amount = Decimal(amount_txt)


        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                f"SELECT * FROM Client WHERE ID='{client_id}' LIMIT 1")

            result = cur.fetchall()
            if result:
                client = result[0]
                if transaction == "Debit":
                    resulting_valance = client["Debit_balance"] + amount
                    if resulting_valance < 0:
                        return {
                            "message": f"Balance is not enough",
                            "status": HTTPStatus.BAD_REQUEST
                        }
                    else:
                        cur.execute(f"UPDATE Client SET "
                                    f"Debit_balance = {resulting_valance} WHERE ID='{client_id}'")

                        conn.commit()
                elif transaction == "Credit":
                    resulting_valance = client["Credit_balance"] + amount
                    cur.execute(f"UPDATE Client SET "
                                f"Credit_balance = {resulting_valance} WHERE ID='{client_id}'")

                    conn.commit()

                query_string = f"insert into Transactions (Client_id, Date, Type, Ammount)" \
                               f" values({client_id}, '{date_obj}', '{transaction}', {amount})"

                cur.execute(query_string)
                conn.commit()
                logger.info(f"transaction {cur.lastrowid} stored")
                return {
                    "transaction_id": cur.lastrowid,
                    "message": "created",
                    "status": HTTPStatus.CREATED
                }
            else:
                return {
                    "message": f"user {client_id} don't exist",
                    "status": HTTPStatus.BAD_REQUEST
                }
    except Exception as ex:
        return {
            "message": str(ex),
            "status": HTTPStatus.INTERNAL_SERVER_ERROR
        }
