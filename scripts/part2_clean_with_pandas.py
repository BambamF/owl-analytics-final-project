import pandas as pd
import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
messy_data_csv = os.path.join(ROOT_DIR, 'data/messy/messy_market_data.csv')

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
    print(df.dtypes)
    print()

def print_missing_details(df: pd.DataFrame):
    missing_values = df.isnull().sum()
    most_affected = missing_values.idxmax()
    print(f"Missing values:")
    print(missing_values.sort_values(ascending=False).head(3))
    print(f"Most affected column: {most_affected}")
    print()
    
def convert_numerics(df: pd.DataFrame):
    numerics = ["open", "high", "low", "close", "volume", "quote_volume", "trade_count"]
    for numeric in numerics:
        df[numeric] = pd.to_numeric(df[numeric], errors='coerce')
    invalid_rows = df[numerics].isna().sum().sum()
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

    symbol_df = df['symbol'].unique()

    df['symbol'] = (
    df['symbol']
    .str.upper()
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

def remove_duplicates(df: pd.DataFrame):
    new_df = df.drop_duplicates()
    print(f"")

def main():
    df = load_csv()
    print_df_details(df)
    print_missing_details(df)
    new_df = convert_numerics(df)
    convert_timestamps(new_df)



if __name__ == "__main__":
    main()