import pandas as pd
import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
messy_data_csv = os.path.join(ROOT_DIR, 'data/messy/messy_market_data.csv')
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT']

def load_csv():
    if not os.path.isfile(messy_data_csv):
        raise FileNotFoundError(messy_data_csv)
    df = pd.read_csv(messy_data_csv)
    return df

def print_df_details(df: pd.DataFrame):
    rows, columns = df.shape
    print()
    print(f"Loaded {messy_data_csv}")
    print(f"Rows: {rows}")
    print(f"Columns: {columns}")
    print()
    print(f"First 10 rows shown")
    print(df.head(10))
    print()
    print(df.dtypes.to_string())
    print()

def print_missing_details(df: pd.DataFrame):
    missing_values = df.isnull().sum()
    most_affected = missing_values.idxmax()
    print(f"Missing values:")
    print(missing_values.sort_values(ascending=False).head(3))
    print(f"Most affected column: {most_affected}")
    print()
    return missing_values.sum()
    
def convert_numerics(df: pd.DataFrame):
    numerics = ["open", "high", "low", "close", "volume", "quote_volume", "trade_count"]
    for numeric in numerics:
        df[numeric] = pd.to_numeric(df[numeric], errors='coerce')
    invalid_rows = df[numerics].isna().any(axis=1).sum()
    print(f"Converted numeric columns:\n{", ".join(numerics)}")
    print(f"Invalid numeric rows after conversion: {invalid_rows}")
    print()
    return df

def convert_timestamps(df: pd.DataFrame):

    time_columns = ["open_time", "close_time"]

    for t in time_columns:
        df[t] = pd.to_datetime(df[t], errors='coerce')
        print(f"Invalid {t} values: {df[t].isna().sum()}")
    print()
    return df

def remove_duplicates(df: pd.DataFrame):
    new_df = df.drop_duplicates(
    subset=["symbol", "interval", "open_time"]
    )
    print(f"Duplicated rows found: {df.shape[0] - new_df.shape[0]}")
    print(f"Rows before duplicates removed: {df.shape[0]}")
    print(f"Rows after duplicates removed: {new_df.shape[0]}")
    print()
    return new_df

def clean_symbols(df: pd.DataFrame):
    symbol_df = df['symbol'].unique()

    df['symbol'] = (
    df['symbol']
    .str.upper()
    .str.strip()
    .str.replace(" ", "", regex=False)
    .str.replace("/", "", regex=False)
    )

    cleaned_symbol_df = df['symbol'].unique()

    print(f"Symbol before cleaning: {symbol_df}")
    print()
    print(f"Symbol after cleaning: {cleaned_symbol_df}")
    print()
    print(f"Unique cleaned symbols: {df['symbol'].nunique()}")
    print()
    return df

def clean_missing_values(df):

    before = df.isna().sum().sum()

    new_df = df.dropna()

    after = df.isna().sum().sum()

    print(f"Missing values removed: {before}")
    print(f"Missing values remaining: {after}")
    print()

    return new_df

def clean_impossible_numerics(df: pd.DataFrame):
    numerics = ["open", "high", "low", "close", "volume", "quote_volume", "trade_count"]

    column_n_neg_values = {numeric:int(df[numeric].lt(0).sum()) for numeric in numerics}

    mask = (df[numerics] < 0).any(axis=1)
    old_total_neg_values = mask.sum()

    df = df[~mask]

    final_total_neg_values = df[numerics].lt(0).sum().sum()

    pre_high_low_clean = (df["high"] < df["low"]).sum()

    df = df[df["high"] >= df["low"]]

    post_high_low_clean = (df["high"] < df["low"]).sum()

    print(f"Invalid numeric values per column: {str(column_n_neg_values)}")
    print(f"Total Negative rows: {old_total_neg_values}")
    print(f"Total negative rows after cleaning: {final_total_neg_values}")
    print(f"Rows where high < low: {pre_high_low_clean}")
    print(f"Rows where high < low after cleaning: {post_high_low_clean}")
    print()
    return df



def compute_columns(df: pd.DataFrame):
    new_columns = ["price_range", "price_change", "percent_change", "candle_direction"]
    numerics = ["open", "high", "low", "close", "volume", "quote_volume", "trade_count"]
    example_columns = numerics + new_columns
    df["price_range"] = df["high"] - df["low"]
    df["price_change"] = df["close"] - df["open"]
    df["percent_change"] = ((df["price_change"] / df["open"]) * 100).replace([float("inf"), float("-inf")], pd.NA)
    df.loc[df["open"] == 0, "percent_change"] = pd.NA
    df.loc[df["close"] < df["open"], "candle_direction"] = "down"
    df.loc[df["close"] > df["open"], "candle_direction"] = "up"
    df.loc[df["close"] == df["open"], "candle_direction"] = "flat"
    print(f"Created columns:\n{str(new_columns)}")
    print()
    print("Example row:")
    row = df.iloc[1]
    for column in example_columns:
        value = row[column]
        if isinstance(value, float):
            print(f"{column}={value:.2f}")
        else:
            print(f"{column}={value}")
    print()
    return df

