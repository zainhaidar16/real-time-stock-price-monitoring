import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta

# Fetch stock data
def fetch_stock_data(ticker, period, interval):
    try:
        end_date = datetime.now()
        if period == '1wk':
            start_date = end_date - timedelta(days=7)
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        else:
            data = yf.download(ticker, period=period, interval=interval)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Process data
def process_data(data):
    try:
        if data is None or data.empty:
            return None
        if data.index.tzinfo is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert('US/Eastern')
        data.reset_index(inplace=True)
        data.rename(columns={'Date': 'Datetime'}, inplace=True)
        return data
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None

# Calculate metrics
def calculate_metrics(data):
    try:
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

# Add technical indicators
def add_technical_indicators(data):
    try:
        if data is None or 'Close' not in data.columns:
            return data
        close_series = pd.Series(data['Close'].values.flatten(), index=data.index)
        data['SMA_20'] = ta.trend.sma_indicator(close_series, window=20)
        data['EMA_20'] = ta.trend.ema_indicator(close_series, window=20)
        return data
    except Exception as e:
        st.error(f"Error calculating indicators: {str(e)}")
        return data

# Create chart
def create_candlestick_chart(data, ticker, indicators):
    try:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Stock Price', 'Volume')
        )

        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=data['Datetime'],
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='OHLC'
            ),
            row=1, col=1
        )

        # Add volume
        fig.add_trace(
            go.Bar(
                x=data['Datetime'],
                y=data['Volume'],
                name='Volume'
            ),
            row=2, col=1
        )

        # Add indicators
        if 'SMA 20' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=data['Datetime'],
                    y=data['SMA_20'],
                    name='SMA 20',
                    line=dict(color='orange')
                ),
                row=1, col=1
            )

        if 'EMA 20' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=data['Datetime'],
                    y=data['EMA_20'],
                    name='EMA 20',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )

        # Update layout
        fig.update_layout(
            height=800,
            xaxis_rangeslider_visible=False,
            template='plotly_dark'
        )

        return fig
    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        return None

# Set page config
st.set_page_config(layout="wide")
st.title('Real Time Stock Dashboard')

# Sidebar parameters
st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'MSFT')
time_period = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
indicators = st.sidebar.multiselect('Technical Indicators', ['SMA 20', 'EMA 20'])

# Interval mapping
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

# Main content
if st.sidebar.button('Update'):
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    if data is not None:
        data = process_data(data)
        if data is not None:
            data = add_technical_indicators(data)
            
            # Calculate metrics
            last_close, change, pct_change, high, low, volume = calculate_metrics(data)
            
            # Display metrics
            st.metric(
                label=f"{ticker} Last Price",
                value=f"${last_close:.2f}",
                delta=f"{change:+.2f} ({pct_change:+.2f}%)"
            )
            
            col1, col2, col3 = st.columns(3)
            col1.metric("High", f"${high:.2f}")
            col2.metric("Low", f"${low:.2f}")
            col3.metric("Volume", f"{volume:,}")
            
            # Create chart
            fig = create_candlestick_chart(data, ticker, indicators)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

# Watchlist
st.sidebar.header('Watchlist')
watchlist = ['AAPL', 'GOOGL', 'AMZN', 'MSFT']

for symbol in watchlist:
    try:
        watch_data = fetch_stock_data(symbol, '1d', '1m')
        if watch_data is not None:
            watch_data = process_data(watch_data)
            if watch_data is not None:
                last_price = float(watch_data['Close'].iloc[-1])
                prev_price = float(watch_data['Open'].iloc[0])
                change = last_price - prev_price
                pct_change = (change / prev_price) * 100
                
                st.sidebar.metric(
                    symbol,
                    f"${last_price:.2f}",
                    f"{change:+.2f} ({pct_change:+.2f}%)"
                )
    except Exception as e:
        st.sidebar.metric(symbol, "N/A", "Error")