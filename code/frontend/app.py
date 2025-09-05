
import streamlit as st
import os
import pandas as pd
import numpy as np
import requests
from scipy.stats import gmean
import matplotlib.pyplot as plt
import altair as alt
from datetime import datetime, timedelta, date
import yfinance as yf


st.set_page_config(layout="wide")
st.header("Stock Market Quotes")

# MAG7 INTRADAY CHANGES in Prozent 

# 60 Sekunden Intervall Refresh
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now()
else:
    now = datetime.now()
    if (now - st.session_state["last_refresh"]).total_seconds() > 60:
        st.session_state["last_refresh"] = now
        st.rerun()


st.markdown("### MAG7 Daily Performance:")

mag7_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

# Intraday Delta berechnen 
def get_today_change(ticker):
    today = datetime.now().date()
    buffer_start = today - timedelta(days=7)
    data = yf.download(ticker, start=buffer_start, end=today + timedelta(days=1), progress=False)
    data = data.dropna()
    
    if data.shape[0] < 2:
        return None
    
    latest = data["Close"].iloc[-1]
    prev = data["Close"].iloc[-2]
    change = (latest - prev) / prev * 100
    
    return float(round(change, 2))


# Horizontale Bars inklusive einer Spalte pro || seperator
cols = st.columns(len(mag7_tickers)* 2 -1)
for i, ticker in enumerate(mag7_tickers):
    col_index = i * 2  # Even indices for tickers
    change = get_today_change(ticker)
    
    if change is not None:
        color = "green" if change >= 0 else "red"
        cols[col_index].markdown(
            f"<div style='color:{color}; font-size:18px; text-align:center'>{ticker}: {change:+.2f}%</div>",
            unsafe_allow_html=True
        )
    else:
        cols[col_index].markdown(f"{ticker}: n/a")

    # Seperator nach jedem Ticker
    if i < len(mag7_tickers) - 1:
        cols[col_index + 1].markdown("<div style='font-size:18px; text-align:center'>|</div>", unsafe_allow_html=True)

# "Letzes Update" Part
st.caption(f"Last updated at {datetime.now().strftime('%H:%M:%S')}")
st.divider()



# Bild
st.image("static/stock_market.jpg", use_container_width=True)
st.divider()

# Eingabefeld für Ticker
today = date.today()
default_start = today - timedelta(days=365)
start_date = st.date_input("Start Date", value=default_start)
end_date = st.date_input("End Date", value=today)
ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT, TSLA)", value="AAPL").upper()


BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000")
# Daten vom Flask-Backend holen
@st.cache_data
def fetch_data(ticker, start_date, end_date):
    try:
        url = f"{BACKEND_URL}/api/stock?ticker={ticker}&start={start_date}&end={end_date}"
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return pd.DataFrame(res.json())
    except:
        return pd.DataFrame()

data = fetch_data(ticker, start_date, end_date)

if data.empty:
    st.error("No data found or API not reachable.")
    st.stop()
else:
    st.success(f"Loaded data for {ticker}")

# Spalten anzeigen (Debug)
# st.write("Spalten:", data.columns.tolist())

# Datumsspalte sicher erkennen
possible_time_cols = [col for col in data.columns if "date" in col.lower() or "time" in col.lower() or col.lower() == "index"]
if possible_time_cols:
    time_col = possible_time_cols[0]
    data["Date"] = pd.to_datetime(data[time_col])
else:
    st.error("Keine gültige Zeitspalte gefunden.")
    st.stop()

# Daten vorbereiten
closing_prices = data["Close"].squeeze()
opening_prices = data["Open"].squeeze()
highs = data["High"].squeeze()
lows = data["Low"].squeeze()
volumes = data["Volume"].squeeze().dropna()
daily_returns = closing_prices.pct_change().dropna()

annual_volatility = daily_returns.std() * (252**0.5)
annual_volatility_pct = round(annual_volatility * 100, 2)
daily_volatility_pct = round(annual_volatility_pct / (252**0.5), 2)

# DataFrame für Anzeige und Charts
df = pd.DataFrame({
    "Day": data["Date"],
    "Opening Price": opening_prices,
    "Closing Prices": closing_prices,
    "Daily Low": lows,
    "Daily High": highs,
    "Volume": volumes
})

# Metriken (Daily, Annual Geo Return, Mean Daily Trading Volume)
geo_mean = round((gmean(1 + daily_returns) - 1) * 100, 2)
mean_vol = round(volumes.mean())
annualized_mean_return = annualized_return = (gmean(1 + daily_returns) ** 252 - 1) * 100


# Tabelle
st.subheader(f"Daily ${ticker} Data and Investment Calculator")
col1, col2 = st.columns([3, 1])
with col1:
    st.dataframe(df, height=400, width=1700)

# Calculator
with col2:
    with st.expander("💰 Investment Projection Calculator"):
        initial = st.number_input("Initial investment amount ($)", min_value=0.0, value=1000.0, step=100.0)
        annual_return_pct = st.number_input("Projected annual return (%)", min_value=0.0, value=7.0, step=0.1)
        years = st.number_input("Investment timeframe (years)", min_value=1, value=10, step=1)
        future_value = initial * ((1 + (annual_return_pct / 100)) ** years)
        st.write(f"**Projected Final Value**: ${future_value:,.2f}\n\n*Estimating reinvestment")

