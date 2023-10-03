import sys
import logging
import pymysql
import os
import boto3
import json

from http import HTTPStatus
from decimal import *

# rds settings
user_name = os.environ['USER_NAME']
password = os.environ['PASSWORD']
rds_host = os.environ['RDS_HOST']
db_name = os.environ['DB_NAME']
sns_topic = os.environ['SNS_TOPIC']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

aws_client = boto3.client('sns')
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


def generate_mail(debit_balance, credit_balance, dates_set_debit, dates_set_credit):
    """
    This function fetches parses the HTML template with current account data
    """
    f = open("index.html", "r")
    mail_text = f.read()
    mail_text = mail_text.replace("{{Debit_Balance}}", str(debit_balance))
    mail_text = mail_text.replace("{{Credit_Balance}}", str(credit_balance))
    mail_text = mail_text.replace("{{Total_Balance}}", str(debit_balance + credit_balance))

    table_text_debit = ""
    table_text_credit = ""
    for key in dates_set_debit:
        elem = dates_set_debit[key]
        table_row = f"<tr><td>{key}</td><td>{elem['Count']}</td><td>{elem['Amount'] / elem['Count']}</td></tr>"
        table_text_debit += table_row

    for key in dates_set_credit:
        elem = dates_set_credit[key]
        table_text_credit += f"<tr><td>{key}</td><td>{elem['Count']}</td><td>{elem['Amount'] / elem['Count']}</td></tr>"
    mail_text = mail_text.replace("{{debit_table_elements}}", table_text_debit)
    mail_text = mail_text.replace("{{credit_table_elements}}", table_text_credit)

    return mail_text


def lambda_handler(event, context):
    """
    This function fetches transaction records and generates a summary
    """
    try:
        id_txt = event.get('Client_ID')
        client_id = int(id_txt)

        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                f"SELECT * FROM Client WHERE ID='{client_id}' LIMIT 1")

            result = cur.fetchall()
            if result:
                client = result[0]

                logger.info("client found")

                cur.execute(f"SELECT * FROM Transactions WHERE Client_id='{client_id}'")

                # Splits transactions by type and then groups them by Month/Year tuple
                dates_set_debit = {}
                dates_set_credit = {}
                credit_balance = Decimal(0.0)
                debit_balance = Decimal(0.0)
                debit_transactions_list = []
                credit_transactions_list = []
                for row in cur:
                    date_tuple = (row["Date"].month, row["Date"].year)
                    if row["Type"] == "Debit":
                        debit_balance += row["Ammount"]
                        row["Date"] = row["Date"].strftime("%m/%d/%y %H:%M:%S")

                        debit_transactions_list.append(row)

                        if date_tuple in dates_set_debit:
                            dates_set_debit[date_tuple]["Amount"] += row["Ammount"]
                            dates_set_debit[date_tuple]["Count"] += 1

                        else:
                            dates_set_debit[date_tuple] = {
                                "Amount": row["Ammount"],
                                "Count": 1
                            }
                    elif row["Type"] == "Credit":
                        credit_balance += row["Ammount"]
                        row["Date"] = row["Date"].strftime("%m/%d/%y %H:%M:%S")

                        credit_transactions_list.append(row)

                        if date_tuple in dates_set_credit:
                            dates_set_credit[date_tuple]["Amount"] += row["Ammount"]
                            dates_set_credit[date_tuple]["Count"] += 1
                        else:
                            dates_set_credit[date_tuple] = {
                                "Amount": row["Ammount"],
                                "Count": 1
                            }
                logger.info("balance computed")
                mail_text = generate_mail(debit_balance, credit_balance, dates_set_debit, dates_set_credit)
                logger.info("email generated")
                conn.commit()
                
                
                # send account summary through sns
                response = aws_client.publish(
                    TopicArn=sns_topic,
                    Message=json.dumps({
                        "client": client["Email"],
                        "subject": "Your Balance",
                        "html": mail_text,
                    })
                )
                logger.info(response)
                return {
                    "credit_transactions": credit_transactions_list,
                    "debit_transactions": debit_transactions_list,
                    "credit_balance": credit_balance,
                    "debit_balance": debit_balance,
                    "status": HTTPStatus.OK
                }
            else:
                return {
                    "message": f"user {client_id} don't exist",
                    "status": HTTPStatus.BAD_REQUEST
                }
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"exc_type: {exc_type}, fname: {fname}, lineno: {exc_tb.tb_lineno}")
        logger.error(f"exc_type: {exc_type}, fname: {fname}, lineno: {exc_tb.tb_lineno}")
        raise
