#%% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
	os.chdir(os.path.join(os.getcwd(), 'project1yscap'))
	print(os.getcwd())
except:
	pass

#%%
# dependencies
import os
from tqdm import tqdm
import time
import datetime
import dateutil
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


#%%
# make api_keys global vars so that functions can use them
def set_api_global():
    global nyt_api
    global news_api
    global alpha_api

set_api_global()

#%% [markdown]
# # Topic & Stock_Quote

#%%
Topic = "Apple"
Stock_Quote = "AAPL"

# make the key_word global
def set_topicstockquote_global():
    global Topic
    global Stock_Quote

set_topicstockquote_global()

#%% [markdown]
# # Stock Data
#%% [markdown]
# ## 1) Define a function that returns a stock dataframe

#%%
def get_stock_data(stock_quote, stock_dates):
    stock_url = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol="+stock_quote+"&apikey="+alpha_api
    open_prices = []
    volumes = []
    dates_output = []
    
    data = requests.get(stock_url).json()
    
    for stock_date in tqdm(stock_dates):
        # There are holidays and weekends
        try:
            open_prices.append(data["Time Series (Daily)"][stock_date]["1. open"])
            volumes.append(data["Time Series (Daily)"][stock_date]["5. volume"])
            if stock_date in data["Time Series (Daily)"].keys():
                dates_output.append(stock_date)
        except:
            pass
    
    stock_df = pd.DataFrame({"Date": dates_output, 
                             stock_quote+" Open Price": pd.to_numeric(open_prices), 
                             stock_quote+" Volume": pd.to_numeric(volumes)
                            })
    return stock_df, dates_output

#%% [markdown]
# ## 2) Inputs

#%%
# set stock_dates
stock_dates = []

# decide the start date
start_date = datetime.date(2018,6,1)
number_of_days = 91

for i in range(number_of_days):
    stock_date = start_date + datetime.timedelta(i)
    stock_dates.append(stock_date.isoformat())

#%% [markdown]
# ## 3) Get the stock dataframes

#%%
stock_df, stock_dates_output = get_stock_data(Stock_Quote, stock_dates)

#%% [markdown]
# ## 4) Save to csv

#%%
stock_df.to_csv(os.path.join(".", Topic, Stock_Quote+"_"+"open price & volume.csv"))

#%% [markdown]
# # News Data
#%% [markdown]
# ## 1) Extract data from New York Times

#%%
# build a function that transfer the ISO formatted string back to datetime
def getDataTimeFromISO(iso):
    d = dateutil.parser.parse(iso)
    return d


#%%
getDataTimeFromISO(stock_dates_output[0])


#%%
# define the day_lag variable. -1 means the news yesterday may determines the price today.
day_lag = -1
# change the date
bd = getDataTimeFromISO(stock_dates_output[0]).date()+datetime.timedelta(day_lag)
# the params works in a way that does not include the end date. Therefore we need one more day from the end date
ed = getDataTimeFromISO(stock_dates_output[-1]).date()+datetime.timedelta(day_lag+1)


#%%
bd = bd.isoformat()
ed = ed.isoformat()


#%%
begin_date = bd[:4] + bd[5:7] + bd[8:10]
end_date = ed[:4] + ed[5:7] + ed[8:10]
print(begin_date, end_date)


#%%
# make bd, ed global
def set_date_global():
    global bd
    global ed
    global day_lag

set_date_global()


#%%
# prepare variables
# make sure we can loop through all the articles we get
n = 500
pages = range(n)
nyt_snippet = []
nyt_pub_date = []

# urls
nyt_base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json?"

# get data from urls
for page in tqdm(pages):
    params = {
        "api-key": nyt_api,
        "q": Topic,
        "begin_date": begin_date,
        "end_date": end_date,
        "sort": "newest",
        "fl": ["snippet","pub_date"],
        "page": page
    }
    # pause to avoid being classified as spam
    # time.sleep(0.2)
    
    try: 
        nyt_data = requests.get(nyt_base_url, params=params).json()
        # loop through 10 articles on each page
        for i in range(10):
            nyt_snippet.append(nyt_data["response"]["docs"][i]["snippet"])
            interm_date = nyt_data["response"]["docs"][i]["pub_date"]
            nyt_pub_date.append(interm_date[:4]+interm_date[5:7]+interm_date[8:10])
   
    except:
        pass

#%% [markdown]
# ## 2) Save The New York Times data to csv