st.divider()
st.subheader("Charting and Indicators")

# Chart vorbereiten
df["Color"] = np.where(df["Closing Prices"] > df["Opening Price"], "green", "red")
min_date, max_date = df["Day"].min(), df["Day"].max()

base = alt.Chart(df).encode(x=alt.X("Day:T", axis=alt.Axis(title="Date"), scale=alt.Scale(domain=[min_date, max_date])))
wick = base.mark_rule().encode(y=alt.Y("Daily Low:Q"), y2="Daily High:Q")
candle = base.mark_bar().encode(y=alt.Y("Opening Price:Q", title="Price"), y2="Closing Prices:Q", color=alt.Color("Color:N", scale=None))
chart = (wick + candle).properties(width=1600, height=500, title=f"${ticker} Candlestick Chart (D)").interactive(bind_y=True)






#Info + Indikatoren
col3, col4, col5 = st.columns([1, 5, 1])
with col3:
    with st.expander(f"Additional Information on ${ticker}"):
        st.write(
            f"Daily average return: {geo_mean}%\n\n"
            f"Annualized average return: {annualized_mean_return:.2f}% \n\n"
            f"Daily average trading volume: ${mean_vol:,}\n\n"
            f"Annualized Volatility: {annual_volatility_pct}%\n\n"
            f"Daily Volatility: {daily_volatility_pct}%"
            
        )

with col5:
    indicators = st.multiselect(
        "Select indicators:",
        options=["9 EMA", "10 MA", "RSI", "Stochastic Oscillator", "MACD", "20 EMA", "20 MA"],
        default=[]
    )

with col4:
    subcharts = []


    if "MACD" in indicators:
        # Calculate EMAs
        df["EMA_12"] = df["Closing Prices"].ewm(span=12, adjust=False).mean()
        df["EMA_26"] = df["Closing Prices"].ewm(span=26, adjust=False).mean()

        # MACD and Signal Line
        df["MACD"] = df["EMA_12"] - df["EMA_26"]
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # Line Chart for MACD and Signal
        macd_chart = alt.Chart(df).mark_line(color="blue").encode(
            x="Day:T", y=alt.Y("MACD:Q", title="MACD")
        )

        signal_chart = alt.Chart(df).mark_line(color="red").encode(
            x="Day:T", y="MACD_Signal:Q"
        )

        # Combine charts
        macd_combined = (macd_chart + signal_chart).properties(height=150)

        # Add to subcharts stack
        subcharts.append(macd_combined)


    if "9 EMA" in indicators:
        df["9 EMA"] = df["Closing Prices"].ewm(span=9).mean()
        chart += alt.Chart(df).mark_line(color="blue").encode(x="Day:T", y="9 EMA:Q")

    if "20 EMA" in indicators:
        df["20 EMA"] = df["Closing Prices"].ewm(span=20).mean()
        chart += alt.Chart(df).mark_line(color="darkturquoise").encode(x="Day:T", y="20 EMA:Q")

    if "10 MA" in indicators:
        df["10 MA"] = df["Closing Prices"].rolling(window=10).mean()
        chart += alt.Chart(df).mark_line(color="orange").encode(x="Day:T", y="10 MA:Q")

    if "20 MA" in indicators:
        df["20 MA"] = df["Closing Prices"].rolling(window=20).mean()
        chart += alt.Chart(df).mark_line(color="azure").encode(x="Day:T", y="20 MA:Q")

    if "RSI" in indicators:
        delta = df["Closing Prices"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        roll_up = pd.Series(gain, index=df.index).rolling(window=14).mean()
        roll_down = pd.Series(loss, index=df.index).rolling(window=14).mean()
        rs = roll_up / roll_down
        df["RSI"] = 100 - (100 / (1 + rs))
        rsi_chart = alt.Chart(df).mark_line(color="darkgreen").encode(
            x="Day:T", y=alt.Y("RSI:Q", title="RSI", scale=alt.Scale(domain=[0, 100]))
        ).properties(height=150)
        rsi_chart += alt.Chart(pd.DataFrame({"y": [70, 30]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
        subcharts.append(rsi_chart)

    if "Stochastic Oscillator" in indicators:
        window = 14
        df["Lowest_Low"] = df["Daily Low"].rolling(window=window).min()
        df["Highest_High"] = df["Daily High"].rolling(window=window).max()
        df["%K"] = 100 * ((df["Closing Prices"] - df["Lowest_Low"]) / (df["Highest_High"] - df["Lowest_Low"]))
        stochastic_chart = alt.Chart(df).mark_line(color="purple").encode(
            x="Day:T", y=alt.Y("%K:Q", title="Stochastic Oscillator", scale=alt.Scale(domain=[0, 100]))
        ).properties(height=150)
        stochastic_chart += alt.Chart(pd.DataFrame({"y": [80, 20]})).mark_rule(strokeDash=[4, 4], color="gray").encode(y="y:Q")
        subcharts.append(stochastic_chart)

    full_chart = alt.vconcat(chart, *subcharts).resolve_scale(x='shared')
    st.altair_chart(full_chart, use_container_width=False)
