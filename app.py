import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import date
from patterns import patterns
from ta.utils import dropna
from ta.volatility import BollingerBands

st.title("Market Dashboard Application")
st.sidebar.header("User Input")

def get_input():
    symbol = st.sidebar.text_input("Symbol", "BTC-USD")
    start_date = st.sidebar.date_input("Start Date", date(2021, 1, 1))
    end_date = st.sidebar.date_input("End Date", date(2021, 12, 31))
    return symbol, start_date, end_date

def get_data(symbol, start_date, end_date):
    symbol = symbol.upper()
    if symbol:
        df = yf.download(symbol, start=start_date, end=end_date)
    else:
        df = pd.DataFrame(columns=['Date', 'Close', 'Open', 'Volume', 'Adj Close'])
    return df

symbol, start_date, end_date = get_input()
df = get_data(symbol, start_date, end_date)

if not df.empty and 'Adj Close' in df.columns:
    df = dropna(df)
    close_prices = df["Adj Close"].squeeze() # added this line

    indicator_bb = BollingerBands(close=close_prices, window=20, window_dev=2)
    
    # Use .squeeze() to ensure the output is 1-dimensional
    #df['bb_mavg'] = pd.Series(indicator_bb.bollinger_mavg().squeeze(), index=df.index)
    #df['bb_high'] = pd.Series(indicator_bb.bollinger_hband().squeeze(), index=df.index)
    #df['bb_low'] = pd.Series(indicator_bb.bollinger_lband().squeeze(), index=df.index)

    # Convert to 1-dimensional array 
    #df['bb_mavg'] = pd.Series(indicator_bb.bollinger_mavg().values.ravel(), index=df.index) 
    #df['bb_high'] = pd.Series(indicator_bb.bollinger_hband().values.ravel(), index=df.index) 
    #df['bb_low'] = pd.Series(indicator_bb.bollinger_lband().values.ravel(), index=df.index)
    # Add Bollinger Bands features to the original DataFrame (df)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbh'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()

    # Add Bollinger Band high indicator
    df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()

    # Add Bollinger Band low indicator
    df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()

    # Rename the column at position 5 (index 4)
df.rename(columns={df.columns[6]: "Bollinger Bands"}, inplace=True)








st.subheader("Historical Prices")
st.write(df)

st.subheader("Data Statistics")
st.write(df.describe())

st.subheader("Historical Price Chart - Adjusted Close Price")
st.line_chart(df['Adj Close'])

st.subheader("Volume")
st.bar_chart(df['Volume'])
