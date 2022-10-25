import psycopg2, psycopg2.extras, requests
import pandas as pd
from datetime import datetime, date, timedelta
from iexfinance.stocks import Stock, get_historical_intraday, get_historical_data
from config.config import *
from send_raw_mail import *

#store the current date or a custom date for testing
today = date.today()
# today = datetime(2022, 10, 21)

#only run the script if the date above is a weekday
if today.weekday() == 0:
    expiration = today + timedelta(days = 4)
elif today.weekday() == 1:
    expiration = today + timedelta(days = 3)
elif today.weekday() == 2:
    expiration = today + timedelta(days = 2)
elif today.weekday() == 3:
    expiration = today + timedelta(days = 1)
elif today.weekday() == 4:
    expiration = today + timedelta(days = 7)
else:
    print("it is not a trading day (M - F)")
    quit()

# query database for opening range stategies that are applied to a stock
connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor.execute("""
        select stock_strategy.stock_id, stock_strategy.strategy_id, stock.symbol as symbol, strategy.name as strategy
        from stock_strategy
        join stock on stock_strategy.stock_id = stock.id
        join strategy on stock_strategy.strategy_id = strategy.id
        where strategy.name like 'opening_range%'
    """)
rows = cursor.fetchall()

#store start and end of 15 minute opening range
start_minute_bar = f"{today} 09:30:00"
end_minute_bar = f"{today} 09:45:00"