def clean_run(df: pd.DataFrame):
    new_df = convert_numerics(df)
    new_df = convert_timestamps(new_df)
    new_df = clean_symbols(new_df)
    new_df = remove_duplicates(new_df)
    new_df  = clean_impossible_numerics(new_df)
    new_df = clean_missing_values(new_df)
    new_df = compute_columns(new_df)
    return new_df

def print_data_state(old_df: pd.DataFrame, new_df: pd.DataFrame):
    print("Data-quality report:")
    print(f"Rows before cleaning: {old_df.shape[0]}")
    print(f"Rows after cleaning: {new_df.shape[0]}")
    print(f"Missing values before: {old_df.isnull().sum().sum()}")
    print(f"Missing values after: {new_df.isnull().sum().sum()}")
    print(f"Duplicate rows before: {old_df.duplicated().sum().sum()}")
    print(f"Duplicate rows after: {new_df.duplicated().sum().sum()}")
    print(f"Cleaning decision: invalid rows were removed because they contained impossible values such as negative volume or high appearing to be less than low")
    print()

def sample_check(df: pd.DataFrame, n_sample: int, sample_path: str):
    df_list = []
    for symbol in symbols:
        df_list.append(df[df["symbol"] == symbol].sample(n=n_sample, random_state=1))
    new_df = pd.concat(df_list, ignore_index=True)
    print("Average closing price by symbol:")
    for symbol in new_df["symbol"].unique():
        print(f"{symbol}: {new_df[new_df["symbol"] == symbol]["close"].mean():.2f}")
    print()
    print(f"Highest average volume: {new_df.groupby("symbol")["volume"].mean().idxmax()}")
    print()
    print("Candle direction counts: ")
    for direction in ("up", "down", "flat"):
        print(f"{direction}: {(new_df["candle_direction"] == direction).sum()}")
    print()
    print(f"Largest price range: {new_df.loc[new_df["price_range"].idxmax()]["symbol"]}")
    print()

    results = {
    "highest_volume_symbol": new_df.groupby("symbol")["volume"].mean().idxmax(),
    "largest_price_range_symbol": new_df.loc[new_df["price_range"].idxmax(), "symbol"],
    "up_candles": (new_df["candle_direction"] == "up").sum(),
    "down_candles": (new_df["candle_direction"] == "down").sum(),
    "flat_candles": (new_df["candle_direction"] == "flat").sum()
    }

    pd.DataFrame([results]).to_csv(sample_path, index=False)
    print()

def print_rundown(n_rows: int, n_symbols: int, rec_p_sym: int, q_ans: int, csv_path: str):
    print(f"Saved {csv_path}")
    print(f"Sample rows used: {n_rows}")
    print(f"Symbols included: {n_symbols}")
    print(f"Records per symbol: {rec_p_sym}")
    print(f"Questions answered: {q_ans}")
    print()
    print(
            "Pandas is useful for checking and cleaning data but not for full dataset analysis because "
            "it gives you access to useful tools that allow you to correct inconsistencies and potentially "
            "corrupted data. However, it is not well suited to analysis of potentially very large datasets "
            "as it is unable to take advantage of speed efficient algorithms like MapReduce and "
            "it is also unable to take advantage of distributed computing. "
            "This limits it to slower sorting and fetching algorithms which can be ideal sometimes but "
            "can also result in slow processing."
            )
    print()

def main():
    df = load_csv()
    original_df = df.copy(deep=True)
    print_df_details(original_df)
    print_missing_details(original_df)
    clean_df = clean_run(df)
    print_data_state(original_df, clean_df)
    cleaned_csv = os.path.join(ROOT_DIR, 'data/clean/cleaned_market_data.csv')
    sample_csv = os.path.join(ROOT_DIR, 'results/pandas_sample_results.csv')
    sample_check(clean_df, 5, sample_csv)
    clean_df.to_csv(cleaned_csv, float_format ="%.2f", index=False)
    print_rundown(
    len(clean_df),
    clean_df["symbol"].nunique(),
    5,
    4,
    cleaned_csv
    )

    



if __name__ == "__main__":
    main()