import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import plotly.graph_objects as go
import requests

# ================= AI (OPENROUTER) =================
def ask_ai_openrouter(prompt):
    API_KEY = st.secrets["OPENROUTER_API_KEY"]  # 🔑 secure key

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120,  # ✅ cost + speed control
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        # ✅ Handle API errors cleanly
        if "error" in response_json:
            return f"⚠️ AI error: {response_json['error']['message']}"

        return response_json["choices"][0]["message"]["content"]

    except Exception as e:
        return "⚠️ AI temporarily unavailable"


st.set_page_config(layout="wide")

# =========================
# BRANDING
# =========================
st.markdown("# 🚀 InspireTech Trading Analysis (India)")
st.markdown("### Smart AI-powered stock insights, breakout detection & comparison")

# =========================
# STOCK FORMAT
# =========================
def format_stock(symbol):
    symbol = symbol.upper().strip()
    mapping = {
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFC": "HDFCBANK.NS",
        "ICICI": "ICICIBANK.NS",
        "SBI": "SBIN.NS",
        "AXISBANK": "AXISBANK.NS",
    }
    if symbol in mapping:
        return mapping[symbol]
    if not symbol.endswith(".NS"):
        return symbol + ".NS"
    return symbol


# =========================
# INPUT
# =========================
colA, colB = st.columns([3, 2])

with colA:
    user_stock = st.text_input("🔎 Search Stock", "AXISBANK")

with colB:
    timeframe = st.selectbox("⏱ Timeframe", ["1D", "5D", "1M", "3M", "6M", "1Y", "MAX"])

stock_input = format_stock(user_stock)

st.markdown(f"### 📌 Currently Viewing: **{user_stock.upper()}** ({stock_input})")

# =========================
# TIMEFRAME
# =========================
timeframe_map = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "MAX": ("max", "1d"),
}

period, interval = timeframe_map[timeframe]

# =========================
# DATA
# =========================
data = yf.download(stock_input, period=period, interval=interval)

if data.empty:
    st.error("❌ No data found")
    st.stop()

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

data = data[["Open", "High", "Low", "Close", "Volume"]]
data["Close"] = pd.Series(data["Close"].values.flatten(), index=data.index)
data = data.dropna()

# =========================
# INDICATORS
# =========================
data["RSI"] = RSIIndicator(data["Close"]).rsi()
macd = MACD(data["Close"])
data["MACD"] = macd.macd()
data["Signal"] = macd.macd_signal()
data["MA20"] = data["Close"].rolling(20).mean()

latest = data.iloc[-1]

# =========================
# SUPPORT / RESISTANCE
# =========================
support = data["Low"].rolling(20).min().iloc[-1]
resistance = data["High"].rolling(20).max().iloc[-1]

# =========================
# BREAKOUT
# =========================
if latest["Close"] > resistance:
    breakout = "🚀 Breakout"
elif latest["Close"] < support:
    breakout = "⚠️ Breakdown"
else:
    breakout = "➡️ Range Bound (No Breakout Yet)"

# =========================
# PREDICTION
# =========================
up = 50
down = 50

if latest["MACD"] > latest["Signal"]:
    up += 10
else:
    down += 10

if latest["Close"] > latest["MA20"]:
    up += 10
else:
    down += 10

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    [
        "📊 Overview",
        "📈 Technicals",
        "🤖 AI Assistant",
        "📊 Compare",
        "📁 Portfolio",
        "⭐ Watchlist & Alerts",
        "📊 Scanner",
        "🧠 AI Pro",
    ]
)

# =========================
# OVERVIEW (UNCHANGED)
# =========================
with tab1:
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Price", f"₹{latest['Close']:.2f}")
    col2.metric("RSI", f"{latest['RSI']:.2f}")
    col3.metric("MACD", f"{latest['MACD']:.2f}")
    col4.metric("Support", f"{support:.2f}")
    col5.metric("Resistance", f"{resistance:.2f}")
    col6.metric("Breakout", breakout)

    st.markdown("### 🤖 AI Prediction")
    p1, p2 = st.columns(2)
    p1.metric("Upside", f"{up}%")
    p2.metric("Downside", f"{down}%")

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
        )
    )
    fig.add_trace(go.Scatter(x=data.index, y=data["MA20"], name="MA20"))
    fig.add_hline(y=support, line_color="green")
    fig.add_hline(y=resistance, line_color="red")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🧠 Insights")
    trend = "Uptrend" if latest["Close"] > latest["MA20"] else "Downtrend"
    momentum = "Bullish" if latest["MACD"] > latest["Signal"] else "Bearish"

    st.write(f"• Trend: {trend}")
    st.write(f"• Momentum: {momentum}")
    st.write(f"• Breakout: {breakout}")

