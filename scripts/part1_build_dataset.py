import csv
from datetime import datetime
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import requests
import logging
from typing import Dict, Any
import time
from ratelimit import limits, sleep_and_retry
from datetime import timedelta
from RateLimiter import RateLimiter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
request_limit = 100
rate_limiter = RateLimiter(max_calls=request_limit, period=60)

mutex = threading.Lock()

def add_record_to_csv(rows: list[Dict[str, Any]], csv_path: str | Path):
    with mutex:
        file_exists = os.path.isfile(csv_path)
        is_empty = os.path.getsize(csv_path) == 0  if file_exists else True
        with open(csv_path, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
            if is_empty:
                writer.writeheader()
            writer.writerows(rows)
            print(f"Saved batch of {len(rows)} row for {rows[0]['symbol']} to path {csv_path}")


def download_row(url: str | Path, symbol: str, interval: str, params: Dict[str, str], csv_path: str | Path):
    rate_limiter.acquire()
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data:
            logging.warning(f"No data for symbol: {symbol}")
            return None
        parsed_rows = []
        for record in data:
            row = {
                "symbol": symbol,
                "interval": interval,
                "open_time": record[0],
                "open": record[1],
                "high": record[2],
                "low": record[3],
                "close": record[4],
                "volume": record[5],
                "close_time": record[6],
                "quote_volume": record[7],
                "trade_count": record[8],
            }
            parsed_rows.append(row)
        add_record_to_csv(parsed_rows, csv_path)
        print(f"Downloaded {symbol}: {len(parsed_rows)} records")
        return response
    except Exception as e:
        logging.error(f"Download Failed - Url: {url} | Symbol: {params['symbol']} | Timestamp: {datetime.now()} | Exception: {e}")


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

    interval = "1h"
    limit = 1000
    assert len(symbols) == 10

    url = "https://data-api.binance.vision/api/v3/klines"

    params = {
        "interval":interval,
        "limit":limit
    }

    response_futures: list = []

    
    with ThreadPoolExecutor(max_workers=4) as executor:
        
        print()
        print(f"Starting multithreaded download for 10 symbols")
        used_symbols: set[str] = set()
        for symbol in symbols:
            if symbol in used_symbols:
                continue
            used_symbols.add(symbol)
            params_extended = {"symbol": symbol, **params}
            download_future = executor.submit(download_row, url, symbol, interval, params_extended, csv_path)
            response_futures.append(download_future)
        for future in as_completed(response_futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Future Failed - Url: {url} | Future: {future} | Timestamp: {datetime.now()} | Exception: {e}")
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
    logging.basicConfig(level=logging.INFO)
    main()
