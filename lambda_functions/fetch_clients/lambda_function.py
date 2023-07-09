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
    This function fetches the clients from client table ***DEV Only***
    """
    try:

        with conn.cursor() as cur:
            cur.execute("select * from Client")
            logger.info("The following items have been added to the database:")
            item_count = 0
            for row in cur:
                item_count += 1
                logger.info(row)
        conn.commit()
    except Exception as ex:
        return {
            "message": str(ex),
            "status": HTTPStatus.INTERNAL_SERVER_ERROR
        }
