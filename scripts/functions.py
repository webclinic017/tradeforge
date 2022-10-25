from cgitb import text
import bs4 as bs
import requests
import psycopg2, psycopg2.extras
# from config.config import *

def get_sp_symbols():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    sp_symbols = []

    for row in table.findAll('tr')[1:]:
        sp_symbol = row.findAll('td')[0].text
        sp_symbols.append(sp_symbol)

    sp500 = list(map(lambda s: s.strip(), sp_symbols))

    return sp500

def get_etf_symbols():
    resp = requests.get('https://etfdb.com/compare/volume/')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'table'})
    etf_symbols_volume = []

    for row in table.findAll('tr')[1:]:
        etf_symbol = row.findAll('td')[0].text
        etf_symbols_volume.append(etf_symbol)

    resp = requests.get('https://etfdb.com/compare/market-cap/')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'table'})
    etf_symbols_assets = []

    for row in table.findAll('tr')[1:]:
        etf_symbol = row.findAll('td')[0].text
        etf_symbols_assets.append(etf_symbol)

    etfs = etf_symbols_assets + etf_symbols_volume

    return etfs

def get_crypto_symbols():
    resp = requests.get('https://coinmarketcap.com/')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'cmc-table'})
    # print(table)
    crypto_symbols = []

    for row in table.findAll('tr'): 
        print(row)
        crypto_symbol = row.find('span',{'class':'crypto-symbol'})
        print(crypto_symbol)
        # print(crypto_symbol.findAll(text=True))
        # crypto_symbol = row.findAll('td')[0].text
        # crypto_symbols.append(crypto_symbol)

    # crypto = list(map(lambda s: s.strip(), crypto_symbols))

    # return crypto_symbols

# def connect_db():

#     connection = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

#     cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

#     return cursor, connection

    