CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY, 
    symbol TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    is_etf BOOLEAN,
    is_sp500 BOOLEAN,
    sector TEXT,
    industry TEXT
);

CREATE TABLE IF NOT EXISTS etf (
    id SERIAL PRIMARY KEY, 
    symbol TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crypto (
    id SERIAL PRIMARY KEY, 
    symbol TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS etf_holding (
    etf_id INTEGER NOT NULL,
    holding_id INTEGER NOT NULL,
    dt DATE NOT NULL,
    shares NUMERIC,
    weight NUMERIC,
    PRIMARY KEY (etf_id, holding_id, dt),
    CONSTRAINT fk_etf FOREIGN KEY (etf_id) REFERENCES stock (id),
    CONSTRAINT fk_holding FOREIGN KEY (holding_id) REFERENCES stock (id)
);

CREATE TABLE IF NOT EXISTS stock_price 
(
  datetime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  close NUMERIC,
  volume NUMERIC,
  PRIMARY KEY (stock_id, datetime),
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);

CREATE TABLE IF NOT EXISTS indicator
(
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER,
  rsi NUMERIC,
  macd NUMERIC,
  macdh NUMERIC,
  macds NUMERIC,
  adx NUMERIC,
  adx_dmp NUMERIC,
  adx_dmn NUMERIC,
  PRIMARY KEY (stock_id, dt),
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);

CREATE TABLE IF NOT EXISTS tick_data  
(
  id SERIAL PRIMARY KEY,
  dt TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  stock_id INTEGER NOT NULL,
  bid NUMERIC NOT NULL,
  ask NUMERIC NOT NULL,
  bid_vol NUMERIC,
  ask_vol NUMERIC,
  CONSTRAINT fk_stock FOREIGN KEY(stock_id) REFERENCES stock(id)
);

CREATE TABLE IF NOT EXISTS strategy (
    id SERIAL PRIMARY KEY, 
    name TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS stock_strategy (
    stock_id INTEGER NOT NULL, 
    strategy_id INTEGER NOT NULL,
    FOREIGN KEY (stock_id) REFERENCES stock (id),
    FOREIGN KEY (strategy_id) REFERENCES strategy(id)
);

CREATE INDEX ON stock_price (stock_id, datetime DESC);

-- SELECT create_hypertable('stock_price', 'dt');