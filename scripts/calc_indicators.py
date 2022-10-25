import pandas_ta as ta
import pandas as pd
import psycopg2, psycopg2.extras, requests
from config.config import *

connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

cursor.execute("SELECT id, symbol from stock")

existing_symbols = pd.DataFrame(cursor.fetchall(), columns=['id', 'symbol'])

stock_dict = {}

for i, asset in existing_symbols.iterrows():
    stock_dict[asset.symbol] = asset.id

for i, row in existing_symbols.iterrows():
    cursor.execute("""
        SELECT *
        FROM stock_price
        WHERE stock_id = %s
    """, (stock_dict[row.symbol],))

    prices = pd.DataFrame(cursor.fetchall(), columns=['datetime', 'id', 'open', 'high', 'low', 'close', 'volume'])
    prices.set_index("datetime", inplace=True)
    prices = prices.apply(pd.to_numeric)
    adx = prices.ta.adx()
    macd = prices.ta.macd()
    rsi = prices.ta.rsi()
    bbands = prices.ta.bbands()
    df = pd.concat([prices, adx, macd, rsi], axis=1)
    print(f"Calculating indicators for {row.symbol}")
    for datetime, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO indicator (dt, stock_id, rsi, macd, macdh, macds, adx, adx_dmp, adx_dmn)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (datetime, row["id"], row["RSI_14"], row["MACD_12_26_9"], row["MACDh_12_26_9"], row["MACDs_12_26_9"], row["ADX_14"], row["DMP_14"], row["DMN_14"]))
        except Exception as e:
            print(e)
            
connection.commit()

