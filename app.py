import streamlit as st
import json
import requests
from PIL import Image
import io
import base64
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# 1. Page Setup & Configuration
st.set_page_config(page_title="Quotex Ultimate Multi-Engine Analyzer", layout="wide")

# Custom Dark Theme Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@600;700&display=swap');

    .stApp {
        background-color: #05070a;
    }

    .brand-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.6rem !important;
        background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 0px;
    }

    .vision-card {
        background: rgba(255, 255, 255, 0.02);
        border: 2px solid rgba(0, 242, 254, 0.2);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 0 25px rgba(79, 172, 254, 0.1);
    }

    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 4em;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white !important;
        font-weight: bold;
        border: none;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(79, 172, 254, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="brand-title">QUOTEX ULTIMATE MULTI-ENGINE ANALYZER</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; letter-spacing:3px; font-family:Rajdhani;'>UTC+5 TIME SYNCED | STANDARD & OTC MODES</p>", unsafe_allow_html=True)

# 2. Secure Secrets Retrieval
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("Error: Please add OPENROUTER_API_KEY in your Streamlit Cloud Secrets settings!")
    st.stop()

# 3. 4-Way Mode Selector
analysis_mode = st.selectbox(
    "Select Trading & Analysis Engine", 
    [
        "1️⃣ Screenshot Vision Analyzer (Standard Market)",
        "2️⃣ Screenshot Vision Analyzer (OTC Market)",
        "3️⃣ Live Market Data + AI Predictor (Standard Market)",
        "4️⃣ Live Market Data + AI Predictor (OTC Market)"
    ]
)
st.markdown("---")

# Helper function to generate flexible timeframes (5s increments up to 1m, then 1m increments)
def get_timeframe_options():
    options = []
    # Seconds from 5s to 55s
    for sec in range(5, 60, 5):
        options.append(f"{sec} Seconds")
    # Minutes from 1 min to 60 mins
    for min_val in range(1, 61):
        if min_val == 1:
            options.append("1 Minute")
        else:
            options.append(f"{min_val} Minutes")
    return options

timeframes_list = get_timeframe_options()

# --- OPTION 1: Screenshot Vision Analyzer (Standard) ---
if analysis_mode == "1️⃣ Screenshot Vision Analyzer (Standard Market)":
    st.subheader("📸 Standard Screenshot Vision Analyzer")
    selected_tf = st.selectbox("Select Expiry / Timer Option", timeframes_list, key="s1_tf")
    uploaded_file = st.file_uploader("Upload Standard Quotex Chart Screenshot", type=["jpg", "png", "jpeg"], key="s1_file")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Standard Chart Preview", use_container_width=True)

        if st.button("🚀 Analyze Standard Screenshot", key="btn_s1"):
            with st.spinner(f"Analyzing for {selected_tf} expiry (UTC+5)..."):
                try:
                    buffered = io.BytesIO()
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(buffered, format="JPEG")
                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                    local_tz = pytz.timezone('Asia/Karachi')
                    current_local_time = datetime.now(local_tz).strftime("%H:%M:%S")

                    prompt = f"""
                    You are an expert binary options algorithmic trader analyzing a standard Quotex trading chart screenshot.
                    Target Expiry Timeframe Selected: {selected_tf}
                    Current local time (UTC+5): {current_local_time}
                    
                    Tasks:
                    1. Read the current timestamp/clock time shown on the chart interface.
                    2. Identify the asset name and live price.
                    3. Analyze trend, candlesticks, and indicators specifically calibrated for a {selected_tf} trade duration.
                    4. Calculate precise entry target (accounting for safety execution).
                    5. Provide directional signal ("CALL" or "PUT") and brief technical reasoning.

                    Output ONLY a valid JSON object with no markdown ticks, formatted exactly like this:
                    {{
                      "asset": "...",
                      "live_price": "...",
                      "chart_time": "...",
                      "next_trade_entry_time": "Exact target time (e.g. HH:MM:SS)",
                      "signal": "CALL" or "PUT",
                      "reason": "..."
                    }}
                    """

                    response = requests.post(
                      url="https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": "https://shawkat-tradez.streamlit.app", "X-OpenRouter-Title": "Quotex Vision Analyzer"},
                      data=json.dumps({
                        "model": "openai/gpt-4o",
                        "max_tokens": 400,
                        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
                      }),
                      timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = json.loads(response.json()['choices'][0]['message']['content'].strip().replace("```json","").replace("```",""))
                        signal = data.get("signal", "CALL").upper()
                        banner_color = "#28a745" if signal == "CALL" else "#dc3545"
                        
                        st.markdown(f'<div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin:20px 0;"><span style="font-family:\'Orbitron\'; font-size:1.5rem;">{data.get("asset")} &nbsp; {signal} ({selected_tf} EXPIRY)</span></div>', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Live Price", data.get("live_price"))
                            st.metric("Chart Time", data.get("chart_time"))
                        with col2:
                            st.metric("UTC+5 Entry Target", data.get("next_trade_entry_time"))
                            st.metric("Market Type", "Standard")
                        st.info(f"**Reasoning:** {data.get('reason')}")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# --- OPTION 2: Screenshot Vision Analyzer (OTC) ---
elif analysis_mode == "2️⃣ Screenshot Vision Analyzer (OTC Market)":
    st.subheader("📸 OTC Market Screenshot Vision Analyzer")
    selected_tf = st.selectbox("Select Expiry / Timer Option", timeframes_list, key="s2_tf")
    uploaded_file = st.file_uploader("Upload OTC Quotex Chart Screenshot", type=["jpg", "png", "jpeg"], key="s2_file")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="OTC Chart Preview", use_container_width=True)

        if st.button("🚀 Analyze OTC Screenshot", key="btn_s2"):
            with st.spinner(f"Analyzing OTC chart for {selected_tf} expiry (UTC+5)..."):
                try:
                    buffered = io.BytesIO()
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(buffered, format="JPEG")
                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                    local_tz = pytz.timezone('Asia/Karachi')
                    current_local_time = datetime.now(local_tz).strftime("%H:%M:%S")

                    prompt = f"""
                    You are an expert OTC binary options algorithmic trader analyzing an OTC Quotex market screenshot.
                    Target Expiry Timeframe Selected: {selected_tf}
                    Current local time (UTC+5): {current_local_time}
                    
                    OTC markets have unique price action behavior. Analyze candles, micro-structure, and synthetic volatility matching a {selected_tf} duration.
                    Provide directional signal ("CALL" or "PUT") and brief technical reasoning.

                    Output ONLY a valid JSON object with no markdown ticks, formatted exactly like this:
                    {{
                      "asset": "...",
                      "live_price": "...",
                      "chart_time": "...",
                      "next_trade_entry_time": "Exact target time (e.g. HH:MM:SS)",
                      "signal": "CALL" or "PUT",
                      "reason": "..."
                    }}
                    """

                    response = requests.post(
                      url="https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": "https://shawkat-tradez.streamlit.app", "X-OpenRouter-Title": "Quotex OTC Vision Analyzer"},
                      data=json.dumps({
                        "model": "openai/gpt-4o",
                        "max_tokens": 400,
                        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
                      }),
                      timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = json.loads(response.json()['choices'][0]['message']['content'].strip().replace("```json","").replace("```",""))
                        signal = data.get("signal", "CALL").upper()
                        banner_color = "#28a745" if signal == "CALL" else "#dc3545"
                        
                        st.markdown(f'<div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin:20px 0;"><span style="font-family:\'Orbitron\'; font-size:1.5rem;">{data.get("asset")} &nbsp; {signal} (OTC - {selected_tf})</span></div>', unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Live Price", data.get("live_price"))
                            st.metric("Chart Time", data.get("chart_time"))
                        with col2:
                            st.metric("UTC+5 Entry Target", data.get("next_trade_entry_time"))
                            st.metric("Market Type", "OTC Synthetic")
                        st.info(f"**OTC Reasoning:** {data.get('reason')}")
                except Exception as e:
                    st.error(f"OTC analysis failed: {e}")

# --- OPTION 3: Live Market Data + AI Predictor (Standard) ---
elif analysis_mode == "3️⃣ Live Market Data + AI Predictor (Standard Market)":
    st.subheader("📊 Live Market Data + AI Predictor (Standard)")
    
    col_p, col_t = st.columns(2)
    with col_p:
        standard_pairs = {"EUR/USD": "🇪🇺🇺🇸EUR/USD", "GBP/USD": "🇬🇧🇺🇸GBP/USD", "USD/JPY": "🇺🇸🇯🇵USD/JPY", "EUR/JPY": "🇪🇺🇯🇵EUR/JPY"}
        selected_pair_key = st.selectbox("Select Standard Currency Pair", list(standard_pairs.keys()), format_func=lambda x: standard_pairs[x], key="l1_pair")
    with col_t:
        selected_tf = st.selectbox("Select Expiry / Timer Option", timeframes_list, key="l1_tf")

    if st.button("🚀 Fetch Live Data & Generate AI Signal", key="btn_l1"):
        with st.spinner(f"Pulling live standard market data for {selected_pair_key} ({selected_tf})..."):
            try:
                ticker_symbol = selected_pair_key.replace("/", "") + "=X"
                ticker = yf.Ticker(ticker_symbol)
                todays_data = ticker.history(period="1d", interval="1m")
                
                if len(todays_data) < 3:
                    st.error("Insufficient market data available.")
                    st.stop()
                    
                prev_candle = todays_data.iloc[-2]
                current_open = float(prev_candle['Open'])
                current_close = float(prev_candle['Close'])
                live_price = float(todays_data['Close'].iloc[-1])

                local_tz = pytz.timezone('Asia/Karachi')
                now_utc5 = datetime.now(local_tz)
                target_time = (now_utc5 + timedelta(seconds=15)).strftime("%H:%M:%S")

                ai_prompt = f"""
                You are an elite binary options algorithmic trading engine.
                Asset: {selected_pair_key} (Standard Market)
                Expiry Timeframe: {selected_tf}
                Open: {current_open:.5f}
                Close: {current_close:.5f}
                Current UTC+5 Time: {now_utc5.strftime("%H:%M:%S")}

                Analyze momentum and volatility for a {selected_tf} duration. Provide definitive signal ("CALL" or "PUT") and 1-sentence technical justification.
                Output ONLY raw JSON format matching this exact structure:
                {{"signal": "CALL", "reason": "..."}}
                """

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": "https://shawkat-tradez.streamlit.app", "X-OpenRouter-Title": "Standard Live Predictor"},
                    json={"model": "openai/gpt-4o", "messages": [{"role": "user", "content": ai_prompt}], "max_tokens": 200},
                    timeout=30
                )

                signal = "CALL" if current_close >= current_open else "PUT"
                reason = "Momentum favors continuation on standard price action."
                if response.status_code == 200:
                    try:
                        data = json.loads(response.json()['choices'][0]['message']['content'].strip().replace("```json","").replace("```",""))
                        signal = data.get("signal", signal).upper()
                        reason = data.get("reason", reason)
                    except:
                        pass

                banner_color = "#28a745" if signal == "CALL" else "#dc3545"
                st.markdown(f'<div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin-bottom:15px;"><span style="font-family:\'Orbitron\'; font-size:1.6rem;">{standard_pairs[selected_pair_key]} &nbsp; {signal} ({selected_tf})</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="vision-card"><div style="color:#00f2fe; font-family:\'Rajdhani\'; font-size:1.3rem; font-weight:700;">UTC+5 TARGET TIME: <span style="color:#ffffff;">{target_time}</span></div><div style="font-family:\'Rajdhani\'; color:#aaa; font-size:1.1rem; margin-top:5px;">LIVE PRICE: {live_price:.5f}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="vision-card" style="text-align: left; margin-top: 15px;"><span style="color:#4facfe; font-family:\'Orbitron\'; font-size:1.1rem;">AI REASONING:</span><p style="font-family:\'Rajdhani\'; font-size:1.2rem; color:#e0e0e0; margin-top:8px;">{reason}</p></div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")

# --- OPTION 4: Live Market Data + AI Predictor (OTC) ---
else:
    st.subheader("📊 Live Market Data + AI Predictor (OTC Market Simulation)")
    
    col_p, col_t = st.columns(2)
    with col_p:
        otc_pairs = {"EUR/USD-OTC": "🇪🇺🇺🇸EUR/USD (OTC)", "GBP/USD-OTC": "🇬🇧🇺🇸GBP/USD (OTC)", "USD/JPY-OTC": "🇺🇸🇯🇵USD/JPY (OTC)", "EUR/JPY-OTC": "🇪🇺🇯🇵EUR/JPY (OTC)"}
        selected_pair_key = st.selectbox("Select OTC Currency Pair", list(otc_pairs.keys()), format_func=lambda x: otc_pairs[x], key="l2_pair")
    with col_t:
        selected_tf = st.selectbox("Select Expiry / Timer Option", timeframes_list, key="l2_tf")

    if st.button("🚀 Fetch OTC Simulation Data & Generate AI Signal", key="btn_l2"):
        with st.spinner(f"Simulating OTC price feeds for {selected_pair_key} ({selected_tf})..."):
            try:
                # Using standard proxy ticker to feed baseline volatility for OTC algorithmic modeling
                ticker_symbol = selected_pair_key.replace("-OTC", "").replace("/", "") + "=X"
                ticker = yf.Ticker(ticker_symbol)
                todays_data = ticker.history(period="1d", interval="1m")
                
                if len(todays_data) < 3:
                    st.error("Insufficient market data available.")
                    st.stop()
                    
                prev_candle = todays_data.iloc[-2]
                current_open = float(prev_candle['Open'])
                current_close = float(prev_candle['Close'])
                live_price = float(todays_data['Close'].iloc[-1])

                local_tz = pytz.timezone('Asia/Karachi')
                now_utc5 = datetime.now(local_tz)
                target_time = (now_utc5 + timedelta(seconds=15)).strftime("%H:%M:%S")

                ai_prompt = f"""
                You are an expert OTC algorithmic trading engine specializing in synthetic market patterns.
                Asset: {selected_pair_key} (OTC Market)
                Expiry Timeframe: {selected_tf}
                Baseline Open: {current_open:.5f}
                Baseline Close: {current_close:.5f}
                Current UTC+5 Time: {now_utc5.strftime("%H:%M:%S")}

                Simulate OTC algorithmic behavior and price oscillation for a {selected_tf} trade duration. Provide definitive signal ("CALL" or "PUT") and 1-sentence technical justification.
                Output ONLY raw JSON format matching this exact structure:
                {{"signal": "PUT", "reason": "..."}}
                """

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": "https://shawkat-tradez.streamlit.app", "X-OpenRouter-Title": "OTC Live Predictor"},
                    json={"model": "openai/gpt-4o", "messages": [{"role": "user", "content": ai_prompt}], "max_tokens": 200},
                    timeout=30
                )

                signal = "PUT" if current_close >= current_open else "CALL"
                reason = "OTC algorithmic reversal model expected at current level."
                if response.status_code == 200:
                    try:
                        data = json.loads(response.json()['choices'][0]['message']['content'].strip().replace("```json","").replace("```",""))
                        signal = data.get("signal", signal).upper()
                        reason = data.get("reason", reason)
                    except:
                        pass

                banner_color = "#28a745" if signal == "CALL" else "#dc3545"
                st.markdown(f'<div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin-bottom:15px;"><span style="font-family:\'Orbitron\'; font-size:1.6rem;">{otc_pairs[selected_pair_key]} &nbsp; {signal} ({selected_tf})</span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="vision-card"><div style="color:#00f2fe; font-family:\'Rajdhani\'; font-size:1.3rem; font-weight:700;">UTC+5 TARGET TIME: <span style="color:#ffffff;">{target_time}</span></div><div style="font-family:\'Rajdhani\'; color:#aaa; font-size:1.1rem; margin-top:5px;">SIMULATED LIVE PRICE: {live_price:.5f}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="vision-card" style="text-align: left; margin-top: 15px;"><span style="color:#4facfe; font-family:\'Orbitron\'; font-size:1.1rem;">OTC AI REASONING:</span><p style="font-family:\'Rajdhani\'; font-size:1.2rem; color:#e0e0e0; margin-top:8px;">{reason}</p></div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error: {e}")
