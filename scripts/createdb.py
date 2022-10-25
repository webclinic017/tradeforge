import psycopg2, psycopg2.extras
from config.config import *


connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

strategies = ['opening_range_breakout', 'opening_range_breakdown']

for strategy in strategies:
    cursor.execute("""
        INSERT INTO strategy (name) VALUES (%s)
    """, (strategy,))

connection.commit()

