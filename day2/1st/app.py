#!/usr/bin/env python3
"""
WorldPay Product Service
"""

import os
import sys
import json
import time
import math
import logging
import threading

import boto3
import pymysql
from flask import Flask, request, jsonify
from botocore.exceptions import ClientError

# ============================================================
# Configuration
# ============================================================
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-2")
SECRET_ARN = os.environ.get("SECRET_ARN", "")
DB_NAME = os.environ.get("DB_NAME", "worldpay")
APP_PORT = int(os.environ.get("APP_PORT", "8080"))

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("worldpay")

# ============================================================
# Flask App
# ============================================================
app = Flask(__name__)


# ============================================================
# Database
# ============================================================
def get_db_credentials():
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        resp = client.get_secret_value(SecretId=SECRET_ARN)
        secret = json.loads(resp["SecretString"])
        return {
            "host": secret["host"],
            "port": int(secret.get("port", 3306)),
            "username": secret["username"],
            "password": secret["password"],
        }
    except ClientError as e:
        logger.error("Failed to retrieve secret: %s", e)
        raise


def get_connection():
    creds = get_db_credentials()
    return pymysql.connect(
        host=creds["host"],
        port=creds["port"],
        user=creds["username"],
        password=creds["password"],
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
    )


# ============================================================
# Routes
# ============================================================

@app.route("/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify({"status": "ok"}), 200


@app.route("/v1/stress", methods=["GET"])
def stress():
    duration = int(request.args.get("duration", "30"))
    duration = min(duration, 300)

    def burn_cpu(seconds):
        end = time.time() + seconds
        while time.time() < end:
            math.sqrt(12345678.9)

    threads = []
    for _ in range(os.cpu_count() or 1):
        t = threading.Thread(target=burn_cpu, args=(duration,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    return jsonify({"message": f"Stress completed for {duration}s"}), 200


@app.route("/v1/product", methods=["GET"])
def get_product():
    name = request.args.get("name", "")
    if not name:
        return jsonify({"message": "name parameter is required"}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM product WHERE name = %s",
                (name,),
            )
            row = cur.fetchone()
        if row:
            return jsonify({"message": "The product is well in database"}), 200
        else:
            return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        logger.error("Query failed: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ============================================================
# Entry Point
# ============================================================
if __name__ == "__main__":
    if not SECRET_ARN:
        logger.error("SECRET_ARN environment variable must be set")
        sys.exit(1)
    logger.info("Starting WorldPay Product Service on :%s", APP_PORT)
    app.run(host="0.0.0.0", port=APP_PORT)