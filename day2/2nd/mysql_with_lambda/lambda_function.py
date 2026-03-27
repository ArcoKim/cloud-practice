import json
import os
import pymysql

conn = None


def get_connection():
    global conn
    if conn is None or not conn.open:
        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            connect_timeout=5,
            read_timeout=5,
            cursorclass=pymysql.cursors.DictCursor,
        )
    return conn


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    name = params.get("name")

    if not name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "name parameter is required"}),
        }

    try:
        with get_connection().cursor() as cur:
            cur.execute("SELECT id, name FROM product WHERE name = %s", (name,))
            row = cur.fetchone()
    except Exception:
        global conn
        conn = None
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "internal server error"}),
        }

    if row is None:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "product not found"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(row),
    }