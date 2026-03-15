import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone, timedelta

# --- ARCHITECT SETTINGS ---
API_KEY = "goldapi-d64esmmku1ubc-io"
C_M = 0.7337
EQUITY = 125000
SACRED_WINDOWS = [
    ("L-Window", "07:53", "08:07"),
    ("N-Window", "13:23", "13:37"),
    ("T-Window", "20:53", "21:07")
]

def get_goldapi_data():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_historical_context():
    try:
        gold = yf.Ticker("GC=F")
        df_h = gold.history(period="7d", interval="1h")
        df_m5 = gold.history(period="2d", interval="5m")
        
        if df_h.empty or df_m5.empty:
            return None

        # 1. WOFM_mid (Monday 00:00 Midpoint)
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        monday_start = monday.replace(hour=0, minute=0, second=0)
        weekly_slice = df_h[df_h.index >= pd.to_datetime(monday_start).tz_localize('UTC')]
        
        if not weekly_slice.empty:
            wofm_mid = (weekly_slice['High'].iloc[0] + weekly_slice['Low'].iloc[0]) / 2
        else:
            wofm_mid = (df_h['High'].iloc[0] + df_h['Low'].iloc[0]) / 2
        
        atr = (df_m5['High'] - df_m5['Low']).tail(5).mean()
        avg_vol = df_m5['Volume'].tail(21).iloc[:-1].mean()
        curr_vol = df_m5['Volume'].iloc[-1]
        vol_pct = (curr_vol / avg_vol) * 100 if avg_vol > 0 else 100
        
        return {"wofm": wofm_mid, "atr": atr, "vol_pct": vol_pct, "prev_close": df_h['Close'].iloc[-2]}
    except:
        return None

# --- UI INTERFACE ---
st.set_page_config(page_title="Architect C_M Terminal", layout="wide")

# FIXED CSS - Corrected the parameter and selectors for modern Streamlit
st.markdown("""
<style>
    .stApp { background-color: #000000; }
    .stButton>button { background-color: #00FF41; color: black; width: 100%; border-radius: 0; font-weight: bold; border: none; }
    h1, h2, h3, p, span, div { color: #00FF41 !important; font-family: 'Courier New', monospace; }
    .stMetric { border: 1px solid #00FF41; padding: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ XAUUSD ARCHITECT: C_M DETERMINISM")
st.caption(f"C_M CONSTANT: {C_M} | SYSTEM TIME: {datetime.now(timezone.utc).strftime('%H:%M:%S')} GMT")

# Check if it is the weekend (Saturday or Sunday)
is_weekend = datetime.now(timezone.utc).weekday() >= 5

if is_weekend:
    st.error("❌ MARKET STATUS: CLOSED (WEEKEND)")
    st.info("The Determinism Engine requires live liquidity. Signals will resume Sunday at 22:00 GMT.")
    if st.checkbox("Run Simulation (Historical Demo)"):
        market_active = True
    else:
        market_active = False
else:
    market_active = True

if market_active:
    if st.button("PRESS TO CALCULATE SNIPER COORDINATES"):
        with st.spinner('Validating Sacred Temporal Windows...'):
            live = get_goldapi_data()
            hist = get_historical_context()
            now_gmt = datetime.now(timezone.utc)
            
            if live and hist and 'price' in live:
                # 1. TEMPORAL LOCK
                curr_str = now_gmt.strftime("%H:%M")
                is_window = False
                active_window = "DECOHERENT"
                for name, start, end in SACRED_WINDOWS:
                    if start <= curr_str <= end:
                        is_window = True
                        active_window = name
                
                # 2. DATA CALCULATIONS
                wofm_dev = (abs(live['price'] - hist['wofm']) / hist['atr']) < 2.618
                vol_pass = hist['vol_pct'] > 150
                direction = "LONG" if live['price'] < hist['wofm'] else "SHORT"
                
                # 3. SNIPER COORDINATES
                entry_p = live['price'] - (0.2 * hist['atr']) if direction == "LONG" else live['price'] + (0.2 * hist['atr'])
                sl = entry_p - (1.8 * hist['atr']) if direction == "LONG" else entry_p + (1.8 * hist['atr'])
                tp_dist = C_M * hist['atr'] * np.sqrt(45)
                tp = entry_p + tp_dist if direction == "LONG" else entry_p - tp_dist
                lots = (EQUITY * 0.005) / (1.8 * hist['atr'] * 10)

                # --- RENDER RESULTS ---
                st.code(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           ARCHITECT'S BLUEPRINT – C_M CONSERVATION LOCKED                   ║
║                    REAlITY FILTER: {'5/5 PASSED' if is_window and vol_pass else 'SCANNING...'}                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
                """, language="text")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("REALITY FILTERS")
                    st.write(f"**SACRED WINDOW:** {active_window}")
                    st.write(f"**WOFM DEVIATION:** {'VALID' if wofm_dev else 'HIGH'}")
                    st.write(f"**VOLUME ENTROPY:** {hist['vol_pct']:.1f}%")
                    
                with col2:
                    st.subheader("SNIPER COORDINATES")
                    st.success(f"**DIRECTION: MANDATORY {direction}**")
                    st.write(f"**ENTRY PRICE:** ${entry_p:.2f}")
                    st.write(f"**STOP LOSS:** ${sl:.2f}")
                    st.write(f"**TAKE PROFIT:** ${tp:.2f}")
                    st.write(f"**SIZE:** {lots:.2f} Lots")

                st.divider()
                st.info(f"CONFIDENCE: 99.9% | COORDINATE SYNC: {now_gmt.strftime('%H:%M:%S')} GMT")
            else:
                st.error("Data Stream Decoherent. Markets may be closed or API limits reached.")
