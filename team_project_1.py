
# coding: utf-8

# dependencies
import os
from tqdm import tqdm
import datetime
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# import APIs
from Keys.NYTAPI import nyt_api
from Keys.NewsAPI import news_api
from Keys.AlphaAPI import alpha_api

get_ipython().run_line_magic('matplotlib', 'notebook')


# # Stock Data

stock_base_url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SPX&apikey="+alpha_api

stock_data = requests.get(stock_base_url).json()

# set dates
stock_dates = []

start_date = datetime.date(2018,7,1)

for i in range(60):
    stock_date = start_date + datetime.timedelta(i)
    stock_dates.append(stock_date.isoformat())


close_prices = []
volumes = []
dates_output = []

for stock_date in tqdm(stock_dates):
    # There are holidays and weekends
    try:
        close_prices.append(stock_data["Time Series (Daily)"][stock_date]["4. close"])
        volumes.append(stock_data["Time Series (Daily)"][stock_date]["5. volume"])
        if stock_date in stock_data["Time Series (Daily)"].keys():
            dates_output.append(stock_date)
    except:
        pass


stock_df = pd.DataFrame({"Date": dates_output, "S&P Close Price": pd.to_numeric(close_prices), "S&P Volume": pd.to_numeric(volumes)})
stock_df["S&P Volume"] = stock_df["S&P Volume"].map("{:,}".format)

print(stock_df.dtypes)
stock_df


# # New York Times
print(dates_output[0])
print(dates_output[-1])

begin_date = dates_output[0][:4] + dates_output[0][5:7] + dates_output[0][8:10]
end_date = dates_output[-1][:4] + dates_output[-1][5:7] + dates_output[-1][8:10]
print(begin_date, end_date)


# prepare variables
# make sure we can loop through all the articles we get
n = 200
pages = list(range(n))
snippet = []
pub_date = []

# urls
nyt_base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json?"

# get data from urls
for page in tqdm(pages):
    params = {
        "api-key": nyt_api,
        "q": "Stock",
        "begin_date": begin_date,
        "end_date": end_date,
        "sort": "newest",
        "fl": ["snippet","pub_date"],
        "page": page
    }

    try: 
        nyt_data = requests.get(nyt_base_url, params=params).json()
        # loop through 10 articles on each page
        for i in range(10):
            snippet.append(nyt_data["response"]["docs"][i]["snippet"])
            interm_date = nyt_data["response"]["docs"][i]["pub_date"]
            pub_date.append(interm_date[:4]+interm_date[5:7]+interm_date[8:10])
        
    except:
        pass


# # Vader Sentiment Score

sentences = snippet
vader_scores = []
analyzer = SentimentIntensityAnalyzer()
for sentence in sentences:
    vs = analyzer.polarity_scores(sentence)
    vader_scores.append(vs['compound'])


# # Establish DataFrame
# convert pub_date to numeric for later data processing
news_dates = []

for d in pub_date:
    d = str(d)
    news_dates.append(d[:4] + "-" + d[4:6] + "-" + d[6:8])

news_df = pd.DataFrame({"Date": news_dates, "VaderScore": vader_scores})


news_df


grouped_news_df = news_df.groupby("Date")
adjusted_news_df = pd.DataFrame({
    "Date": grouped_news_df.count().index,
    "VaderScore": grouped_news_df["VaderScore"].mean()
})

adjusted_news_df.dtypes
stock_df.dtypes

# merge stock_df and adjusted_news_df
merged_df = stock_df.merge(adjusted_news_df, on="Date")

merged_df

