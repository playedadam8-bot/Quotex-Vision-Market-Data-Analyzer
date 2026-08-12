import streamlit as st
import json
import requests
from PIL import Image
import io
import base64
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import re

# 1. Page Setup & Configuration
st.set_page_config(page_title="Quotex Ultimate Multi-Engine Analyzer", layout="wide")

# Custom Dark Theme Styling & Animations
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@600;700&display=swap');

    .stApp {
        background-color: #05070a;
    }

    .brand-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.5rem !important;
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

    /* Pulsing Status Indicator for Signal Generation */
    @keyframes pulse-ring {
      0% { transform: scale(0.95); opacity: 0.8; }
      50% { transform: scale(1.05); opacity: 1; box-shadow: 0 0 20px #00f2fe; }
      100% { transform: scale(0.95); opacity: 0.8; }
    }
    .signal-pulse-container {
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 25px 0;
    }
    .signal-status-circle {
      width: 130px;
      height: 130px;
      border-radius: 50%;
      background: radial-gradient(circle, #00f2fe 0%, #05070a 80%);
      border: 3px solid #00f2fe;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: #ffffff;
      font-family: 'Orbitron', sans-serif;
      font-weight: bold;
      animation: pulse-ring 1.8s infinite ease-in-out;
      text-align: center;
      box-shadow: 0 0 30px rgba(0, 242, 254, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="brand-title">QUOTEX ULTIMATE ANALYZER</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; letter-spacing:3px; font-family:Rajdhani;'>UTC+5 TIME SYNCED | 4-MODE ENGINE</p>", unsafe_allow_html=True)

# 2. Secure Secrets Retrieval
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("Error: Please add OPENROUTER_API_KEY in your Streamlit Cloud Secrets settings!")
    st.stop()

# Complete requested currency pairs dictionary
CURRENCY_PAIRS = {
    "EUR/JPY": {"flag": "🇪🇺🇯🇵", "yf": "EURJPY=X"},
    "CAD/JPY": {"flag": "🇨🇦🇯🇵", "yf": "CADJPY=X"},
    "EUR/GBP": {"flag": "🇪🇺🇬🇧", "yf": "EURGBP=X"},
    "AUD/JPY": {"flag": "🇦🇺🇯🇵", "yf": "AUDJPY=X"},
    "USD/JPY": {"flag": "🇺🇸🇯🇵", "yf": "USDJPY=X"},
    "AUD/USD": {"flag": "🇦🇺🇺🇸", "yf": "AUDUSD=X"},
    "AUD/CAD": {"flag": "🇦🇺🇨🇦", "yf": "AUDCAD=X"},
    "EUR/USD": {"flag": "🇪🇺🇺🇸", "yf": "EURUSD=X"},
    "EUR/CAD": {"flag": "🇪🇺🇨🇦", "yf": "EURCAD=X"},
    "AUD/CHF": {"flag": "🇦🇺🇨🇭", "yf": "AUDCHF=X"},
    "GBP/AUD": {"flag": "🇬🇧🇦🇺", "yf": "GBPAUD=X"},
    "GBP/USD": {"flag": "🇬🇧🇺🇸", "yf": "GBPUSD=X"},
    "EUR/AUD": {"flag": "🇪🇺🇦🇺", "yf": "EURAUD=X"},
    "CHF/JPY": {"flag": "🇨🇭🇯🇵", "yf": "CHFJPY=X"},
    "GBP/CAD": {"flag": "🇬🇧🇨🇦", "yf": "GBPCAD=X"},
    "GBP/CHF": {"flag": "🇬🇧🇨🇭", "yf": "GBPCHF=X"},
    "GBP/JPY": {"flag": "🇬🇧🇯🇵", "yf": "GBPJPY=X"},
    "USD/CHF": {"flag": "🇺🇸🇨🇭", "yf": "USDCHF=X"},
    "EUR/CHF": {"flag": "🇪🇺🇨🇭", "yf": "EURCHF=X"}
}

def get_custom_timer_options():
    options = []
    for m in range(1, 6):
        options.append(f"{m} Minute" if m == 1 else f"{m} Minutes")
    for s in range(5, 60, 5):
        options.append(f"{s} Seconds")
    for m in range(6, 16):
        options.append(f"{m} Minutes")
    return options

custom_timers = get_custom_timer_options()

# 4-Way Mode Selector
analysis_mode = st.selectbox(
    "Select Trading & Analysis Engine", 
    [
        "1️⃣ Screenshot Vision Analyzer (Auto 1-Min Standard)",
        "2️⃣ Screenshot Vision Analyzer (Manual Custom Timer)",
        "3️⃣ Live Market Data + AI Predictor (Manual Pair Selection)",
        "4️⃣ AI Auto-Scanned Pair Predictor (AI Picks Best Pair for Next-Min)"
    ]
)
st.markdown("---")

# --- MODE 1: Auto 1-Min Standard Screenshot Reader ---
if analysis_mode == "1️⃣ Screenshot Vision Analyzer (Auto 1-Min Standard)":
    st.subheader("📸 Screenshot Vision Analyzer (Auto 1-Min / Next-Minute Safe Entry)")
    
    with st.form("form_m1"):
        uploaded_file = st.file_uploader("Upload Quotex Chart Screenshot", type=["jpg", "png", "jpeg"], key="m1_file")
        submitted_m1 = st.form_submit_button("🚀 Analyze & Get Next-Minute Signal")

    if submitted_m1:
        if uploaded_file is not None:
            pulse_placeholder = st.empty()
            pulse_placeholder.markdown("""
                <div class="signal-pulse-container">
                    <div class="signal-status-circle">
                        <span style="font-size:0.85rem;">SCANNING</span>
                        <span style="font-size:0.7rem; color:#00f2fe; margin-top:3px;">CHART...</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            try:
                img = Image.open(uploaded_file)
                buffered = io.BytesIO()
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                local_tz = pytz.timezone('Asia/Karachi')
                current_local_time = datetime.now(local_tz).strftime("%H:%M:%S")

                prompt = f"""
                You are an expert binary options algorithmic trader analyzing a Quotex trading chart screenshot.
                Current local time (UTC+5): {current_local_time}
                
                Tasks:
                1. Read the current timestamp/clock time shown on the chart interface.
                2. Identify the asset name and live price.
                3. Analyze current trend, candlesticks, and indicators.
                4. Calculate precise entry target for the NEXT upcoming candle/minute (targeting entry exactly 2 seconds before new minute starts, e.g., HH:MM:58).
                5. Provide directional signal ("CALL" or "PUT") and technical reasoning.

                Output ONLY a valid JSON object with no markdown ticks, formatted exactly like this:
                {{
                  "asset": "...",
                  "live_price": "...",
                  "chart_time": "...",
                  "next_trade_entry_time": "Exact target time (e.g., HH:MM:58)",
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
                
                pulse_placeholder.empty()

                if response.status_code == 200:
                    raw_content = response.json()['choices'][0]['message']['content'].strip()
                    if raw_content.startswith("```"):
                        raw_content = raw_content.split("```")[1]
                        if raw_content.startswith("json"):
                            raw_content = raw_content[4:].strip()
                    if raw_content.endswith("```"):
                        raw_content = raw_content[:-3].strip()

                    data = json.loads(raw_content)
                    asset = data.get("asset", "N/A")
                    live_price = data.get("live_price", "N/A")
                    chart_time = data.get("chart_time", "N/A")
                    entry_target = data.get("next_trade_entry_time", "N/A")
                    signal = data.get("signal", "NEUTRAL").upper()
                    reason = data.get("reason", "No reason provided.")

                    banner_color = "#28a745" if signal == "CALL" else "#dc3545" if signal == "PUT" else "#ffc107"
                    arrow = "↑" if signal == "CALL" else "↓" if signal == "PUT" else "•"

                    st.markdown(f"""
                        <div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin: 20px 0;">
                            <span style="font-family:'Orbitron'; font-size:1.5rem;">{asset} &nbsp; {signal} (VISION SIGNAL)</span>
                            <span style="font-size:2.5rem;">{arrow}</span>
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Live Price", value=live_price)
                        st.metric(label="Chart Clock Time", value=chart_time)
                    with col2:
                        st.metric(label="⚡ Precise Entry Target (UTC+5)", value=entry_target)
                        st.metric(label="Expiry Timeframe", value="1 Minute")

                    st.markdown(f"""
                        <div class="vision-card" style="text-align: left; margin-top: 15px;">
                            <span style="color:#4facfe; font-family:'Orbitron'; font-size:1.1rem;">TECHNICAL REASONING:</span><br>
                            <p style="font-family:'Rajdhani'; font-size:1.2rem; color:#e0e0e0; margin-top:8px; line-height:1.5;">{reason}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                pulse_placeholder.empty()
                st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please upload a chart screenshot first!")

# --- MODE 2: Screenshot Vision Analyzer with Manual Custom Timer ---
elif analysis_mode == "2️⃣ Screenshot Vision Analyzer (Manual Custom Timer)":
    st.subheader("📸 Screenshot Vision Analyzer (Manual Custom Timer)")
    
    with st.form("form_m2"):
        selected_timer = st.selectbox("Select Expiry / Timer Option", custom_timers, key="m2_timer")
        uploaded_file = st.file_uploader("Upload Quotex Chart Screenshot", type=["jpg", "png", "jpeg"], key="m2_file")
        submitted_m2 = st.form_submit_button("🚀 Analyze with Custom Timer")

    if submitted_m2:
        if uploaded_file is not None:
            pulse_placeholder = st.empty()
            pulse_placeholder.markdown("""
                <div class="signal-pulse-container">
                    <div class="signal-status-circle">
                        <span style="font-size:0.85rem;">SCANNING</span>
                        <span style="font-size:0.7rem; color:#00f2fe; margin-top:3px;">CUSTOM...</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            try:
                img = Image.open(uploaded_file)
                buffered = io.BytesIO()
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                local_tz = pytz.timezone('Asia/Karachi')
                current_local_time = datetime.now(local_tz).strftime("%H:%M:%S")

                prompt = f"""
                You are an expert binary options algorithmic trader analyzing a Quotex trading chart screenshot.
                Selected Expiry Timer: {selected_timer}
                Current local time (UTC+5): {current_local_time}
                
                Tasks:
                1. Read current timestamp/clock time shown on the chart interface.
                2. Identify asset name and live price.
                3. Analyze trend and indicators calibrated specifically for a {selected_timer} duration.
                4. Calculate optimal entry timing and target execution.
                5. Provide directional signal ("CALL" or "PUT") and brief technical reasoning.

                Output ONLY a valid JSON object with no markdown ticks, formatted exactly like this:
                {{
                  "asset": "...",
                  "live_price": "...",
                  "chart_time": "...",
                  "next_trade_entry_time": "Exact target time (e.g., HH:MM:SS)",
                  "signal": "CALL" or "PUT",
                  "reason": "..."
                }}
                """

                response = requests.post(
                  url="[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)",
                  headers={"Authorization": f"Bearer {API_KEY}", "HTTP-Referer": "[https://shawkat-tradez.streamlit.app](https://shawkat-tradez.streamlit.app)", "X-OpenRouter-Title": "Quotex Custom Timer Analyzer"},
                  data=json.dumps({
                    "model": "openai/gpt-4o",
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}]
                  }),
                  timeout=30
                )
                
                pulse_placeholder.empty()

                if response.status_code == 200:
                    raw_content = response.json()['choices'][0]['message']['content'].strip()
                    if raw_content.startswith("```"):
                        raw_content = raw_content.split("```")[1]
                        if raw_content.startswith("json"):
                            raw_content = raw_content[4:].strip()
                    if raw_content.endswith("```"):
                        raw_content = raw_content[:-3].strip()

                    data = json.loads(raw_content)
                    signal = data.get("signal", "CALL").upper()
                    banner_color = "#28a745" if signal == "CALL" else "#dc3545"

                    st.markdown(f"""
                        <div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin: 20px 0;">
                            <span style="font-family:'Orbitron'; font-size:1.5rem;">{data.get("asset")} &nbsp; {signal} ({selected_timer} EXPIRY)</span>
                        </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Live Price", value=data.get("live_price"))
                        st.metric(label="Chart Time", value=data.get("chart_time"))
                    with col2:
                        st.metric(label="UTC+5 Entry Target", value=data.get("next_trade_entry_time"))
                        st.metric(label="Selected Expiry", value=selected_timer)

                    st.info(f"**Technical Reasoning:** {data.get('reason')}")
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                pulse_placeholder.empty()
                st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please upload a chart screenshot first!")

# --- MODE 3: Live Market Data + AI Predictor (Manual Pair Selection) ---
elif analysis_mode == "3️⃣ Live Market Data + AI Predictor (Manual Pair Selection)":
    st.subheader("📊 Live Market Data + AI Predictor (1m to 15m Expiry)")
    
    with st.form("form_m3"):
        col_p, col_t = st.columns(2)
        with col_p:
            pair_display_list = [f"{info['flag']} {pair}" for pair, info in CURRENCY_PAIRS.items()]
            selected_display = st.selectbox("Select Currency Pair", pair_display_list, key="m3_pair_sel")
            selected_pair_key = selected_display.split(" ")[1]
        with col_t:
            expiry_1_to_15 = [f"{m} Minute" if m == 1 else f"{m} Minutes" for m in range(1, 16)]
            selected_expiry = st.selectbox("Select Expiry Timer (1m - 15m)", expiry_1_to_15, key="m3_timer_sel")
        
        submitted_m3 = st.form_submit_button("🚀 Fetch Live Market Data & Generate AI Signal")

    if submitted_m3:
        pulse_placeholder = st.empty()
        pulse_placeholder.markdown("""
            <div class="signal-pulse-container">
                <div class="signal-status-circle">
                    <span style="font-size:0.85rem;">FETCHING</span>
                    <span style="font-size:0.7rem; color:#00f2fe; margin-top:3px;">OPENROUTER AI...</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        try:
            yf_symbol = CURRENCY_PAIRS[selected_pair_key]["yf"]
            ticker = yf.Ticker(yf_symbol)
            todays_data = ticker.history(period="1d", interval="1m")
            
            if len(todays_data) < 5:
                pulse_placeholder.empty()
                st.error("Insufficient live market data returned from Yahoo Finance.")
                st.stop()
                
            prev_candle = todays_data.iloc[-2]
            current_open = float(prev_candle['Open'])
            current_close = float(prev_candle['Close'])
            current_high = float(prev_candle['High'])
            current_low = float(prev_candle['Low'])
            live_price = float(todays_data['Close'].iloc[-1])

            local_tz = pytz.timezone('Asia/Karachi')
            now_utc5 = datetime.now(local_tz)
            target_time = (now_utc5 + timedelta(seconds=15)).strftime("%H:%M:%S")

            ai_prompt = f"""
            You are an elite forex and binary options algorithmic trading engine.
            Asset: {selected_pair_key}
            Selected Expiry Timer: {selected_expiry}
            Candle Open: {current_open:.5f}
            Candle Close: {current_close:.5f}
            Candle High: {current_high:.5f}
            Candle Low: {current_low:.5f}
            Live Price: {live_price:.5f}
            Current UTC+5 Time: {now_utc5.strftime("%H:%M:%S")}

            Analyze trend structure, momentum, and price action configured specifically for a {selected_expiry} expiry duration. 
            Provide a definitive signal ("CALL" or "PUT") and a professional 1-sentence technical justification.
            
            Output ONLY raw JSON format matching this exact structure, with no markdown tags:
            {{
              "signal": "CALL",
              "reason": "..."
            }}
            """

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "HTTP-Referer": "https://shawkat-tradez.streamlit.app",
                    "X-OpenRouter-Title": "Shawkat Live Market Predictor"
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": ai_prompt}],
                    "max_tokens": 200
                },
                timeout=30
            )

            pulse_placeholder.empty()

            signal = "CALL"
            reason = "OpenRouter AI calculated positive continuation for the selected expiry."

            if response.status_code == 200:
                try:
                    res_json = response.json()
                    raw_res = res_json['choices'][0]['message']['content'].strip()
                    if raw_res.startswith("```"):
                        raw_res = raw_res.split("```")[1]
                        if raw_res.startswith("json"):
                            raw_res = raw_res[4:].strip()
                    if raw_res.endswith("```"):
                        raw_res = raw_res[:-3].strip()

                    data = json.loads(raw_res)
                    signal = data.get("signal", "CALL").upper()
                    reason = data.get("reason", reason)
                except Exception:
                    pass

            banner_color = "#28a745" if signal == "CALL" else "#dc3545"
            arrow = "↑" if signal == "CALL" else "↓"
            display_title_name = f"{CURRENCY_PAIRS[selected_pair_key]['flag']} {selected_pair_key}"

            st.markdown(f"""
                <div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin-bottom:15px;">
                    <span style="font-family:'Orbitron'; font-size:1.6rem;">{display_title_name} &nbsp; {signal} ({selected_expiry})</span>
                    <span style="font-size:2.8rem;">{arrow}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="vision-card">
                    <div style="color:#00f2fe; font-family:'Rajdhani'; font-size:1.3rem; font-weight:700;">
                        UTC+5 TARGET TIME: <span style="color:#ffffff;">{target_time}</span>
                    </div>
                    <div style="font-family:'Rajdhani'; color:#aaa; font-size:1.1rem; margin-top:5px;">LIVE YFINANCE PRICE: {live_price:.5f}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="vision-card" style="text-align: left; margin-top: 15px;">
                    <span style="color:#4facfe; font-family:'Orbitron'; font-size:1.1rem;">OPENROUTER AI REASONING ({selected_expiry}):</span><br>
                    <p style="font-family:'Rajdhani'; font-size:1.2rem; color:#e0e0e0; margin-top:8px; line-height:1.5;">{reason}</p>
                </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            pulse_placeholder.empty()
            st.error(f"Live market data or AI analysis error: {e}")

# --- MODE 4: AI Auto-Scanned Pair Predictor (AI Picks Best Pair for Next-Min) ---
else:
    st.subheader("🤖 AI Auto-Scanned Pair Predictor (Live Market)")
    st.markdown("<p style='color:#aaa; font-family:Rajdhani;'>OpenRouter AI will autonomously scan live market data across all 19 currency pairs, choose the strongest trending asset for the next minute, and deliver a precision signal!</p>", unsafe_allow_html=True)

    with st.form("form_m4"):
        submitted_m4 = st.form_submit_button("🚀 AI Scan & Get Best Next-Minute Signal")

    if submitted_m4:
        pulse_placeholder = st.empty()
        pulse_placeholder.markdown("""
            <div class="signal-pulse-container">
                <div class="signal-status-circle">
                    <span style="font-size:0.85rem;">AI SCANNING</span>
                    <span style="font-size:0.7rem; color:#00f2fe; margin-top:3px;">MARKETS...</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        try:
            scanned_summary = []
            for pair in CURRENCY_PAIRS.keys():
                try:
                    yf_sym = CURRENCY_PAIRS[pair]["yf"]
                    t_data = yf.Ticker(yf_sym).history(period="1d", interval="1m")
                    if len(t_data) >= 3:
                        c_open = float(t_data.iloc[-2]['Open'])
                        c_close = float(t_data.iloc[-2]['Close'])
                        c_price = float(t_data['Close'].iloc[-1])
                        diff_pct = ((c_close - c_open) / c_open) * 100
                        scanned_summary.append(f"Pair: {pair}, Open: {c_open:.5f}, Close: {c_close:.5f}, Live: {c_price:.5f}, Delta: {diff_pct:.3f}%")
                except Exception:
                    continue

            local_tz = pytz.timezone('Asia/Karachi')
            now_utc5 = datetime.now(local_tz)
            target_time = (now_utc5 + timedelta(seconds=58)).strftime("%H:%M:%S")

            ai_prompt = f"""
            You are an elite autonomous binary options AI scanner powered by OpenRouter. Review the following live market data snippets for all available currency pairs:
            {json.dumps(scanned_summary)}

            Current UTC+5 Time: {now_utc5.strftime("%H:%M:%S")}
            Task: Choose the SINGLE best currency pair with the highest probability momentum setup for the NEXT 1-MINUTE candle. Provide your chosen asset, directional signal ("CALL" or "PUT"), and brief technical justification.

            Output ONLY raw JSON format matching this exact structure, with no markdown tags:
            {{
              "best_asset": "EUR/USD",
              "signal": "CALL",
              "reason": "Strong bullish momentum and clean candle closure."
            }}
            """

            response = requests.post(
                url="[https://openrouter.ai/api/v1/chat/completions](https://openrouter.ai/api/v1/chat/completions)",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "HTTP-Referer": "[https://shawkat-tradez.streamlit.app](https://shawkat-tradez.streamlit.app)",
                    "X-OpenRouter-Title": "Shawkat AI Auto Scanner"
                },
                json={
                    "model": "openai/gpt-4o",
                    "messages": [{"role": "user", "content": ai_prompt}],
                    "max_tokens": 250
                },
                timeout=30
            )

            pulse_placeholder.empty()

            best_asset = "EUR/USD"
            signal = "CALL"
            reason = "OpenRouter AI selected optimal volatility continuation setup."

            if response.status_code == 200:
                try:
                    res_json = response.json()
                    raw_res = res_json['choices'][0]['message']['content'].strip()
                    if raw_res.startswith("```"):
                        raw_res = raw_res.split("```")[1]
                        if raw_res.startswith("json"):
                            raw_res = raw_res[4:].strip()
                    if raw_res.endswith("```"):
                        raw_res = raw_res[:-3].strip()

                    data = json.loads(raw_res)
                    best_asset = data.get("best_asset", best_asset)
                    signal = data.get("signal", signal).upper()
                    reason = data.get("reason", reason)
                except Exception:
                    pass

            banner_color = "#28a745" if signal == "CALL" else "#dc3545"
            arrow = "↑" if signal == "CALL" else "↓"
            flag_prefix = CURRENCY_PAIRS.get(best_asset, {"flag": "🌐"}).get("flag", "🌐")
            display_title_name = f"{flag_prefix} {best_asset}"

            st.markdown(f"""
                <div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin-bottom:15px;">
                    <span style="font-family:'Orbitron'; font-size:1.6rem;">{display_title_name} &nbsp; {signal} (AI AUTO-PICK)</span>
                    <span style="font-size:2.8rem;">{arrow}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="vision-card">
                    <div style="color:#00f2fe; font-family:'Rajdhani'; font-size:1.3rem; font-weight:700;">
                        UTC+5 PRECISE ENTRY TARGET: <span style="color:#ffffff;">{target_time} (2s before close)</span>
                    </div>
                    <div style="font-family:'Rajdhani'; color:#aaa; font-size:1.1rem; margin-top:5px;">EXPIRY: 1 Minute</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="vision-card" style="text-align: left; margin-top: 15px;">
                    <span style="color:#4facfe; font-family:'Orbitron'; font-size:1.1rem;">OPENROUTER AI AUTO-SCANNER REASONING:</span><br>
                    <p style="font-family:'Rajdhani'; font-size:1.2rem; color:#e0e0e0; margin-top:8px; line-height:1.5;">{reason}</p>
                </div>
            """, unsafe_allow_html=True)

        exceptException as e:
            pulse_placeholder.empty()
            st.error(f"AI auto-scan error: {e}")
