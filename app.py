import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import date
from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.volume import AccDistIndexIndicator  # Import for ADI
import ta

from streamlit_drawable_canvas import st_canvas

from ta.momentum import RSIIndicator

import requests

from ta.trend import MACD


st.title("Market Dashboard Application")
st.sidebar.header("User Input")






def get_input():
    # Normalize the symbol
    symbol = st.sidebar.text_input("Symbol", "BTC-USD").strip().upper()

    # Check if the symbol looks like a cryptocurrency
    
    if "-" in symbol and not symbol.endswith("USD"):  # If '-' exists but 'USD' is missing
        symbol = f"{symbol}USD"  # Append 'USD' for cryptos
    #################################################################

    # Dropdown for period including "Custom Dates"
    period = st.sidebar.selectbox(
        "Choose a period or custom dates:",
        ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max', 'Custom Dates'],
        index=4  # Default to '6mo'
    )

    # Default to None for custom dates
    start_date, end_date = None, None

    # If "Custom Dates" is selected, show start and end date pickers
    if period == "Custom Dates":
        start_date = st.sidebar.date_input("Start Date", date(2021, 1, 1))
        end_date = st.sidebar.date_input("End Date", date(2021, 12, 31))

    # Dropdown for interval
    interval = st.sidebar.selectbox(
        "Choose an interval:",
        ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'],
        index=8  # Default to '1d'
    )

    return symbol, period, interval, start_date, end_date


def get_data(symbol, period, interval, start_date=None, end_date=None):
    symbol = symbol.upper()

    # Handle data fetching based on the selected period or custom dates
    if period != "Custom Dates":
        # Fetch data using period and interval
        df = yf.download(tickers=symbol, period=period, interval=interval)
    else:
        # Fetch data using start and end dates
        df = yf.download(tickers=symbol, start=start_date, end=end_date, interval=interval)

    # Handle case where no data is returned
    if df.empty:
        df = pd.DataFrame(columns=['Date', 'Close', 'Open', 'Volume', 'Adj Close'])

    return df




symbol, period, interval, start_date, end_date = get_input()
df = get_data(symbol, period, interval, start_date, end_date)



if not df.empty and 'Close' in df.columns: # Replacing Adj Close with Close
    df = dropna(df)
    close_prices = df["Close"].squeeze() # Replacing Adj Close with Close

    # --------------------- BOLLINGER BANDS -----------------------
    indicator_bb = BollingerBands(close=close_prices, window=20, window_dev=2) # Replacing Adj Close with Close
    df['bb_bbm'] = indicator_bb.bollinger_mavg()  # Middle Band
    df['bb_bbh'] = indicator_bb.bollinger_hband()  # Upper Band
    df['bb_bbl'] = indicator_bb.bollinger_lband()  # Lower Band
    df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()  # High Indicator
    df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()  # Low Indicator

    # --------------------- ADI (Accumulation/Distribution Index) -----------------------
    

    # Check the column names and ensure they are capitalized correctly
    required_columns = ['High', 'Low', 'Close', 'Volume']

    
        
    # Correctly access columns as 1D pandas Series
    high = df['High'].squeeze()  # Convert to Series if it's accidentally 2D
    low = df['Low'].squeeze()
    close = df['Close'].squeeze()
    volume = df['Volume'].squeeze()

    
    # Calculate ADI
    df['ADI'] = ta.volume.acc_dist_index(high, low, close, volume)



# --------------------- RSI (Relative Strength Index) -----------------------

    # Check that the 'Close' column exists and flatten it
    if "Close" in df.columns:
        close = df["Close"].squeeze()  # Ensure it's a 1D pandas Series

        # Add RSI Period and FillNA options in the Sidebar
        rsi_period = st.sidebar.slider("RSI Period", min_value=5, max_value=50, value=14, step=1)
        fillna_option = st.sidebar.checkbox("Fill NaN values in RSI", value=False)

        # Calculate RSI using the ta library
        rsi_indicator = RSIIndicator(close=close, window=rsi_period, fillna=fillna_option)
        df["RSI"] = rsi_indicator.rsi()