#%%
nyt_news_df = pd.DataFrame({"Date": nyt_pub_date, "Snippet": nyt_snippet})
nyt_news_df.to_csv(os.path.join(".", Topic, "New York Times.csv"))

#%% [markdown]
# ## 3) Extract Data from News API - WSJ, FOX, CNN
#%% [markdown]
# ### note the pages!

#%%
def newsAPI(news_input):
    base_url = "https://newsapi.org/v2/everything"
    description = []
    pub_date = []
    pageSize = 100
    pages = range(20)
    
    if news_input == "WSJ":
        news_source = "the-wall-street-journal"
    elif news_input == "CNN":
        news_source = "cnn"
    elif news_input == "FOX":
        news_source = "fox-news"
    
    for page in tqdm(pages):
        params = {
            "q": Topic,
            "sources": news_source,
            "apiKey": news_api,
            "from": bd,
            # due to the different params functions, change the end date here to match the dates in New York Times
            "to": (getDataTimeFromISO(ed)+datetime.timedelta(-1)).date().isoformat(),
            "pageSize": pageSize,
            "page": page,
            "sortBy": "publishedAt"
        }
        # pause to avoid being classified as spam
        time.sleep(0.2)
        
        try:
            data = requests.get(base_url, params=params).json()
            # loop through each article on each page
            for i in range(pageSize):
                description.append(data["articles"][i]["description"])
                pub_date.append(data["articles"][i]["publishedAt"][:10])
        except:
            pass
    
    return description, pub_date


#%%
wsj_description, wsj_pub_date = newsAPI("WSJ")


#%%
cnn_description, cnn_pub_date = newsAPI("CNN")

#%% [markdown]
# ## 4) Save Data from News API - WSJ, CNN
#%% [markdown]
# ### Please Note: FOX has been taken out because it does not have much data points

#%%
wsj_news_df = pd.DataFrame({"Date": wsj_pub_date, "Description": wsj_description})
wsj_news_df.to_csv(os.path.join(".", Topic, "WSJ.csv"))


#%%
cnn_news_df = pd.DataFrame({"Date": cnn_pub_date, "Description": cnn_description})
cnn_news_df.to_csv(os.path.join(".", Topic, "CNN.csv"))

#%% [markdown]
# # Vader Sentiment Score
#%% [markdown]
# ## 1) Get vader scores from news data

#%%
# define a function to recycle the code
def vaderSentimentScoreCalculator(dates, sentences):
    analyzer = SentimentIntensityAnalyzer()
    vader_scores = []
    news_dates = []
    for date, sentence in zip(dates, sentences):
        try: 
            vs = analyzer.polarity_scores(sentence)
            vader_scores.append(vs['compound'])
            news_dates.append(date)
        except:
            pass
    
    return news_dates, vader_scores


#%%
nyt_dates, nyt_vaderscores = vaderSentimentScoreCalculator(nyt_pub_date, nyt_snippet)
wsj_dates, wsj_vaderscores = vaderSentimentScoreCalculator(wsj_pub_date, wsj_description)
cnn_dates, cnn_vaderscores = vaderSentimentScoreCalculator(cnn_pub_date, cnn_description)

#%% [markdown]
# ## 2) Set up dataframe for vader score

#%%
def news_to_vaderscore(news_source, pub_date, vadercores):
    
    news_dates = []
    
    for d in pub_date:
        d = getDataTimeFromISO(d).date() - datetime.timedelta(day_lag)
        d = d.isoformat()
        news_dates.append(d)
    
    news_df = pd.DataFrame({"Date": news_dates, news_source+" VS (Day_Lag="+str(day_lag)+")": vadercores})
    
    grouped_news_df = news_df.groupby("Date")
    
    adjusted_news_df = pd.DataFrame({
        "Date": grouped_news_df.count().index,
        news_source+" VS (Day_Lag="+str(day_lag)+")": grouped_news_df[news_source+" VS (Day_Lag="+str(day_lag)+")"].mean()
        })
    
    # format the vader score
    adjusted_news_df[news_source+" VS (Day_Lag="+str(day_lag)+")"] = adjusted_news_df[news_source+" VS (Day_Lag="+str(day_lag)+")"].map("{:.4f}".format)
    
    # convert vader score to numeric
    adjusted_news_df[news_source+" VS (Day_Lag="+str(day_lag)+")"] = pd.to_numeric(adjusted_news_df[news_source+" VS (Day_Lag="+str(day_lag)+")"])
    
    return adjusted_news_df