# =========================
# TECHNICALS (UNCHANGED)
# =========================
with tab2:
    st.dataframe(data.tail(30))

# =========================
# AI CHAT (UNCHANGED)
# =========================
with tab3:
    st.subheader("🤖 Trading Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.button("🧹 Clear Chat"):
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.write(f"{msg['role']}: {msg['content']}")

    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask question")
        submit = st.form_submit_button("Send")

    if submit and user_input:
        st.session_state.chat_history.append({"role": "User", "content": user_input})

        prompt = f"""
Act like a professional Indian stock trader.

Use:
- Breakout status
- Prediction (UP/DOWN)
- Trend logic

Be decisive:
- Say BUY / SELL / WAIT
- Give 1–2 line reason
- Mention risk level (Low/Medium/High)

Stock: {stock_input}
Breakout: {breakout}
Prediction: UP {up}% DOWN {down}%

User Question:
{user_input}
"""

        result = ask_ai_openrouter(prompt)

        st.session_state.chat_history.append({"role": "AI", "content": result})
        st.rerun()

# =========================
# COMPARE (ENHANCED SAFE)
# =========================
with tab4:

    st.subheader("📊 Compare Stocks")

    stocks = st.text_input("Compare stocks (comma separated)", "RELIANCE, TCS")

    col_results = st.columns(4)

    for i, s in enumerate(stocks.split(",")):
        try:
            s_clean = s.strip().upper()
            if not s_clean:
                continue

            s_full = format_stock(s_clean)
            d = yf.download(s_full, period="1mo", interval="1d")

            if d.empty:
                col_results[i % 4].error(f"{s_clean}: No Data")
                continue

            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)

            close_series = pd.Series(d["Close"].values.flatten(), index=d.index)
            latest_price = float(close_series.dropna().iloc[-1])
            prev_price = float(close_series.dropna().iloc[-2])

            change_pct = ((latest_price - prev_price) / prev_price) * 100
            arrow = "🔼" if change_pct > 0 else "🔽"

            col_results[i % 4].metric(
                label=s_full,
                value=f"₹{latest_price:.2f}",
                delta=f"{arrow} {change_pct:.2f}%",
            )

        except:
            col_results[i % 4].error(f"{s_clean} → error")

# =========================
# PORTFOLIO (UNCHANGED)
# =========================
with tab5:
    st.subheader("📁 Portfolio Tracker")

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []

    col1, col2, col3 = st.columns(3)

    stock = col1.text_input("Stock")
    qty = col2.number_input("Quantity", 1)
    buy = col3.number_input("Buy Price", 0.0)

    if st.button("➕ Add to Portfolio"):
        if stock:
            stock = stock.upper().strip()
            exists = any(p["stock"] == stock for p in st.session_state.portfolio)

            if not exists:
                st.session_state.portfolio.append(
                    {"stock": stock, "qty": qty, "buy": buy}
                )
            else:
                st.warning("Stock already exists")

    total_value = 0
    total_investment = 0
    rows = []

    for p in st.session_state.portfolio:
        try:
            s_full = format_stock(p["stock"])
            d = yf.download(s_full, period="5d")

            if d.empty:
                continue

            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)

            close_series = pd.Series(d["Close"].values.flatten(), index=d.index)
            latest_price = float(close_series.dropna().iloc[-1])

            value = latest_price * p["qty"]
            invested = p["buy"] * p["qty"]
            pnl = value - invested
            pct = (pnl / invested) * 100 if invested > 0 else 0

            total_value += value
            total_investment += invested

            rows.append(
                {
                    "Stock": s_full,
                    "Qty": p["qty"],
                    "Buy": p["buy"],
                    "Current": round(latest_price, 2),
                    "Value": round(value, 2),
                    "P&L": round(pnl, 2),
                    "%": round(pct, 2),
                }
            )

        except:
            continue

    if rows:
        df_port = pd.DataFrame(rows)
        st.dataframe(df_port, use_container_width=True)

        st.markdown("### 📊 Portfolio Summary")
        total_pnl = total_value - total_investment
        color = "green" if total_pnl >= 0 else "red"

        st.markdown(
            f"Total Value: ₹{total_value:.2f}  \n"
            f"Total Invested: ₹{total_investment:.2f}  \n"
            f"<span style='color:{color}'>Total P&L: ₹{total_pnl:.2f}</span>",
            unsafe_allow_html=True,
        )

    if st.button("🧹 Clear Portfolio"):
        st.session_state.portfolio = []
        st.rerun()
