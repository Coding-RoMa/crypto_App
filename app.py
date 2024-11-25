

import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import date  # Import the date class
from patterns import patterns



from ta.utils import dropna
from ta.volatility import BollingerBands



st.title("Market Dashboard Application")
st.sidebar.header("User Input")

def get_input():
    # Use date objects for default values
    symbol = st.sidebar.text_input("Symbol", "BTC-USD")
    start_date = st.sidebar.date_input("Start Date", date(2021, 1, 1)) 
    # in the beginning i used the code shown in the course for dates, it was like this:
    # "Start Date", "2021-01-01"
    # But Streamlit doesn't accept this format, so i had to modify the code
    end_date = st.sidebar.date_input("End Date", date(2021, 12, 31))

    return symbol, start_date, end_date

def get_data(symbol, start_date, end_date):
    symbol = symbol.upper()
    if (symbol):
        df = yf.download(symbol, start=start_date, end=end_date)
    else:
        df = pd.DataFrame(columns=['Date', 'Close', 'Open', 'Volume', 'Adj Close'])

    return df


#def get_patterns():
    ## Allow users to select one or more patterns from the list
    #selected_patterns = st.sidebar.multiselect("Select Patterns", options=list(patterns.values())) # updating the current code - options=patterns)
    #return selected_patterns




# Unpack user inputs
symbol, start_date, end_date = get_input()
df = get_data(symbol, start_date, end_date)




## Get user-selected patterns
#selected_patterns = get_patterns()



if not df.empty and 'Adj Close' in df.columns:
    # Drop rows with missing values
    df = dropna(df)

    # Initialize Bollinger Bands Indicator
    indicator_bb = BollingerBands(close=df["Adj Close"], window=20, window_dev=2)

    # Add Bollinger Bands features to the DataFrame
    df['bb_mavg'] = indicator_bb.bollinger_mavg()  # Middle Band
    df['bb_high'] = indicator_bb.bollinger_hband()  # High Band
    df['bb_low'] = indicator_bb.bollinger_lband()  # Low Band



st.subheader("Historical Prices")
st.write(df)

st.subheader("Data Statistics")
st.write(df.describe())

st.subheader("Historical Price Chart - Adjusted Close Price")
st.line_chart(df['Adj Close'])

st.subheader("Volume")
st.bar_chart(df['Volume'])


#from where i got the patterns: 
# https://github.com/TA-Lib/ta-lib-python/blob/master/docs/func_groups/pattern_recognition.md#cdl2crows---two-crows

#here's another useful link: 
# https://github.com/TA-Lib/ta-lib/blob/main/docs/functions.md


## Reverse the dictionary to map readable names back to codes
#name_to_code = {v: k for k, v in patterns.items()}

## Convert selected patterns back to their corresponding codes
#selected_codes = [name_to_code[name] for name in selected_patterns]
#st.write("Corresponding Pattern Codes:")
#st.write(selected_codes)


# Display selected patterns in the main app area
#st.write("You selected the following patterns:")
#st.write(selected_patterns)