# --------------------- MACD (Moving Average Convergence Divergence) -----------------------



    if "Close" in df.columns:
        close = df["Close"].squeeze()  # Ensure it's a 1D pandas Series

        # Add MACD Parameters to the Sidebar
        macd_fast = st.sidebar.slider("MACD Fast Window", min_value=5, max_value=50, value=12, step=1)
        macd_slow = st.sidebar.slider("MACD Slow Window", min_value=10, max_value=100, value=26, step=1)
        macd_signal = st.sidebar.slider("MACD Signal Window", min_value=5, max_value=30, value=9, step=1)
        fillna_option = st.sidebar.checkbox("Fill NaN values in MACD", value=False)

        # Calculate MACD using the ta library
        macd_indicator = MACD(close=close, window_slow=macd_slow, window_fast=macd_fast, window_sign=macd_signal, fillna=fillna_option)

        # Add MACD values to the DataFrame
        df["MACD_Line"] = macd_indicator.macd()
        df["MACD_Signal"] = macd_indicator.macd_signal()
        df["MACD_Histogram"] = macd_indicator.macd_diff()




    
    # --------------------- COLUMN RENAMING -----------------------
    columns = [
        #("Price Data", "Date"),
        #("Price Data", "Adj Close"),
        ("Price Data", "Close"), # Replacing Adj Close with Close
        ("Price Data", "High"),
        ("Price Data", "Low"),
        ("Price Data", "Open"),
        ("Price Data", "Volume"),
        ("Bollinger Bands", "Middle"),
        ("Bollinger Bands", "High"),
        ("Bollinger Bands", "Low"),
        ("Bollinger Bands", "High Indicator"),
        ("Bollinger Bands", "Low Indicator"),
        ("Indicators", "ADI"),  # Add ADI to columns
        ("Indicators", "RSI"),  # Add RSI to columns
        ("MACD", "MACD Line"),  # MACD line
        ("MACD", "Signal Line"),  # Signal line
        ("MACD", "Histogram"),  # MACD Histogram
   
    ]


    # Rename columns
    try:
        df.columns = pd.MultiIndex.from_tuples(columns)
        df.columns = [f"{level_0}_{level_1}" if level_0 else level_1 for level_0, level_1 in df.columns]
    except ValueError as e:
        st.error(f"Column mismatch: {e}")
        st.write("Columns After Calculation:", df.columns)


# --------------------- DISPLAY DATAFRAME -----------------------
# >>>> The following two lines are referred to the table with the data
st.subheader("Historical Prices")
st.write(df)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

st.subheader("Data Statistics")
st.write(df.describe())


# --------------------- VOLUME CHART -----------------------
st.subheader("Volume")
st.bar_chart(df['Price Data_Volume'])
#st.bar_chart(df['Volume'])

# --------------------- ADI CHART -----------------------
st.subheader("Accumulation/Distribution Index (ADI)")
st.line_chart(df['Indicators_ADI'])



# -------------- Scaling ADI -----------------------

# Scale ADI to fit within the price range
adi_min = df['Indicators_ADI'].min()
adi_max = df['Indicators_ADI'].max()
price_min = df['Price Data_Close'].min() # Replacing Adj Close with Close
price_max = df['Price Data_Close'].max() # Replacing Adj Close with Close

# Dynamically scale ADI to match the price range
df['Scaled_ADI'] = ((df['Indicators_ADI'] - adi_min) / (adi_max - adi_min)) * (price_max - price_min) + price_min


# Display RSI data in the app
st.subheader("RSI Data")
st.write(df[["Price Data_Close", "Indicators_RSI"]].tail(20))  # Display the last 20 rows of Close and RSI # Replacing Adj Close with Close

# --------------------- RSI Chart -----------------------
st.subheader("RSI Chart")
st.line_chart(df["Indicators_RSI"])


# --------------------- MACD Chart -----------------------
st.subheader("MACD Chart")
fig_macd = go.Figure()

# Add MACD Line
fig_macd.add_trace(go.Scatter(
    x=df.index,
    y=df["MACD_MACD Line"],
    mode='lines',
    name="MACD Line",
    line=dict(color='blue')
))

# Add Signal Line
fig_macd.add_trace(go.Scatter(
    x=df.index,
    y=df["MACD_Signal Line"],
    mode='lines',
    name="Signal Line",
    line=dict(color='orange')
))

# Add Histogram (Bar Chart)
fig_macd.add_trace(go.Bar(
    x=df.index,
    y=df["MACD_Histogram"],
    name="MACD Histogram",
    marker_color="green",
    opacity=0.5
))

# Update layout
fig_macd.update_layout(
    title="MACD Chart",
    xaxis_title="Date",
    yaxis_title="MACD",
    height=400,
    width=1000,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    
)

# Display the MACD chart
st.plotly_chart(fig_macd)




# --------------------- COMBINED CHART -----------------------
st.subheader("Historical Price Chart with Volume, Bollinger Bands, ADI, RSI, and MACD")

# Create a Plotly figure
fig = go.Figure()

