import csv
from datetime import datetime
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
import logging
from typing import Dict, Any
from RateLimiter import RateLimiter


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
request_limit = 100
rate_limiter = RateLimiter(max_calls=request_limit, period=60)
interval = "1h"
limit = 1000

mutex = threading.Lock()

csv_initialised = False
session = requests.Session()

log_path = os.path.join(ROOT_DIR, 'reports/api_download.log')

def to_iso(ts):
    return datetime.fromtimestamp(ts / 1000).isoformat()

def add_record_to_csv(rows: list[Dict[str, Any]], csv_path: str | Path):
    global csv_initialised
    FIELDNAMES = [
    "symbol",
    "interval",
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume"
]
    with mutex:
        with open(csv_path, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
            if not csv_initialised:
                writer.writeheader()
                csv_initialised = True
            writer.writerows(rows)
            print(f"Saved batch of {len(rows)} row for {rows[0]['symbol']} to path {csv_path}")


def download_row(url: str, symbol: str, interval: str, params: Dict[str, str], csv_path: str | Path):
    rate_limiter.acquire()
    try:
        logging.info(f"START request symbol={symbol} interval={interval} limit={limit}")
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if len(data) != 1000:
            logging.warning(f"Unexpected row count for {symbol}: {len(data)}")
        if len(data) < 1000:
            raise ValueError(f"Incomplete data for {symbol}: {len(data)} rows")
        
        if not data:
            logging.warning(f"No data for symbol: {symbol}")
            return None
        
        parsed_rows = []

        for record in data:
            row = {
                "symbol": symbol,
                "interval": interval,
                "open_time": to_iso(record[0]),
                "open": record[1],
                "high": record[2],
                "low": record[3],
                "close": record[4],
                "volume": record[5],
                "close_time": to_iso(record[6]),
                "quote_volume": record[7],
                "trade_count": record[8],
                "taker_buy_base_volume": record[9],
                "taker_buy_quote_volume": record[10]
            }
            parsed_rows.append(row)

        add_record_to_csv(parsed_rows, csv_path)

        logging.info(f"END request symbol={symbol} records={len(parsed_rows)}")
        logging.info(f"WROTE csv={csv_path} records={len(parsed_rows)}")

        print(f"Downloaded {symbol}: {len(parsed_rows)} records")

    except Exception as e:

        logging.error(f"Download Failed - Url: {url} | Symbol: {params['symbol']} | Timestamp: {datetime.now()} | Exception: {e}")
        raise(e)

def main():
    csv_path = os.path.join(ROOT_DIR, "data/clean/clean_market_data.csv")
    if os.path.isfile(csv_path):
        os.remove(csv_path)
    results_api_path = os.path.join(ROOT_DIR, "results/api_download.log")
    results_runtime_path = os.path.join(ROOT_DIR, "results/runtime_comparisons.csv")

    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    Path(results_api_path).parent.mkdir(parents=True, exist_ok=True)
    Path(results_runtime_path).parent.mkdir(parents=True, exist_ok=True)

    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT']

    assert len(symbols) == 10

    url = "https://data-api.binance.vision/api/v3/klines"

    params = {
        "interval":interval,
        "limit":limit
    }

    response_futures: list = []

    
    with ThreadPoolExecutor(max_workers=20) as executor:
        
        print()
        print(f"Starting multithreaded download for 10 symbols")
        for symbol in symbols:
            params_extended = {"symbol": symbol, **params}
            download_future = executor.submit(download_row, url, symbol, interval, params_extended, csv_path)
            response_futures.append(download_future)
        for future in as_completed(response_futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Future Failed - Url: {url} | Future: {future} | Timestamp: {datetime.now()} | Exception: {e}")
                print(e)
        print(f"Multithreaded download completed")
        print()

        print(f"Request limit: {request_limit} requests per minute")
        print(f"Current request batch allowed")
        print(f"Rate-limit wait events logged: {rate_limiter.wait_calls}")
        print()

    if os.path.isfile(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for _ in csv.reader(f)) - 1
            print()
            print(f"Symbols Configured: {total_rows}")
            print(f"Interval: {interval}")
            print(f"Limit Per Symbol: {limit}")
            print(f"Expected Records: 10000")
            print()
            if os.path.isdir(os.path.join(ROOT_DIR, "data/clean")) \
                    and os.path.isdir(os.path.join(ROOT_DIR, "results")):
                print(f"Created Folders: data/clean, results")
            print(f"Saved: data/clean/clean_market_data.csv")
            print(f"Total Records: {total_rows}")
            print(f"Record Count Check: {'passed' if total_rows == 10_000 else 'failed'}")
            print()
    else:
        print(f"CSV path does not exist: {csv_path}")
    

if __name__ == "__main__":
    logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
    )
    with open(log_path, 'a', encoding="utf-8", newline="") as log_file:
        main()
