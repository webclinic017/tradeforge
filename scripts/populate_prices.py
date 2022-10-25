import psycopg2, psycopg2.extras, requests
import pandas as pd
from datetime import datetime
from iexfinance.stocks import Stock
from iexfinance.refdata import get_symbols
from iexfinance.stocks import get_historical_intraday
from config.config import *
import alpaca_trade_api as alpaca_api

connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

cursor.execute("SELECT id, symbol from stock")

existing_symbols = pd.DataFrame(cursor.fetchall(), columns=['id', 'symbol'])

stock_dict = {}

for index, asset in existing_symbols.iterrows():
    stock_dict[asset.symbol] = asset.id

batch_size = 100

for i in range(0, len(existing_symbols), batch_size):
    symbol_batch = existing_symbols[i:i+batch_size]
    symbol_batch_list = symbol_batch['symbol'].values.tolist()
    symbol_batch_string = ",".join(symbol_batch_list)
    request = requests.get(f'https://cloud.iexapis.com/stable/stock/market/batch?symbols={symbol_batch_string}&types=chart&range=1y&token={IEX_TOKEN}').json()
    
    for symbol in symbol_batch_list:
        print(f"inserting price data for {symbol}")
        # df = pd.DataFrame(request[symbol]["chart"])
        # print(df)
        # print(df.ffill())
        stock_id = stock_dict[symbol]

        for bar in request[symbol]["chart"]:            
            # dt = bar["date"] + bar["minute"]

            # dt = datetime.strptime(dt, "%Y-%m-%d%H:%M")

            try:
                cursor.execute("""
                    INSERT INTO stock_price (datetime, stock_id, open, high, low, close, volume)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)
                """, (bar["date"], stock_id, bar["open"], bar["high"], bar["low"], bar["close"], bar["volume"]))
            except Exception as e:
                print(e)

connection.commit()