#%%
nyt_df = news_to_vaderscore("NYT", nyt_dates, nyt_vaderscores)
wsj_df = news_to_vaderscore("WSJ", wsj_dates, wsj_vaderscores)
cnn_df = news_to_vaderscore("CNN", cnn_dates, cnn_vaderscores)

#%% [markdown]
# ## 3) Save to csv

#%%
nyt_df.to_csv(os.path.join(".", Topic, "nyt_vs.csv"))
wsj_df.to_csv(os.path.join(".", Topic, "wsj_vs.csv"))
cnn_df.to_csv(os.path.join(".", Topic, "cnn_vs.csv"))

#%% [markdown]
# # Merge stock dataframes and vader score dataframes

#%%
nyt_wsj_df = nyt_df.merge(wsj_df, how="inner", on="Date")


#%%
nyt_wsj_cnn_df = nyt_wsj_df.merge(cnn_df, how="inner", on="Date")


#%%
stock_news_df = stock_df.merge(nyt_wsj_cnn_df, how="inner", on="Date")

#%% [markdown]
# # Output Dataframe

#%%
stock_news_df.to_csv(os.path.join(".", Topic, Topic+"_"+"final.csv"))

#%% [markdown]
# # Make Plots

#%%
price = stock_news_df.iloc[:,1]
volume = stock_news_df.iloc[:,2]
vs_all = stock_news_df.iloc[:,3:6]
x_axis = stock_news_df.iloc[:, 0]


#%%
stock_news_df.head()

#%% [markdown]
# ## 1) Price vs VaderScore

#%%
fig =plt.figure(figsize=(16,12))    # creating figure object
ax = fig.add_subplot(212)           # adding axes on this figure

# instantiate a second axes that shares the same x-axis
ax2 = ax.twinx()

# ploting Stock price and Vader Score on the same axis

price.plot(ax=ax, label=Stock_Quote+" Price",color="b", marker="o", markersize=10, lw=5,ls='--', alpha=1)
vs_all.plot(ax=ax2, label="Vader Score",color=["r","g","y"],markersize=10, lw=4,ls='-',alpha=0.5)


# designing labile and ticks

ax.set_ylabel(Stock_Quote +"Price",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax.set_xlabel("Date",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax2.set_ylabel("Vader Score",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax.set_xticklabels(x_axis, fontdict = {"fontsize" : 12, "fontweight": "bold"}, rotation = 75)
ax.set_xticks(np.arange(0, len(stock_news_df.iloc[:,0])))

# setting a title

ax.set_title(Stock_Quote+" Price vs Vader Score", fontdict = {"fontsize" : 28, "fontweight": "bold"})
ax.legend(numpoints = 2, frameon = True, markerscale = 1.5, edgecolor = 'blue', fontsize = '12', framealpha = 1, loc="upper left")
ax.grid()

# save and show fig
fig1 = plt.gcf()
fig1.savefig(os.path.join(".", Topic, Topic+"_"+"Price vs VaderScore"), dpi=600)
plt.show()

#%% [markdown]
# ## 2) Volume vs VaderScore

#%%
fig =plt.figure(figsize=(16,12))    # creating figure object
ax = fig.add_subplot(212)           # adding axes on this figure

# instantiate a second axes that shares the same x-axis
ax2 = ax.twinx()

# ploting Stock price and Vader Score on the same axis

volume.plot(ax=ax, label=Stock_Quote+" Volume",color="b", marker="o", markersize=10, lw=5,ls='--', alpha=1)
vs_all.plot(ax=ax2, label="Vader Score",color=["r","g","y"],markersize=10, lw=4,ls='-',alpha=0.5)


# designing labile and ticks

ax.set_ylabel(Stock_Quote +"Price",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax.set_xlabel("Date",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax2.set_ylabel("Vader Score",fontdict = {"fontsize" : 22, "fontweight": "bold"})
ax.set_xticklabels(x_axis, fontdict = {"fontsize" : 12, "fontweight": "bold"}, rotation = 75)
ax.set_xticks(np.arange(0, len(stock_news_df.iloc[:,0])))

# setting a title

ax.set_title(Stock_Quote+" Volume vs Vader Score", fontdict = {"fontsize" : 28, "fontweight": "bold"})
ax.legend(numpoints = 2, frameon = True, markerscale = 1.5, edgecolor = 'blue', fontsize = '12', framealpha = 1, loc="upper left")
ax.grid()

# save and show fig
fig2 = plt.gcf()
fig2.savefig(os.path.join(".", Topic, Topic+"_"+"Volume vs VaderScore"), dpi=600)
plt.show()