#loop through stock strategies for processing
for row in rows:
    #store symbol and strategy in vars
    symbol = row["symbol"]
    strategy = row["strategy"]
    print(f"processing {strategy} for {symbol}")

    #get the latest intraday minute data for stock
    df = get_historical_intraday(symbol, today, token=IEX_TOKEN)
    # print(df) 

    #store minute bars for first 15 minutes
    opening_range_mask = (df.index >= start_minute_bar) & (df.index <= end_minute_bar)
    opening_range_bars = df[opening_range_mask]

    #store minute bars for after first 15 minutes
    after_opening_range_mask = (df.index > end_minute_bar)
    after_opening_range_bars = df[after_opening_range_mask]

    #calc the 15 minute opening range
    opening_range_low = opening_range_bars["low"].min()
    opening_range_high = opening_range_bars["high"].max()
    opening_range = round(opening_range_high - opening_range_low, 2)

    # print(f"Opening Range Low: {opening_range_low}")
    # print(f"Opening Range High: {opening_range_high}")
    # print(f"Opening Range: {opening_range}")
    # print(opening_range_bars)

    #get the current price of stock symbol
    stock = Stock(f'{symbol}', token=IEX_TOKEN)
    quote = stock.get_price()
    quote = quote[f"{symbol}"].price
    # print(f"Current Price: {quote}")

    #round current price to closest dollar for ATM option strike price
    strike_price = round(quote)

    #init symbol vars to build option symbol
    expiration_symbol = expiration.strftime("%y%m%d")
    strike_symbol = str(strike_price).zfill(5)
    call = 'C'
    put = 'P'

    if strategy == "opening_range_breakout":

        #get minute bars where the close is greater than the opening range
        breakout_signal = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

        #build option symbol
        option_symbol = symbol + expiration_symbol + call + strike_symbol + '000'

        # print(option_symbol)

        try:
            #send request to get available option chains
            response = requests.get('https://sandbox.tradier.com/v1/markets/options/chains',
                params={'symbol': symbol, 'expiration': expiration},
                headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY}', 'Accept': 'application/json'}
            )
            json_response = response.json()
            # print(response.status_code)
            # print(json_response)

            #create list of available option chain symbols
            option_chain_symbols = []
            for row in json_response["options"]["option"]:
                # print(row)
                option_chain_symbols.append(row["symbol"])
                # print(row["last"])

            #test if option_symbol built by script is available from broker
            if option_symbol in option_chain_symbols:
                # print(breakout_signal['close'])

                #get current price of option chain/contract
                response = requests.get('https://sandbox.tradier.com/v1/markets/quotes',
                    params={'symbols': option_symbol, 'greeks': 'false'},
                    headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY}', 'Accept': 'application/json'}
                )
                json_response = response.json()
                option_limit_price = json_response["quotes"]["quote"]["last"]

                #calc profit and loss of bracket trade
                option_take_profit = round(option_limit_price * 1.2, 2)
                option_stop_loss = round(option_limit_price * .9, 2)

                #VARS AND PAYLOAD FOR REGULAR STOCKS (NOT OPTIONS)
                # limit_price = int(breakout_signal.iloc[0]['close'])
                # take_profit = limit_price + opening_range
                # stop_loss = limit_price - opening_range
                # data={
                #             'class': 'otoco', 
                #             'duration': 'day', 
                #             'type[0]': 'limit', 
                #             'price[0]': f'{limit_price}', 
                #             'symbol[0]': f'{symbol}', 
                #             'side[0]': 'buy', 
                #             'quantity[0]': '10', 
                #             'type[1]': 'limit', 
                #             'price[1]': f'{limit_price + opening_range}', 
                #             'symbol[1]': f'{symbol}', 
                #             'side[1]': 'sell', 
                #             'quantity[1]': '10', 
                #             'type[2]': 'stop', 
                #             'stop[2]': f'{limit_price - opening_range}', 
                #             'symbol[2]': f'{symbol}', 
                #             'side[2]': 'sell', 
                #             'quantity[2]': '10'
                #         }

                #init option order payload
                data={
                        'class': 'otoco', 
                        'duration': 'day', 
                        'type[0]': 'limit', 
                        'price[0]': option_limit_price, 
                        'option_symbol[0]': option_symbol, 
                        'side[0]': 'buy_to_open', 
                        'quantity[0]': '10', 
                        'type[1]': 'limit', 
                        'price[1]': option_take_profit, 
                        'option_symbol[1]': option_symbol, 
                        'side[1]': 'sell_to_close', 
                        'quantity[1]': '10', 
                        'type[2]': 'stop', 
                        'stop[2]': option_stop_loss, 
                        'option_symbol[2]': option_symbol, 
                        'side[2]': 'sell_to_close', 
                        'quantity[2]': '10'
                    }
                # print(data)

                #send request to create order
                response = requests.post('https://sandbox.tradier.com/v1/accounts/VA41833079/orders',
                    data=data,
                    headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY}', 'Accept': 'application/json'}
                )
                print(response)
                json_response = response.json()
                # print(response.status_code)
                print(json_response)
                message = f"placing {strategy} order for {option_symbol} at {option_limit_price}, {symbol} closed above {opening_range_high}, at {breakout_signal.index[0]}"
                print(message)

                #send email with order details
                notify(message)
        except Exception as e:
            print(f"no {strategy} entry for {symbol}")
            # print(e)
            print("==========================================================")
            continue

    elif strategy == "opening_range_breakdown":
        
        breakdown_signal = after_opening_range_bars[after_opening_range_bars['close'] < opening_range_low]

        option_symbol = symbol + expiration_symbol + put + strike_symbol + '000'

        # print(option_symbol)

        try:
            response = requests.get('https://sandbox.tradier.com/v1/markets/options/chains',
                params={'symbol': symbol, 'expiration': expiration},
                headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY} ', 'Accept': 'application/json'}
            )
            json_response = response.json()
            # print(response.status_code)
            # print(json_response)
            option_chain_symbols = []
            for row in json_response["options"]["option"]:
                option_chain_symbols.append(row["symbol"])
                # print(row["last"])
                        
            if option_symbol in option_chain_symbols:
                # print(breakout_signal['close'])
                response = requests.get('https://sandbox.tradier.com/v1/markets/quotes',
                    params={'symbols': option_symbol, 'greeks': 'false'},
                    headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY}', 'Accept': 'application/json'}
                )
                json_response = response.json()

                option_limit_price = json_response["quotes"]["quote"]["last"]
                option_take_profit = round(option_limit_price * 1.2, 2)
                option_stop_loss = round(option_limit_price * .9, 2)

                limit_price = int(breakdown_signal.iloc[0]['close'])
                take_profit = limit_price + opening_range
                stop_loss = limit_price - opening_range
                
                # data = {
                #             'class': 'otoco', 
                #             'duration': 'day', 
                #             'type[0]': 'limit', 
                #             'price[0]': f'{limit_price}', 
                #             'symbol[0]': f'{symbol}', 
                #             'side[0]': 'buy', 
                #             'quantity[0]': '10', 
                #             'type[1]': 'limit', 
                #             'price[1]': f'{limit_price - opening_range}', 
                #             'symbol[1]': f'{symbol}', 
                #             'side[1]': 'sell', 
                #             'quantity[1]': '10', 
                #             'type[2]': 'stop', 
                #             'stop[2]': f'{limit_price + opening_range}', 
                #             'symbol[2]': f'{symbol}', 
                #             'side[2]': 'sell', 
                #             'quantity[2]': '10'
                #         }
                data = {
                            'class': 'otoco', 
                            'duration': 'day', 
                            'type[0]': 'limit', 
                            'price[0]': option_limit_price, 
                            'option_symbol[0]': option_symbol, 
                            'side[0]': 'buy_to_open', 
                            'quantity[0]': '10', 
                            'type[1]': 'limit', 
                            'price[1]': option_take_profit, 
                            'option_symbol[1]': option_symbol, 
                            'side[1]': 'sell_to_close', 
                            'quantity[1]': '10', 
                            'type[2]': 'stop', 
                            'stop[2]': option_stop_loss, 
                            'option_symbol[2]': option_symbol, 
                            'side[2]': 'sell_to_close', 
                            'quantity[2]': '10'
                        }
                # print(data)
                response = requests.post('https://sandbox.tradier.com/v1/accounts/VA41833079/orders',
                    data=data,
                    headers={'Authorization': f'Bearer {TRADIER_SANDBOX_KEY}', 'Accept': 'application/json'}
                )
                print(response)
                json_response = response.json()
                # print(response.status_code)
                print(json_response)
                message=f"placing {strategy} order for {option_symbol} at {option_limit_price}, {symbol} closed below {opening_range_low}, at {breakdown_signal.index[0]}"
                print(message)
                notify(message)
        except Exception as e:
            # print(e)
            print(f"no {strategy} entry for {symbol}")
            print("==========================================================")
            continue
    print("==========================================================")