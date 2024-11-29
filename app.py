import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import date
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.volume import AccDistIndexIndicator  # Import for ADI

st.title("Market Dashboard Application")
st.sidebar.header("User Input")

# --------------------- USER INPUT -----------------------
def get_input():
    symbol = st.sidebar.text_input("Symbol", "BTC-USD")
    start_date = st.sidebar.date_input("Start Date", date(2021, 1, 1))
    end_date = st.sidebar.date_input("End Date", date(2021, 12, 31))
    return symbol, start_date, end_date

# --------------------- GET DATA -----------------------
def get_data(symbol, start_date, end_date):
    symbol = symbol.upper()
    if symbol:
        df = yf.download(symbol, start=start_date, end=end_date)
    else:
        df = pd.DataFrame(columns=['Date', 'Close', 'Open', 'Volume', 'Adj Close'])
    return df

symbol, start_date, end_date = get_input()
df = get_data(symbol, start_date, end_date)

# --------------------- INDICATOR CALCULATIONS -----------------------
if not df.empty and 'Adj Close' in df.columns:
    df = dropna(df)  # Clean up NaN values
    close_prices = df["Adj Close"].squeeze()

    # --------------------- BOLLINGER BANDS -----------------------
    indicator_bb = BollingerBands(close=close_prices, window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()  # Middle Band
    df['bb_bbh'] = indicator_bb.bollinger_hband()  # Upper Band
    df['bb_bbl'] = indicator_bb.bollinger_lband()  # Lower Band
    df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()  # High Indicator
    df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()  # Low Indicator

    # --------------------- ADI (Accumulation/Distribution Index) -----------------------
    adi_indicator = AccDistIndexIndicator(
        high=df['High'],
        low=df['Low'],
        close=df['Adj Close'],  # Use 'Adj Close' for consistency
        volume=df['Volume'],
        fillna=True
    )
    df['ADI'] = adi_indicator.acc_dist_index()  # Add ADI column

    # --------------------- FLATTEN COLUMNS -----------------------
    df.columns = [
        col.replace(' ', '_').lower() for col in df.columns
    ]  # Normalize all column names to lowercase, flattened format

# --------------------- DISPLAY DATAFRAME -----------------------
st.subheader("Historical Prices")
st.write(df)

st.subheader("Data Statistics")
st.write(df.describe())

# --------------------- PRICE CHART -----------------------
st.subheader("Historical Price Chart - Adjusted Close Price and Bollinger Bands")
st.line_chart(df[['adj_close', 'bb_bbm', 'bb_bbh', 'bb_bbl']])

# --------------------- VOLUME CHART -----------------------
st.subheader("Volume")
st.bar_chart(df['volume'])

# --------------------- ADI CHART -----------------------
st.subheader("Accumulation/Distribution Index (ADI)")
st.line_chart(df['adi'])

# --------------------- COMBINED CHART -----------------------
st.subheader("Historical Price Chart with Volume, Bollinger Bands, and ADI")

# Create a Plotly figure
fig = go.Figure()

# Add Adjusted Close Price as a line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['adj_close'],
    mode='lines',
    name='Adj Close',
    line=dict(color='blue')
))

# Add Bollinger Bands (Middle, High, Low) as lines
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['bb_bbm'],
    mode='lines',
    name='Bollinger Middle',
    line=dict(color='orange')
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['bb_bbh'],
    mode='lines',
    name='Bollinger High',
    line=dict(color='green')
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['bb_bbl'],
    mode='lines',
    name='Bollinger Low',
    line=dict(color='red')
))

# Add Volume as a bar chart (secondary Y-axis)
fig.add_trace(go.Bar(
    x=df.index,
    y=df['volume'],
    name='Volume',
    marker_color='gray',
    opacity=0.6,
    yaxis='y2'
))

# Add ADI as a separate line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['adi'],
    mode='lines',
    name='ADI',
    line=dict(color='purple')
))

# Update layout for dual-axis visualization
fig.update_layout(
    title='Adjusted Close Price, Bollinger Bands, Volume, and ADI',
    xaxis=dict(title='Date'),
    yaxis=dict(
        title='Price',
        showgrid=True,
        zeroline=True
    ),
    yaxis2=dict(
        title='Volume',
        overlaying='y',  # Overlay volume axis on the same plot
        side='right'     # Display volume axis on the right side
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=600,
    width=1000
)

# Display the combined chart
st.plotly_chart(fig)