# Add Close Price as a line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Price Data_Close'],  # Replacing Adj Close with Close
    mode='lines',
    name='Close',  # Replacing Adj Close with Close
    line=dict(color='blue')
))

# Add Bollinger Bands (Middle, High, Low) as lines
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Bollinger Bands_Middle'],
    mode='lines',
    name='Bollinger Middle',
    line=dict(color='orange')
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Bollinger Bands_High'],
    mode='lines',
    name='Bollinger High',
    line=dict(color='green')
))
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Bollinger Bands_Low'],
    mode='lines',
    name='Bollinger Low',
    line=dict(color='red')
))

# Add Volume as a bar chart (secondary Y-axis)
fig.add_trace(go.Bar(
    x=df.index,
    y=df['Price Data_Volume'],
    name='Volume',
    marker_color='gray',
    opacity=0.6,
    yaxis='y2'  # Link to secondary Y-axis for volume
))


##############################
# Add ADI as a separate line (on a secondary y-axis)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Indicators_ADI'],
    mode='lines',
    name='ADI',
    line=dict(color='purple'),
    yaxis='y5'  # Assigning ADI to a new y-axis
))

#################################





# Add RSI as a line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Indicators_RSI'],
    mode='lines',
    name='RSI',
    line=dict(color='brown'),
    yaxis="y3"  # Link to tertiary Y-axis for RSI
))

# Add RSI levels as horizontal lines on the RSI Y-axis
fig.add_hline(
    y=70,
    line_dash="dot",
    line_color="red",
    annotation_text="Overbought (70)",
    annotation_position="top right",
    yref="y3"  # Reference RSI axis
)
fig.add_hline(
    y=30,
    line_dash="dot",
    line_color="green",
    annotation_text="Oversold (30)",
    annotation_position="bottom right",
    yref="y3"  # Reference RSI axis
)

# Add MACD Line to Combined Chart
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["MACD_MACD Line"],
    mode='lines',
    name="MACD Line",
    line=dict(color='blue', dash="dot"),
    yaxis="y4"  # Use a fourth axis for MACD
))

# Add Signal Line to Combined Chart
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["MACD_Signal Line"],
    mode='lines',
    name="Signal Line",
    line=dict(color='orange', dash="dash"),
    yaxis="y4"  # Use a fourth axis for MACD
))

# Add MACD Histogram to Combined Chart (as a filled area)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df["MACD_Histogram"],
    mode='lines',
    fill='tozeroy',  # Fill area to zero
    name="MACD Histogram",
    line=dict(color="green"),
    opacity=0.3,
    yaxis="y4"  # Use a fourth axis for MACD
))


#####################################################################


fig.update_layout(
    title= 'Chart', #'Close Price, Bollinger Bands, Volume, ADI, RSI, and MACD',  # Updated title to reflect all included indicators
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
    yaxis3=dict(
        title='RSI',
        range=[0, 100],  # RSI ranges from 0 to 100
        overlaying='y',  # Overlay RSI axis on the same plot
        side='right',    # Place RSI axis on the right side
        anchor="free",   # Free anchor to avoid conflicts
        position=0.85    # Slightly offset RSI axis to avoid overlap
    ),
    yaxis4=dict(
        title="MACD",       # Title for MACD axis
        overlaying="y",     # Overlay it on the same plot
        side="right",       # Place it on the right
        anchor="free",      # Free anchor for independent positioning
        position=0.92       # Offset it to the right within the valid range
    ),

    #################################
    
    # Define this new y-axis in the layout:

    yaxis5=dict(
        title='ADI',
        overlaying='y',
        anchor='free',
        side='right',
        position=0.98  # Adjust to avoid overlap
    ),

    ###########################
    
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    
    height=700,
    width=1000
)




# Display the combined chart
st.plotly_chart(fig)


# -------------------------- Want to add the news container --------------------



import feedparser

st.subheader(f"Latest News for {symbol.upper()}")

try:
    if symbol.endswith("-USD"):  # Cryptocurrency news from Google News RSS feed
        crypto_name = symbol.split('-')[0]  # e.g., BTC, ETH
        rss_url = f"https://news.google.com/rss/search?q={crypto_name}+crypto&hl=en-US&gl=US&ceid=US:en"

        news_feed = feedparser.parse(rss_url)

        if news_feed.entries:
            # Display the top 5 news articles
            for entry in news_feed.entries[:5]:
                st.markdown(f"### [{entry.title}]({entry.link})")
                st.write(f"Published on: {entry.published}")
                st.write("---")
        else:
            st.write("No news articles found for this cryptocurrency.")



    else:
        # Fetch stock news using yfinance
        ticker = yf.Ticker(symbol)
        stock_news = ticker.news
        if stock_news and len(stock_news) > 0:
            # Display the top 5 news articles
            for article in stock_news[:5]:
                st.markdown(f"### [{article['title']}]({article['link']})")
                st.write(f"Published by: {article['publisher']}")
                st.write(f"Published on: {pd.to_datetime(article['providerPublishTime'], unit='s')}")
                st.write("---")
        else:
            st.write("No news articles found for this stock.")
