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
import time


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
request_limit = 100
rate_limiter = RateLimiter(max_calls=request_limit, period=60)
interval = "1h"
limit = 1000

mutex = threading.Lock()

session = requests.Session()
runtime_comp_path = os.path.join(ROOT_DIR, 'results/runtime_comparison.csv')

log_path = os.path.join(ROOT_DIR, 'results/api_download.log')

def to_iso(ts):
    return datetime.fromtimestamp(ts / 1000).isoformat()

def add_record_to_csv(rows: list[Dict[str, Any]], csv_path: str | Path):
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
        file_exists = os.path.exists(csv_path)
        with open(csv_path, 'a', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
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
    
def multithreaded_download(symbols: list[str], params: dict[str, str], url: str, csv_path: str | Path, method: str, note: str):
    file_exists = os.path.isfile(runtime_comp_path)
    response_futures: list = []

    start = time.perf_counter()
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
    end = time.perf_counter()
    running_time = end - start

    RUNTIME_FIELDS = ["method", "seconds", "records", "note"]

    comparison_dict = {
        "method": method,
        "seconds": str(running_time),
        "records": limit,
        "note": note
    }

    with open(runtime_comp_path, 'a', encoding='utf-8', newline="") as runtime_csv:
        writer = csv.DictWriter(runtime_csv, fieldnames=RUNTIME_FIELDS)
        if not file_exists:
            writer.writeheader() 
        writer.writerow(comparison_dict)

    return running_time

def serial_download(symbols: list[str], params: dict[str, str], url: str, csv_path: str | Path, method: str, note: str):

    start = time.perf_counter()
    file_exists = os.path.isfile(runtime_comp_path)

    print(f"Starting serial download for {len(symbols)} symbols")
    for symbol in symbols:
            params_extended = {"symbol": symbol, **params}
            download_row(url, symbol, interval, params_extended, csv_path)

    end = time.perf_counter()

    running_time = end - start


    RUNTIME_FIELDS = ["method", "seconds", "records", "note"]

    comparison_dict = {
        "method": method,
        "seconds": str(running_time),
        "records": limit, 
        "note": note
    }

    with open(runtime_comp_path, 'a', encoding='utf-8', newline="") as runtime_csv:
        writer = csv.DictWriter(runtime_csv, fieldnames=RUNTIME_FIELDS)
        if not file_exists:
            writer.writeheader() 
        writer.writerow(comparison_dict)
    print("Serial download completed")
    print()
    return running_time

def analyse_csv(csv_path: str | Path):
    if os.path.isfile(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for _ in f) - 1
            print()
            print(f"Symbols Configured: {total_rows}")
            print(f"Interval: {interval}")
            print(f"Limit Per Symbol: {limit}")
            print(f"Expected Records: 10000")
            print()
            
            print(f"Saved: {csv_path}")
            print(f"Total Records: {total_rows}")
            print(f"Record Count Check: {'passed' if total_rows == 10_000 else 'failed'}")
            print()
    else:
        print(f"CSV path does not exist: {csv_path}")

def main():
    csv_path = os.path.join(ROOT_DIR, "data/clean/clean_market_data.csv")
    csv_parallel = os.path.join(ROOT_DIR, "data/clean/clean_market_data_parallel.csv")
    csv_serial = os.path.join(ROOT_DIR, "data/clean/clean_market_data_serial.csv")
    if os.path.isfile(csv_path):
        os.remove(csv_path)
    if os.path.isfile(csv_parallel):
        os.remove(csv_parallel)
    if os.path.isfile(csv_serial):
        os.remove(csv_serial)
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

    multi_note = "downloaded several symbols at the same time"
    serial_note = "downloaded the ten symbols one after another"

    multi_time = multithreaded_download(symbols, params, url, csv_parallel, "multithreading", multi_note)

    serial_time = serial_download(symbols, params, url, csv_serial, "serial", serial_note)

    print(f"Serial Seconds: {serial_time:.4f}\nMultithreading Seconds: {multi_time:.4f}\nSaved: {runtime_comp_path}")

    print()
    print(f"Request limit: {request_limit} requests per minute")
    print(f"Current request batch allowed")
    print(f"Rate-limit wait events logged: {rate_limiter.wait_calls}")
    print()

    if os.path.isdir(os.path.join(ROOT_DIR, "data/clean")) \
                    and os.path.isdir(os.path.join(ROOT_DIR, "results")):
        print(f"Created Folders: data/clean, results")

    analyse_csv(csv_parallel)
    analyse_csv(csv_serial)
    print()

    expected_result_files = ["data/clean/clean_market_data.csv", "results/api_download.log", "results/runtime_comparison.csv", "data/clean/clean_market_data_parallel.csv", "data/clean/clean_market_data_serial.csv"]
    result_file_counter = sum([1 for f in expected_result_files if os.path.isfile(f)])
    print(f"Script completed successfully")
    print(f"Output files found: {result_file_counter}")
    print("No price analytics were calculated in Team 1")
    print()
    

if __name__ == "__main__":
    logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
    )
    with open(log_path, 'a', encoding="utf-8", newline="") as log_file:
        main()
