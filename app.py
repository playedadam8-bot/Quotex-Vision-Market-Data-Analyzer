import streamlit as st
import json
import requests
from PIL import Image
import io
import base64
import yfinance as yf
from datetime import datetime
import pytz

# 1. Page Setup & Configuration
st.set_page_config(page_title="Quotex Ultimate Analyzer", layout="wide")

# Custom Dark Theme Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@600;700&display=swap');

    .stApp {
        background-color: #05070a;
    }

    .brand-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.8rem !important;
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

st.markdown('<h1 class="brand-title">QUOTEX ULTIMATE ANALYZER</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; letter-spacing:3px; font-family:Rajdhani;'>VISION SCREENSHOT & LIVE MARKET ENGINE</p>", unsafe_allow_html=True)

# 2. Secure Secrets Retrieval
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except Exception as e:
    st.error("Error: Please add OPENROUTER_API_KEY in your Streamlit Cloud Secrets settings!")
    st.stop()

# 3. Mode Selector
analysis_mode = st.radio("Select Analysis Mode", ["📸 Screenshot Vision Analyzer", "📊 Live Market Data & Candle Predictor"], horizontal=True)
st.markdown("---")

if analysis_mode == "📸 Screenshot Vision Analyzer":
    uploaded_file = st.file_uploader("Upload Quotex Chart Screenshot", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Chart Preview", use_container_width=True)

        if st.button("🚀 Analyze Screenshot & Get Signal"):
            with st.spinner("AI Vision is scanning chart elements & calculating entry timing..."):
                try:
                    buffered = io.BytesIO()
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(buffered, format="JPEG")
                    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

                    prompt = """
                    You are an expert binary options algorithmic trader analyzing a Quotex trading chart screenshot.
                    
                    Tasks:
                    1. Read the current timestamp/clock time shown on the chart interface.
                    2. Identify the asset name and live price.
                    3. Analyze the current trend, candlesticks, and any visible technical indicators.
                    4. Calculate the precise entry target for the NEXT upcoming candle (target entry time exactly 2 seconds before the new minute starts, e.g., HH:MM:58).
                    5. Provide your directional signal ("CALL" or "PUT") and brief technical reasoning.

                    Output ONLY a valid JSON object with no markdown ticks, formatted exactly like this:
                    {
                      "asset": "...",
                      "live_price": "...",
                      "chart_time": "...",
                      "next_trade_entry_time": "Exact target time to click trade (e.g., HH:MM:58)",
                      "signal": "CALL" or "PUT",
                      "reason": "Brief technical explanation."
                    }
                    """

                    response = requests.post(
                      url="https://openrouter.ai/api/v1/chat/completions",
                      headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "HTTP-Referer": "https://shawkat-tradez.streamlit.app", 
                        "X-OpenRouter-Title": "Quotex Vision Analyzer", 
                      },
                      data=json.dumps({
                        "model": "openai/gpt-4o",
                        "max_tokens": 400,
                        "messages": [
                          {
                            "role": "user",
                            "content": [
                              {"type": "text", "text": prompt},
                              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                          }
                        ]
                      }),
                      timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            raw_content = result['choices'][0]['message']['content'].strip()
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
                                st.metric(label="⚡ Precise Entry Target", value=entry_target)
                                st.metric(label="Expiry Timeframe", value="1 Minute")

                            st.markdown(f"""
                                <div class="vision-card" style="text-align: left; margin-top: 15px;">
                                    <span style="color:#4facfe; font-family:'Orbitron'; font-size:1.1rem;">TECHNICAL REASONING:</span><br>
                                    <p style="font-family:'Rajdhani'; font-size:1.2rem; color:#e0e0e0; margin-top:8px; line-height:1.5;">{reason}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Unexpected API Response: {result}")
                    else:
                        st.error(f"API Error ({response.status_code}): {response.text}")

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

else:
    # Live Financial Data Mode
    FLAG_MAP = {
        "EUR/JPY": "🇪🇺🇯🇵EUR/JPY", "CAD/JPY": "🇨🇦🇯🇵CAD/JPY", 
        "EUR/GBP": "🇪🇺🇬🇧EUR/GBP", "AUD/JPY": "🇦🇺🇯🇵AUD/JPY",
        "USD/JPY": "🇺🇸🇯🇵USD/JPY", "AUD/USD": "🇦🇺🇺🇸AUD/USD", 
        "EUR/USD": "🇪🇺🇺🇸EUR/USD", "GBP/USD": "🇬🇧🇺🇸GBP/USD",
        "GBP/JPY": "🇬🇧🇯🇵GBP/JPY", "USD/CHF": "🇺🇸🇨🇭USD/CHF"
    }

    selected_pair_key = st.selectbox("Select Currency Pair", list(FLAG_MAP.keys()), format_func=lambda x: FLAG_MAP[x])
    display_pair_name = FLAG_MAP[selected_pair_key]

    if st.button("🚀 GENERATE LIVE MARKET SIGNAL"):
        with st.spinner(f"Fetching live market candles for {selected_pair_key}..."):
            try:
                ticker_symbol = selected_pair_key.replace("/", "") + "=X"
                ticker = yf.Ticker(ticker_symbol)
                todays_data = ticker.history(period="1d", interval="1m")
                
                if len(todays_data) < 3:
                    st.error("Insufficient market data available right now.")
                    st.stop()
                    
                prev_candle = todays_data.iloc[-2]
                current_open = float(prev_candle['Open'])
                current_close = float(prev_candle['Close'])
                current_high = float(prev_candle['High'])
                current_low = float(prev_candle['Low'])
                live_price = float(todays_data['Close'].iloc[-1])

                default_bias = "CALL" if current_close >= current_open else "PUT"
                next_minute_time = datetime.now().strftime("%H:%M:58")

                banner_color = "#28a745" if default_bias == "CALL" else "#dc3545"
                arrow = "↑" if default_bias == "CALL" else "↓"

                st.markdown(f"""
                    <div style="background:{banner_color}; padding:20px; border-radius:15px; display:flex; justify-content:space-between; align-items:center; color:white; margin-bottom:15px;">
                        <span style="font-family:'Orbitron'; font-size:1.6rem;">{display_pair_name} &nbsp; {default_bias} (LIVE FEED)</span>
                        <span style="font-size:2.8rem;">{arrow}</span>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="vision-card">
                        <div style="color:#00f2fe; font-family:'Rajdhani'; font-size:1.3rem; font-weight:700;">
                            EXECUTION TARGET: <span style="color:#ffffff;">{next_minute_time} (2s before close)</span>
                        </div>
                        <div style="font-family:'Rajdhani'; color:#aaa; font-size:1.1rem; margin-top:5px;">LIVE PRICE: {live_price:.5f}</div>
                    </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Market data error: {e}")
