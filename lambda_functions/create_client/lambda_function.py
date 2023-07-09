import sys
import logging
import pymysql
import os
from http import HTTPStatus

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
    """
    This function stores a client record in the database
    if the client already exist, returns its ID
    """
    try:
        client_email = event.get('Email')
        client_name = event.get('Name')


        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                f"SELECT * FROM Client WHERE Email='{client_email}' LIMIT 1")
            result = cur.fetchall()
            if not result:
                query_string = f"insert into Client (Name, Email) values('{client_name}', '{client_email}')"

                cur.execute(query_string)
                conn.commit()
                logger.info(f"stored client {client_email}")
                return {
                    "id": cur.lastrowid,
                    "message": "created",
                    "status": HTTPStatus.CREATED
                }
            else:
                client = result[0]
                return {
                    "id": client["ID"],
                    "message": f"user {client_email} already exist",
                    "status": HTTPStatus.BAD_REQUEST
                }
    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        raise
