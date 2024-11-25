import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import pytz
import ta

def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data

def process_data(data):
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

def calculate_metrics(data):
    """Calculate basic stock metrics with proper type conversion."""
    try:
        # Convert Series values to float
        last_close = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[0])
        change = last_close - prev_close
        pct_change = (change / prev_close) * 100
        high = float(data['High'].max())
        low = float(data['Low'].min())
        volume = int(data['Volume'].sum())
        
        return last_close, change, pct_change, high, low, volume
        
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0

def add_technical_indicators(data):
    """Add technical analysis indicators."""
    try:
        # Handle multi-dimensional data and ensure 1D series
        if 'Close' not in data.columns:
            raise ValueError("Missing 'Close' column in data")
            
        # Convert Close prices to 1D series
        close_series = data['Close'].values.flatten() if isinstance(data['Close'].values, np.ndarray) else data['Close']
        close_series = pd.Series(close_series, index=data.index)
        
        # Calculate technical indicators
        data['SMA_20'] = ta.trend.sma_indicator(
            close=close_series,
            window=20,
            fillna=True
        )
        
        data['EMA_20'] = ta.trend.ema_indicator(
            close=close_series,
            window=20,
            fillna=True
        )
        
        data['RSI'] = ta.momentum.rsi(
            close=close_series,
            window=14,
            fillna=True
        )
        
        # MACD
        macd = ta.trend.MACD(
            close=close_series,
            window_slow=26,
            window_fast=12,
            window_sign=9
        )
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(
            close=close_series,
            window=20,
            window_dev=2
        )
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_middle'] = bb.bollinger_mavg()
        data['BB_lower'] = bb.bollinger_lband()
        
        return data
        
    except Exception as e:
        st.error(f"Error calculating indicators: {str(e)}")
        return data


# Streamlit setup
st.set_page_config(layout="wide")
st.title('Real Time Stock Dashboard')

st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'ADBE')
time_period = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Technical Indicators', ['SMA 20', 'EMA 20'])

interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

if st.sidebar.button('Update'):
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    data = process_data(data)
    data = add_technical_indicators(data)
    
    last_close, change, pct_change, high, low, volume = calculate_metrics(data)
    
    st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{high:.2f} USD")
    col2.metric("Low", f"{low:.2f} USD")
    col3.metric("Volume", f"{volume:,}")
    
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close')
    
    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))
    
    fig.update_layout(title=f'{ticker} {time_period.upper()} Chart',
                      xaxis_title='Time',
                      yaxis_title='Price (USD)',
                      height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader('Historical Data')
    st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])
    
    st.subheader('Technical Indicators')
    st.dataframe(data[['Datetime', 'SMA_20', 'EMA_20']])

st.sidebar.header('Real-Time Stock Prices')
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT']
for symbol in stock_symbols:
    try:
        real_time_data = fetch_stock_data(symbol, '1d', '1m')
        if not real_time_data.empty:
            real_time_data = process_data(real_time_data)
            
            # Convert Series values to float
            last_price = float(real_time_data['Close'].iloc[-1])
            open_price = float(real_time_data['Open'].iloc[0])
            change = last_price - open_price
            pct_change = (change / open_price) * 100
            
            # Pass formatted values to metric
            st.sidebar.metric(
                f"{symbol}",
                f"{last_price:.2f} USD",
                f"{change:+.2f} ({pct_change:+.2f}%)"
            )
    except Exception as e:
        st.sidebar.warning(f"Could not load data for {symbol}: {str(e)}")

