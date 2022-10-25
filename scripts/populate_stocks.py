import psycopg2, psycopg2.extras, requests, json
from iexfinance.stocks import Stock
from iexfinance.refdata import get_symbols
from iexfinance.stocks import get_historical_intraday
import pandas as pd
from datetime import datetime
from config.config import *
import alpaca_trade_api as alpaca_api
import functions

sp500 = functions.get_sp_symbols()

etfs = functions.get_etf_symbols()

connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

cursor.execute("SELECT symbol from stock")

existing_symbols = cursor.fetchall()

# symbols = requests.get(f'https://cloud.iexapis.com/stable/ref-data/symbols?token={IEX_TOKEN}').json()
# crypto = requests.get(f'https://cloud.iexapis.com/stable/ref-data/crypto/symbols?token={IEX_TOKEN}').json()

# print(json.dumps(crypto, indent=2))

# print(len(crypto))

# for index in range(len(crypto)):
#     print(crypto[index]["symbol"])


symbols = get_symbols(token=IEX_TOKEN)

for index, asset in symbols.iterrows():
    is_etf = True if asset["type"] == 'et' else False

    is_sp500 = True if asset["symbol"] in sp500 else False

    if (is_sp500 or asset['symbol'] in etfs) and [asset['symbol']] not in existing_symbols:

        asset['exchange'] = "NYSE" if asset['exchange'] == "XNYS" else asset['exchange']
        asset['exchange'] = "NASDAQ" if asset['exchange'] == "XNAS" else asset['exchange']
    
        try:
            print(f"Inserting {asset['symbol']} - {asset['name']}")
            cursor.execute("""
                INSERT INTO stock (name, symbol, exchange, is_sp500, is_etf)
                VALUES (%s, %s, %s, %s, %s)
            """, (asset['name'], asset['symbol'], asset['exchange'], is_sp500, is_etf))
        except Exception as e:
            print(f"ERROR:{asset}")
            print(e)
    else:
        print(f"{asset['symbol']} not added or already exists")
    
connection.commit()