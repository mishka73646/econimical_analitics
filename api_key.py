import requests
import pandas as pd

def get_stock_data(symbol="AAPL"):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={7898787IHJY9hhisjHI}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data["Time Series (Daily)"]).T
    df.index = pd.to_datetime(df.index)
    return df.astype(float)

# Пример рекомендации
def get_stock_advice(df):
    latest_close = df["4. close"].iloc[-1]
    prev_close = df["4. close"].iloc[-2]
    if latest_close > prev_close:
        return "📈 Растет", "Покупать"
    else:
        return "📉 Падает", "Продавать"