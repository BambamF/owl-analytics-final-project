1. What was the hardest technical problem in this project and how did you overcome it?

The hardest technical problem was building a complete data pipeline where each stage produced reliable data for the next stage. The project involved downloading data from an API, cleaning it with pandas, and analysing it with Spark. The main challenge was ensuring that the data was consistent and correctly formatted throughout the process.

The raw dataset contained several problems that could affect analysis. These included missing values, incorrect data types, duplicate rows, inconsistent symbol formatting, negative numeric values, and impossible market values such as rows where the high price was lower than the low price. If these problems were not removed, the Spark analytics could produce incorrect results.

I overcame this by separating the cleaning process into individual functions. Numeric columns were converted using pandas so invalid values could be detected. Timestamp columns were converted into datetime formats. Duplicate records were removed, and symbols were standardised by converting them to uppercase and removing unnecessary formatting differences. Invalid rows containing negative values or impossible price relationships were removed.

Another challenge was making sure the cleaned pandas dataset worked correctly when loaded into Spark. I solved this by checking the schema after loading the CSV, verifying that columns had the correct types, and testing the Spark DataFrame before performing analytics. Breaking the problem into smaller stages made debugging easier because each stage could be tested independently.

2. Did multithreading make the API download faster or safer? Explain.

Multithreading mainly made the API download faster. Instead of downloading each cryptocurrency symbol one at a time, multiple API requests could run at the same time. This reduced the total time required to collect data because waiting time from one request could overlap with other requests.

However, multithreading also created safety problems. Multiple threads running at the same time could access shared resources, especially the log file. If two threads attempted to write to the log file simultaneously, their messages could overlap and create corrupted log output. This would make it harder to track errors or understand what happened during the download process.

To solve this problem, access to the log file needed to be controlled. A locking mechanism ensured that only one thread could write to the file at a time. This protected the log data while still allowing the API requests themselves to run concurrently.

Therefore, multithreading improved the speed of the downloader, but it required additional protection to make the process reliable.

3. What did pandas make easier?

Pandas made the cleaning and inspection of the dataset much easier. It provided simple DataFrame operations for checking the data, modifying columns, and removing invalid records.

One useful feature was quickly inspecting the dataset structure. Pandas allowed the program to print the number of rows and columns, view sample records, check data types, and identify missing values. This helped identify problems in the raw dataset before cleaning.

Pandas also simplified data transformation. Numeric columns could be converted easily, timestamps could be parsed, and duplicate rows could be removed using built-in functions. Filtering invalid data was also straightforward, for example removing rows with negative volumes or invalid price relationships.

Pandas was also useful for the small validation analysis after cleaning. A sample of records could be checked for average closing prices, candle direction counts, and symbol-level results. This provided a quick way to confirm that the cleaning process worked correctly.

However, pandas was not used for the full analytics because it is limited by local memory and does not provide distributed processing. For a larger dataset, processing everything in pandas would be less efficient.

4. What did Spark make easier?

Spark made analysing the full cleaned dataset easier. The client required analytics across all records rather than only a small sample, so Spark was used because it can process larger datasets more effectively.

Spark SQL made grouped analysis much easier. It allowed queries to be written for tasks such as calculating average close prices by symbol, counting records, calculating total trading activity, and ranking symbols. These operations would require more manual handling in a traditional programming approach.

Spark was especially useful for the advanced analytics tasks. It allowed the project to calculate volatility rankings using price ranges, activity rankings using trade counts and quote volume, and time-based analysis using trade dates and trading hours.

The final market summary was also easier to produce with Spark because multiple grouped calculations could be combined into a single dataset. This created a report containing information such as total records, average volume, total trades, average percentage change, candle counts, volatility rank, and activity rank for each symbol.

5. What would you improve if you had more time?

If I had more time, I would improve the reliability and reporting of the pipeline.

For the API downloader, I would add better handling for failed requests. For example, I would add automatic retries when an API request fails due to a temporary network problem. I would also add clearer logging of failed symbols and download progress so problems could be identified more easily.

For the cleaning stage, I would improve the data quality reporting. The current process identifies and removes invalid data, but a better version would produce a detailed report showing exactly how many rows were removed at each stage. For example, it could show how many rows were removed because of missing values, duplicates, negative values, or invalid price relationships.

For the Spark analytics, I would improve the final output by adding visualisations. The current summary provides rankings and statistics, but charts showing volatility, trading activity, and changes over time would make the results easier for a client to interpret.

I would also improve the final report generation by automating more of the output. Instead of only saving a CSV summary, the pipeline could generate a complete analytics report containing the important findings and explanations automatically.

Overall, the project showed the difference between tools designed for different purposes. Pandas was effective for cleaning and validating smaller amounts of data, while Spark was more suitable for analysing the complete dataset and producing large-scale market insights.