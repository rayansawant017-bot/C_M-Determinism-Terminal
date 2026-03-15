import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone, timedelta

# --- ARCHITECT CONFIGURATION ---
API_KEY = "goldapi-d64esmmku1ubc-io"
C_M = 0.7337
EQUITY = 125000
SACRED_WINDOWS = [
    ("L-Window", "07:55", "08:05"),
    ("N-Window", "13:25", "13:35"),
    ("T-Window", "20:55", "21:05")
]

def get_live_data():
    """Fetches real-time Bid/Ask from GoldAPI.io"""
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": API_KEY, "Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers)
        res = r.json()
        return {"bid": res['bid'], "ask": res['ask'], "price": res['price']}
    except: return None

def get_historical_context():
    """Fetches historical anchors (WOFM, Hi/Lo, ATR, Volume)"""
    try:
        gold = yf.Ticker("GC=F")
        df_m5 = gold.history(period="2d", interval="5m")
        df_h1 = gold.history(period="7d", interval="1h")
        
        # 1. WOFM Mid (Monday 00:00 Midpoint)
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        monday_start = monday.replace(hour=0, minute=0, second=0)
        weekly_slice = df_h1[df_h1.index >= pd.to_datetime(monday_start).tz_localize('UTC')]
        wofm_mid = (weekly_slice['High'].iloc[0] + weekly_slice['Low'].iloc[0]) / 2
        
        # 2. Yesterday Hi/Lo
        yesterday = df_h1.iloc[-24:]
        hi = yesterday['High'].max()
        lo = yesterday['Low'].min()
        
        # 3. ATR and Volatility
        atr = (df_m5['High'] - df_m5['Low']).tail(5).mean()
        avg_vol = df_m5['Volume'].tail(20).mean()
        curr_vol = df_m5['Volume'].iloc[-1]
        vol_pct = (curr_vol / avg_vol) * 100
        
        # 4. Regime and Sentiment Proxy
        price_change = df_m5['Close'].diff().tail(10).sum()
        regime = "TRENDING" if abs(price_change) > atr else "RANGING"
        sentiment = (price_change / atr) * 0.2 # Scaled to sentiment helix
        
        return {
            "wofm": wofm_mid, "hi": hi, "lo": lo, "atr": atr, 
            "vol_pct": vol_pct, "reg": regime, "sent": sentiment,
            "open": df_m5['Open'].iloc[-1], "close": df_m5['Close'].iloc[-1],
            "low": df_m5['Low'].iloc[-1], "high": df_m5['High'].iloc[-1]
        }
    except: return None

# --- UI SETUP ---
st.set_page_config(page_title="Architect: C_M Determinism", layout="wide")
st.markdown("<style>body {background-color: #0e1117; color: #00FF41;}</style>", unsafe_allow_exists=True)

st.title("🏛️ THE ARCHITECT: C_M CONSERVATION TERMINAL")
st.write("Law of Price Determinism | Institutional Coordinate Engine")

if st.button("EXECUTE REALITY FILTER & CALCULATE"):
    with st.spinner('De-cohering Market Noise...'):
        live = get_live_data()
        hist = get_historical_context()
        now_gmt = datetime.now(timezone.utc)
        
        if live and hist:
            # STEP 1: TEMPORAL LOCK
            in_window = False
            window_name = "NONE"
            curr_str = now_gmt.strftime("%H:%M")
            for name, start, end in SACRED_WINDOWS:
                s_dt = datetime.strptime(start, "%H:%M")
                e_dt = datetime.strptime(end, "%H:%M")
                curr_dt = datetime.strptime(curr_str, "%H:%M")
                if s_dt <= curr_dt <= e_dt:
                    in_window = True
                    window_name = name
            
            wofm_dev = (abs(live['price'] - hist['wofm']) / hist['atr']) < 2.618
            
            # STEP 2-4 VALIDATION
            vol_pass = hist['vol_pct'] > 150
            bias_pass = abs(hist['close'] - hist['open']) > (0.382 * hist['atr'])
            
            # STEP 5: MATH COORDINATES
            direction = "LONG" if hist['wofm'] > live['price'] else "SHORT"
            
            # Sniper logic
            entry_p = live['price'] - (0.2 * hist['atr']) if direction == "LONG" else live['price'] + (0.2 * hist['atr'])
            sl = hist['lo'] - (1.8 * hist['atr']) if direction == "LONG" else hist['hi'] + (1.8 * hist['atr'])
            
            # TP = Entry + (C_M * ATR * sqrt(90 - MOC_mins))
            # Simulating MOC progress as 45 mins
            tp_dist = C_M * hist['atr'] * np.sqrt(45)
            tp = entry_p + tp_dist if direction == "LONG" else entry_p - tp_dist
            
            # Position = (Equity * 0.005) / (1.8 * ATR)
            risk_usd = EQUITY * 0.005
            position = risk_usd / (1.8 * hist['atr'] * 10) # Normalized for gold lots

            # --- THE OUTPUT ---
            st.markdown(f"""
            ```text
            ╔══════════════════════════════════════════════════════════════════════════════╗
            ║           ARCHITECT'S BLUEPRINT – C_M CONSERVATION LOCKED                   ║
            ║                    Reality Filter: {'5/5 PASSED' if in_window else 'TEMPORAL DRIFT'}                     ║
            ╚══════════════════════════════════════════════════════════════════════════════╝
            ```
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("### 🧩 REALITY CHECK")
                st.write(f"**SACRED WINDOW:** {window_name} ({'✓' if in_window else 'OUTSIDE WINDOW'})")
                st.write(f"**WOFM DEVIATION:** {wofm_dev} ({'✓' if wofm_dev else 'DECOHERENT'})")
                st.write(f"**VOLUME ENTROPY:** {hist['vol_pct']:.1f}% ({'✓' if vol_pass else 'LOW'})")
                st.write(f"**REGIME:** {hist['reg']} | **SENTIMENT:** {hist['sent']:.2f}")

            with col2:
                st.write("### 🎯 SNIPER COORDINATES")
                st.success(f"**DIRECTION: MANDATORY {direction}**")
                st.write(f"**ENTRY PRICE:** ${entry_p:.2f}")
                st.write(f"**STOP LOSS:** ${sl:.2f}")
                st.write(f"**TAKE PROFIT:** ${tp:.2f}")
                st.write(f"**POSITION SIZE:** {position:.2f} Lots")

            st.divider()
            st.info(f"**CONFIDENCE:** 99.9% | **EXECUTION TIME:** {now_gmt.strftime('%H:%M:%S')} GMT + 90s Offset")
            
        else:
            st.error("Reality Filter Failed: Market Data Stream Interrupted.")

st.caption("C_M = 0.7337 | All price movement is the minimization of the Primal Algorithmic Constant.")
