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
    close_prices = df["Adj Close"].squeeze()

    # --------------------- BOLLINGER BANDS -----------------------
    indicator_bb = BollingerBands(close=close_prices, window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()  # Middle Band
    df['bb_bbh'] = indicator_bb.bollinger_hband()  # Upper Band
    df['bb_bbl'] = indicator_bb.bollinger_lband()  # Lower Band
    df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()  # High Indicator
    df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()  # Low Indicator

    # --------------------- ADI (Accumulation/Distribution Index) -----------------------
    '''
    adi_indicator = AccDistIndexIndicator(
        high=df['High'],
        low=df['Low'],
        close=df['Adj Close'],  # Use 'Adj Close' for consistency
        volume=df['Volume'],
        fillna=True  # Fill NaN values
    )
    df['ADI'] = adi_indicator.acc_dist_index()  # Add ADI column to DataFrame
    '''

    # Check the column names and ensure they are capitalized correctly
    required_columns = ['High', 'Low', 'Close', 'Volume']

    
        
    # Correctly access columns as 1D pandas Series
    high = df['High'].squeeze()  # Convert to Series if it's accidentally 2D
    low = df['Low'].squeeze()
    close = df['Close'].squeeze()
    volume = df['Volume'].squeeze()

    
    # Calculate ADI
    df['ADI'] = ta.volume.acc_dist_index(high, low, close, volume)
    
    



    

    # --------------------- COLUMN RENAMING -----------------------
    columns = [
        ("Price Data", "Date"),
        ("Price Data", "Adj Close"),
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
   
    ]

    df.columns = pd.MultiIndex.from_tuples(columns)

    # Flatten multi-level columns to a single level
    df.columns = [f"{level_0}_{level_1}" if level_0 else level_1 for level_0, level_1 in df.columns]

# --------------------- DISPLAY DATAFRAME -----------------------
st.subheader("Historical Prices")
st.write(df)

st.subheader("Data Statistics")
st.write(df.describe())

# --------------------- PRICE CHART -----------------------
st.subheader("Historical Price Chart - Adjusted Close Price")
st.line_chart(df[['Price Data_Adj Close', 'Bollinger Bands_Middle', 'Bollinger Bands_High', 'Bollinger Bands_Low']])

# --------------------- VOLUME CHART -----------------------
st.subheader("Volume")
st.bar_chart(df['Price Data_Volume'])

# --------------------- ADI CHART -----------------------
st.subheader("Accumulation/Distribution Index (ADI)")
st.line_chart(df['Indicators_ADI'])



# -------------- Scaling ADI -----------------------

# Scale ADI to fit within the price range
adi_min = df['Indicators_ADI'].min()
adi_max = df['Indicators_ADI'].max()
price_min = df['Price Data_Adj Close'].min()
price_max = df['Price Data_Adj Close'].max()

# Dynamically scale ADI to match the price range
df['Scaled_ADI'] = ((df['Indicators_ADI'] - adi_min) / (adi_max - adi_min)) * (price_max - price_min) + price_min





# --------------------- COMBINED CHART -----------------------
st.subheader("Historical Price Chart with Volume, Bollinger Bands, and ADI")

# Create a Plotly figure
fig = go.Figure()

# Add Adjusted Close Price as a line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Price Data_Adj Close'],
    mode='lines',
    name='Adj Close',
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
    yaxis='y2'
))



# Add ADI as a separate line
fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Indicators_ADI'],
    mode='lines',
    name='ADI',
    line=dict(color='purple')
))

## Add Scaled ADI as a line
#fig.add_trace(go.Scatter(
    #x=df.index,
    #y=df['Scaled_ADI'],  # Use scaled ADI for display
    #mode='lines',
    #name='Scaled ADI',
    #line=dict(color='purple', dash='dash')  # Dashed line for distinction
#))



fig.add_trace(go.Scatter(
    x=df.index,
    y=df['Scaled_ADI'],  # Use scaled ADI for visualization
    mode='lines',
    name='Scaled ADI',
    line=dict(color='purple', dash='dash'),
    customdata=df['Indicators_ADI'],  # Attach original ADI values
    hovertemplate="Date: %{x}<br>Original ADI: %{customdata}<br>Scaled ADI: %{y}<extra></extra>"
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







'''
# the following block removes unnecessary calls to the plotly chart - since i'm not sync drwaings, there's no need to have multiple plots in the app

# --- Drawing Canvas ---
st.sidebar.header("Drawing Tools")
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Transparent fill for shapes
    stroke_width=2,  # Thickness of the drawing lines
    stroke_color="red",  # Line color
    background_color="white",  # Background of the canvas
    height=400,  # Canvas height
    width=1000,  # Canvas width
    drawing_mode="freedraw",  # Drawing mode: "freedraw", "line", "rect", etc.
    key="canvas",  # Unique key for the canvas
)

# --- Handle Drawing Data ---
if canvas_result.json_data is not None:
    # Extract shapes drawn on the canvas
    st.write("Canvas JSON Data:", canvas_result.json_data)

    # Process drawn shapes or display JSON data (optional)
    for shape in canvas_result.json_data["objects"]:
        st.write(shape)

# Render the Plotly chart ONLY ONCE
#st.plotly_chart(fig, key="unique_plot")

'''















'''
# enhancing canvas functionalities to get a more personalized experience

# Enhancing canvas functionalities to get a more personalized experience

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

# Add text input for text annotations
text_to_add = st.sidebar.text_input("Add text:", value="")  # Default empty text

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
if canvas_result.json_data is not None:
    st.write("Canvas JSON Data:", canvas_result.json_data)

    # Process drawn shapes or display JSON data
    for shape in canvas_result.json_data["objects"]:
        st.write(shape)

    # Display text annotations (if any)
    if text_to_add:
        st.write(f"Text added: {text_to_add}")

'''


# making the notes and drawings permanently accessible and downloadable

import streamlit as st
from streamlit_drawable_canvas import st_canvas
import json

# --- Initialize Session State ---
if "drawing_data" not in st.session_state:
    st.session_state["drawing_data"] = []  # For drawings
if "text_annotations" not in st.session_state:
    st.session_state["text_annotations"] = []  # For text notes

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

# Add text input for text annotations
text_to_add = st.sidebar.text_input("Add text:", value="")  # Default empty text

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
if canvas_result.json_data is not None:
    # Save drawing data into session state
    st.session_state["drawing_data"] = canvas_result.json_data

    # Display raw JSON for debugging or confirmation
    st.write("Canvas JSON Data:", canvas_result.json_data)

# --- Handle Text Annotations ---
if text_to_add:
    # Save text annotation to session state
    st.session_state["text_annotations"].append(text_to_add)

    # Display saved text annotations
    st.write("Text Annotations:", st.session_state["text_annotations"])

# --- Save and Download Data ---
# Combine drawings and text into a single dictionary
saved_data = {
    "drawings": st.session_state["drawing_data"],
    "text_annotations": st.session_state["text_annotations"],
}

# Save data to a JSON file
with open("saved_annotations.json", "w") as file:
    json.dump(saved_data, file)

# Provide a download button for the JSON file
st.download_button(
    label="Download Annotations",
    data=json.dumps(saved_data, indent=4),
    file_name="annotations.json",
    mime="application/json",
)

