import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import pytz

def main():
    st.title("Stock Price Dashboard")

    # Get user input for stock symbol
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):", "AAPL")

    # Fetch stock data
    stock_data = yf.download(stock_symbol, period="1d", interval="1m")

    # Display stock data
    st.subheader("Stock Data")
    st.write(stock_data)

    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                          open=stock_data['Open'],
                                          high=stock_data['High'],
                                          low=stock_data['Low'],
                                          close=stock_data['Close'])])

    # Update layout
    fig.update_layout(title=f"{stock_symbol} Candlestick Chart",
                      xaxis_title="Date",
                      yaxis_title="Price",
                      xaxis_rangeslider_visible=False)

    # Display the chart
    st.plotly_chart(fig)