import bs4 as bs
import requests
import psycopg2, psycopg2.extras

from functions import *
# from config.config import *


get_crypto_symbols()

# resp = requests.get('https://etfdb.com/compare/volume/')
# soup = bs.BeautifulSoup(resp.text, 'lxml')
# table = soup.find('table', {'class': 'table'})
# etf_symbols_volume = []

# for row in table.findAll('tr')[1:]:
#     etf_symbol = row.findAll('td')[0].text
#     etf_symbols_volume.append(etf_symbol)

# resp = requests.get('https://etfdb.com/compare/market-cap/')
# soup = bs.BeautifulSoup(resp.text, 'lxml')
# table = soup.find('table', {'class': 'table'})
# etf_symbols_assets = []

# for row in table.findAll('tr')[1:]:
#     etf_symbol = row.findAll('td')[0].text
#     etf_symbols_assets.append(etf_symbol)

# etf_symbols = etf_symbols_assets + etf_symbols_volume

# print(etf_symbols)