# =========================
# WATCHLIST + ALERTS (SAFE ADD)
# =========================
with tab6:

    st.subheader("⭐ Watchlist & Alerts")

    # =====================
    # SESSION INIT
    # =====================
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    if "alerts" not in st.session_state:
        st.session_state.alerts = []

    # =====================
    # ADD TO WATCHLIST
    # =====================
    col1, col2 = st.columns([3, 1])

    with col1:
        watch_stock = st.text_input("Add Stock to Watchlist")

    with col2:
        if st.button("➕ Add"):
            if watch_stock:
                s = watch_stock.upper().strip()
                if s not in st.session_state.watchlist:
                    st.session_state.watchlist.append(s)
                else:
                    st.warning("Already added")

    # =====================
    # DISPLAY WATCHLIST
    # =====================
    st.markdown("### 📌 Your Watchlist")

    if st.session_state.watchlist:
        for s in st.session_state.watchlist:
            try:
                s_full = format_stock(s)

                d = yf.download(s_full, period="5d", interval="1d")

                if d.empty:
                    st.warning(f"{s_full} → No Data")
                    continue

                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)

                close_series = pd.Series(d["Close"].values.flatten(), index=d.index)
                price = float(close_series.dropna().iloc[-1])

                colA, colB = st.columns([4, 1])
                colA.write(f"{s_full} → ₹{price:.2f}")

                if colB.button("❌", key=f"remove_{s}"):
                    st.session_state.watchlist.remove(s)
                    st.rerun()

            except:
                st.write(f"{s} → error")

    else:
        st.info("No stocks in watchlist")

    # =====================
    # ALERT CREATION
    # =====================
    st.markdown("### 🔔 Create Alert")

    col1, col2, col3 = st.columns(3)

    alert_stock = col1.text_input("Stock", key="alert_stock")
    alert_type = col2.selectbox(
        "Condition",
        ["Price Above", "Price Below", "% Change", "RSI Above", "RSI Below"],
    )
    alert_value = col3.number_input("Value", 0.0)

    if st.button("➕ Add Alert"):
        if alert_stock:
            st.session_state.alerts.append(
                {
                    "stock": alert_stock.upper().strip(),
                    "type": alert_type,
                    "value": alert_value,
                }
            )

    # =====================
    # CHECK ALERTS
    # =====================
    st.markdown("### 🚨 Alert Engine")

    triggered = []

    for alert in st.session_state.alerts:
        try:
            s_full = format_stock(alert["stock"])

            d = yf.download(s_full, period="5d", interval="1d")

            if d.empty:
                continue

            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)

            close_series = pd.Series(d["Close"].values.flatten(), index=d.index)
            price = float(close_series.dropna().iloc[-1])

            rsi_series = RSIIndicator(close_series).rsi()
            rsi = float(rsi_series.dropna().iloc[-1])

            hit = False

            if alert["type"] == "Price Above" and price > alert["value"]:
                hit = True
            elif alert["type"] == "Price Below" and price < alert["value"]:
                hit = True
            elif alert["type"] == "% Change":
                prev = float(close_series.dropna().iloc[-2])
                pct = ((price - prev) / prev) * 100
                if abs(pct) >= alert["value"]:
                    hit = True
            elif alert["type"] == "RSI Above" and rsi > alert["value"]:
                hit = True
            elif alert["type"] == "RSI Below" and rsi < alert["value"]:
                hit = True

            if hit:
                triggered.append(f"{s_full} → {alert['type']} {alert['value']} HIT")

        except:
            continue

    # =====================
    # DISPLAY RESULTS
    # =====================
    if triggered:
        st.error("🚨 Alerts Triggered")
        for t in triggered:
            st.write(t)
    else:
        st.success("✅ No alerts triggered")

    # =====================
    # VIEW ALL ALERTS
    # =====================
    if st.session_state.alerts:
        st.markdown("### 📋 All Alerts")
        st.json(st.session_state.alerts)

    # =====================
    # CLEAR ALERTS
    # =====================
    if st.button("🧹 Clear All Alerts"):
        st.session_state.alerts = []
        st.rerun()
