# Owl Analytics: Cryptocurrency Analysis Report

In this project, I collected, cleaned and analysed cryptocurrency market data.
The work flow involed acquiring, cleaning and then analysing the data in three stages administered through three teams.
The first stage downloaded raw market data from an API, the second stage cleaned and prepared the data using pandas, and the final stage analysed the complete cleaned dataset using Spark. This separation allowed each tool to be used where it was most effective.

## API Downloader

The API downloader was responsible for retrieving historical market data for multiple cryptocurrency symbols. The downloader sent requests to the market data API and collected records containing information such as opening price, highest price, lowest price, closing price, trading volume, quote volume, and trade count.

The downloader was designed to handle multiple symbols efficiently by using concurrent requests rather than downloading each symbol sequentially. Each API request was assigned as a separate task, allowing several symbols to be downloaded at the same time. This reduced the total download time while still respecting the limitations imposed by the API.

The downloader also included error handling to make the process more reliable. If a request failed because of a temporary network issue or API error, the program could identify the failure rather than silently producing incomplete data. Logging was used to record important events such as successful downloads, failed requests, and processing progress.

## Limiting Concurrent API Requests

Although concurrency improved performance, unlimited concurrent requests would risk overwhelming the API or causing requests to be rejected due to rate limits. To prevent this, the downloader limited the number of simultaneous API requests.

A controlled worker pool was used so that only a fixed number of requests could run at the same time. This provided a balance between speed and reliability. Instead of creating a new request thread for every symbol, the program reused a limited number of workers. This approach reduced resource usage and ensured that the downloader remained within acceptable API usage limits.

Limiting concurrency also made failures easier to manage. If too many requests were sent simultaneously, a large number of requests could fail together. By controlling the request rate, the downloader produced more consistent results.

## Protecting the Log File

The log file required protection because multiple concurrent tasks could attempt to write to it at the same time. Without protection, simultaneous writes could interfere with each other and produce corrupted or incomplete log messages.

For example, two threads could attempt to write separate messages at the same moment, causing the text from both messages to become mixed together. This would make debugging difficult because the order and content of events would no longer be reliable.

To solve this problem, access to the log file was synchronised. A locking mechanism ensured that only one worker could write to the file at a time. This guaranteed that log entries remained complete and readable while still allowing the downloading tasks themselves to run concurrently.

## Data Cleaning Performed by Dara

After the raw data was collected, Dara processed the dataset to identify and remove inconsistencies. The original dataset contained several quality issues that needed to be corrected before analysis.

The cleaning process first converted columns into the correct data types. Numeric columns such as open price, high price, low price, close price, volume, quote volume, and trade count were converted into numeric formats. Invalid numeric values were converted into missing values so they could be identified. Timestamp columns were also converted into proper datetime formats.

Duplicate records were removed because repeated rows could distort later analysis. Symbol values were cleaned by converting them to uppercase and removing unnecessary spaces and formatting differences. This ensured that symbols such as "btc/usdt" and "BTCUSDT" were treated as the same asset.

Impossible numeric values were also removed. Examples included negative trading volumes and cases where the recorded high price was lower than the low price. These records represented invalid market data and could negatively affect calculations.

Additional calculated columns were created during cleaning. These included price range, price change, percentage change, and candle direction. Price range measured the difference between the high and low prices, while candle direction classified each record as an upward, downward, or flat movement depending on whether the closing price was higher, lower, or equal to the opening price.

## Why Pandas Was Used Only on a Small Sample

Pandas was used during the cleaning stage because it provides a simple and powerful interface for inspecting and transforming tabular data. It was useful for checking missing values, correcting data types, removing invalid rows, and performing quick validation checks.

However, pandas loads the entire dataset into memory on a single machine. This makes it unsuitable for very large datasets where the amount of data exceeds available memory. Pandas also does not provide built-in distributed processing capabilities.

For this reason, pandas was only used for a small sample analysis after cleaning. The sample allowed quick verification of the results, including checking average closing prices, candle direction counts, and symbol-level information. This provided confidence that the cleaning process worked correctly without requiring expensive processing on the full dataset.

## Why Spark Was Used for Full Analytics

Zehra requested Spark for the final analytics because the client required analysis across the complete cleaned dataset rather than a small sample. Spark is designed for large-scale data processing and can distribute computation across multiple processing units.

Using Spark allowed the full dataset to be analysed efficiently. Instead of loading everything into local memory like pandas, Spark can process data using distributed computation. Spark SQL also provided an effective way to perform grouped analysis, filtering, sorting, and aggregation.

The Spark analysis included average prices by symbol, volume comparisons, record counts, volatility rankings, activity rankings, and time-based market activity analysis. These calculations required the full dataset to produce reliable results.

## Final Analytics Results

The final Spark analysis produced a ranked market summary containing one row per cryptocurrency symbol. The summary included total records, average volume, total trades, average percentage change, average price range, candle direction counts, volatility ranking, and activity ranking.

The volatility analysis identified which symbols experienced the largest price movements by comparing average and standard deviation of price ranges. Symbols with larger price ranges were considered more volatile because their prices changed more significantly during trading periods.

The activity analysis ranked symbols based on total trade count and quote volume. This showed which cryptocurrencies were the most actively traded during the analysed period.

Time-based analysis examined trading activity by hour and date. This identified when trading activity was highest based on total trades and quote volume.

Overall, the final Spark report provided a complete view of market behaviour across all cleaned records. The results were more reliable than the pandas sample because they considered the entire dataset rather than only a small subset. The final ranked summary gave Zehra a clear overview of the most active and most volatile symbols to include in the client report.