except Exception as e:
    st.error(f"An error occurred while fetching news: {e}")



# -------------------------- Canvas -----------------------------------


# making it possible to manage notes and add them to drawings if i want to

import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw, ImageFont
import io
import json

# --- Initialize Session State ---
if "drawing_data" not in st.session_state:
    st.session_state["drawing_data"] = []  # For drawings
if "text_annotations" not in st.session_state:
    st.session_state["text_annotations"] = []  # For sidebar notes
if "canvas_annotations" not in st.session_state:
    st.session_state["canvas_annotations"] = []  # For text added directly to the canvas

# --- Sidebar Drawing Options ---
st.sidebar.header("Drawing Tools")

# Choose drawing mode
drawing_mode = st.sidebar.selectbox(
    "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
)

# Choose line color
stroke_color = st.sidebar.color_picker("Line color:", "#FF0000")  # Default red

# Choose fill color for shapes (no transparency)
fill_color = st.sidebar.color_picker("Fill color:", "#FFA500")  # Default orange

# Choose stroke width
stroke_width = st.sidebar.slider("Stroke width:", 1, 25, 2)

# --- Add Sidebar Annotations ---
st.sidebar.subheader("Add Sidebar Notes (Not Included in Image)")
text_to_add = st.sidebar.text_input("Add sidebar note:")
if st.sidebar.button("Add Note") and text_to_add.strip():
    st.session_state["text_annotations"].append(text_to_add)

# Display and manage sidebar notes
st.sidebar.subheader("Manage Sidebar Notes")
indices_to_delete = []
for i, note in enumerate(st.session_state["text_annotations"]):
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.write(note)
    with col2:
        if st.button("❌", key=f"delete_note_{i}"):
            indices_to_delete.append(i)

# Remove notes marked for deletion
if indices_to_delete:
    st.session_state["text_annotations"] = [
        note for idx, note in enumerate(st.session_state["text_annotations"])
        if idx not in indices_to_delete
    ]

# --- Add Canvas Annotations ---
st.sidebar.subheader("Add Text to Canvas (Included in Image)")
canvas_text = st.sidebar.text_input("Text to add to canvas:")
x_pos = st.sidebar.number_input("X Position:", min_value=0, max_value=1000, value=50)
y_pos = st.sidebar.number_input("Y Position:", min_value=0, max_value=400, value=50)

if st.sidebar.button("Add Canvas Annotation") and canvas_text.strip():
    st.session_state["canvas_annotations"].append(
        {"text": canvas_text, "x": x_pos, "y": y_pos}
    )

# --- Drawing Canvas ---
canvas_result = st_canvas(
    fill_color=fill_color,  # Shape fill color
    stroke_width=stroke_width,  # Thickness of the drawing lines
    stroke_color=stroke_color,  # Line color
    background_color="#FFFFFF",  # Background of the canvas (white)
    height=400,  # Canvas height
    width=1000,  # Canvas width
    drawing_mode=drawing_mode,  # Drawing mode: "freedraw", "line", "rect", etc.
    key="canvas",  # Unique key for the canvas
)

# --- Handle Drawing Data ---
final_image = None
if canvas_result.image_data is not None:
    # Convert canvas data to an image
    image = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")

    # Add canvas text annotations
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()  # Use default font
    for annotation in st.session_state["canvas_annotations"]:
        draw.text((annotation["x"], annotation["y"]), annotation["text"], fill="black", font=font)

    # Save the final image for download
    final_image = image
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Display the updated image
    st.image(image, caption="Canvas Drawing with Annotations", use_container_width=True)

    # Provide download button for the image
    st.download_button(
        label="Download Final Image with Canvas Annotations",
        data=img_buffer,
        file_name="drawing_with_canvas_annotations.png",
        mime="image/png",
    )

# --- Save and Download Sidebar Notes ---
if st.session_state["text_annotations"]:
    saved_data = {"text_annotations": st.session_state["text_annotations"]}
    st.download_button(
        label="Download Sidebar Notes (Text Only)",
        data=json.dumps(saved_data, indent=4),
        file_name="sidebar_notes.json",
        mime="application/json",
    )