# =========================
# MARKET SCANNER (SAFE ADD)
# =========================
with tab7:

    st.subheader("📊 Market Scanner")

    # Small curated NSE list (safe + fast)
    scan_list = [
        "RELIANCE",
        "TCS",
        "INFY",
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "AXISBANK",
        "LT",
        "ITC",
        "WIPRO",
    ]

    results = []

    for s in scan_list:
        try:
            s_full = format_stock(s)
            d = yf.download(s_full, period="5d", interval="1d")

            if d.empty:
                continue

            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.get_level_values(0)

            close_series = pd.Series(d["Close"].values.flatten(), index=d.index)

            latest = float(close_series.iloc[-1])
            prev = float(close_series.iloc[-2])

            change_pct = ((latest - prev) / prev) * 100

            # breakout logic (same as your core)
            support = float(close_series.tail(20).min())
            resistance = float(close_series.tail(20).max())

            breakout_flag = latest > resistance

            results.append(
                {
                    "Stock": s_full,
                    "Price": round(latest, 2),
                    "% Change": round(change_pct, 2),
                    "Breakout": "🚀 Yes" if breakout_flag else "-",
                }
            )

        except:
            continue

    if results:
        df_scan = pd.DataFrame(results)

        st.markdown("### 🔥 Top Gainers")
        st.dataframe(
            df_scan.sort_values("% Change", ascending=False).head(5),
            use_container_width=True,
        )

        st.markdown("### 🚀 Breakout Candidates")
        st.dataframe(df_scan[df_scan["Breakout"] == "🚀 Yes"], use_container_width=True)
    else:
        st.warning("No scan results")
# =========================
# AI PRO (SMART REASONING)
# =========================
with tab8:

    st.subheader("🧠 AI Pro Trading Assistant")

    if "chat_pro" not in st.session_state:
        st.session_state.chat_pro = []

    if st.button("🧹 Clear AI Pro Chat"):
        st.session_state.chat_pro = []

    for msg in st.session_state.chat_pro:
        st.write(f"{msg['role']}: {msg['content']}")

    with st.form("chat_pro_form", clear_on_submit=True):
        user_q = st.text_input("Ask deep analysis question")
        submit = st.form_submit_button("Ask")

    if submit and user_q:

        # ✅ SAFE VALUE EXTRACTION (NO ERRORS)
        try:
            price_val = float(latest["Close"])
        except:
            price_val = 0

        try:
            rsi_val = float(latest["RSI"])
        except:
            rsi_val = 0

        try:
            macd_val = float(latest["MACD"])
        except:
            macd_val = 0

        try:
            ma20_val = float(latest["MA20"])
        except:
            ma20_val = 0

        trend_val = "Uptrend" if price_val > ma20_val else "Downtrend"

        context = f"""
Stock: {stock_input}
Price: {price_val:.2f}
RSI: {rsi_val:.2f}
MACD: {macd_val:.2f}
Trend: {trend_val}
Support: {float(support):.2f}
Resistance: {float(resistance):.2f}
Breakout: {breakout}
"""

        prompt = f"""
You are a professional Indian stock market trader.

Analyze using:
- Price action
- RSI
- MACD
- Support/Resistance
- Breakout signals

Give structured output:

1. Trend: (Bullish / Bearish / Sideways)
2. Action: (BUY / SELL / WAIT)
3. Entry: (price range)
4. Stop Loss: (strict level)
5. Risk Level: (Low / Medium / High)
6. Reason: (2–3 lines simple explanation)

Be confident and practical. Avoid generic advice.

Context:
{context}

User Question:
{user_q}
"""

        result = ask_ai_openrouter(prompt)

        st.session_state.chat_pro.append({"role": "User", "content": user_q})
        st.session_state.chat_pro.append({"role": "AI", "content": result})

        st.rerun()
