import pymysql
import pandas as pd

def get_connection():
    """
    Establishes a connection to MySQL via SSH tunnel on localhost:3307.
    """
    return pymysql.connect(
        host='127.0.0.1',
        port=3307,
        user='dbuser',
        password='MyP@ssw0rd2025!',
        db='my_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_usage_records(limit=10):
    """
    Fetches a specified number of records using a raw cursor and returns a DataFrame.
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM usage_records LIMIT %s", (limit,))
        rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)

def fetch_products(limit=10):
    """
    Fetches a specified number of products using a raw cursor and returns a DataFrame.
    """
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM products LIMIT %s", (limit,))
        rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows)

if __name__ == '__main__':
    # Display the first 10 usage records
    df_usage = fetch_usage_records(10)
    print("=== Usage Records Sample ===")
    print(df_usage.to_string(index=False), "\n")

    # Display the first 10 products
    df_products = fetch_products(10)
    print("=== Products Sample ===")
    print(df_products.to_string(index=False))

