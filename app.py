import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Vantage Local Institutional Terminal", layout="wide")

st.title("🛰️ Vantage Local MT5 Institutional Bridge & Dashboard")
st.markdown("Connected directly to your laptop's MetaTrader 5 terminal with **Zero Latency**.")

# --- INITIALIZE MT5 ---
if not mt5.initialize():
    st.error(f"❌ MT5 Initialization failed, error code = {mt5.last_error()}")
    st.stop()

# Account info sidebar
acc = mt5.account_info()
if acc:
    st.sidebar.success("🟢 MT5 Connected")
    st.sidebar.metric("Account Login", acc.login)
    st.sidebar.metric("Balance", f"${acc.balance:,.2f} {acc.currency}")
    st.sidebar.metric("Equity", f"${acc.equity:,.2f} {acc.currency}")

# Symbol setup
symbol = "XAUUSD"
if mt5.symbol_info(symbol) is None:
    symbol = "GOLD"
mt5.symbol_select(symbol, True)

# Fetch live tick
tick = mt5.symbol_info_tick(symbol)
bid = tick.bid if tick else 0.0
ask = tick.ask if tick else 0.0
spread = round(ask - bid, 2)

# Fetch history for indicators
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
if rates is not None and len(rates) > 0:
    df = pd.DataFrame(rates)
    df['hl'] = df['high'] - df['low']
    atr = round(df['hl'].rolling(14).mean().iloc[-1], 2)
    current_close = round(df['close'].iloc[-1], 2)
else:
    atr = 5.0
    current_close = bid

# --- METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Symbol", symbol)
col2.metric("Live Bid", f"${bid:,.2f}")
col3.metric("Live Ask", f"${ask:,.2f}")
col4.metric("Spread", f"{spread} Pips")

st.markdown("---")

# --- TRADING EXECUTION PANEL ---
st.subheader("⚡ Instant Order Execution Panel")
lot = st.number_input("Lot Size", value=0.01, step=0.01, format="%.2f")

sl_price = round(current_close - (atr * 1.5), 2)
tp_price = round(current_close + (atr * 2.5), 2)

c1, c2, c3 = st.columns(3)
c1.info(f"**Estimated SL:** ${sl_price}")
c2.success(f"**Estimated TP:** ${tp_price}")
c3.warning(f"**ATR (14):** ${atr}")

if st.button("🚀 Execute BUY Order on Vantage MT5"):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": ask,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": 20,
        "magic": 112233,
        "comment": "Python Local Bridge",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        st.error(f"❌ Order Execution Failed! Retcode: {result.retcode}")
    else:
        st.success(f"✅ Order Placed Successfully! Ticket ID: {result.order}")

mt5.shutdown()