import requests
import time
import hashlib
import re
from collections import deque

# --- ⚙️ DUAL API CONFIGURATION ---
# API 1
API_1_URL = "http://203.161.58.20/api/functions/agent-api/otp" 
API_1_KEY = "sk_b331fc25989e09a87e32cd047f13d4ff346696b821c556cb642075d293f8ee35"

# API 2
API_2_URL = "http://147.135.212.197/crapi/had/viewstats"
API_2_TOKEN = "RVFRQTRSQnxgk2NDSJiAZERTmIdSa49rXIB3fYJ_YVJXmICIdIyB"

# Telegram Bot Config
BOT_TOKEN = "8364756844:AAFGuS6NTl7MzSJt3TjuD4OoMSTXO4KFjYY"
CHAT_ID = "-1003880345384" 

POLL_INTERVAL = 5 
FETCH_RECORDS = 50 

seen_otps = deque(maxlen=4000)

def extract_otp(message):
    ig_match = re.search(r'(?i)ig[- ]?(\d+)', message)
    if ig_match: return ig_match.group(1)
    space_match = re.search(r'\b(\d{3})[\s-](\d{3})\b', message)
    if space_match: return space_match.group(1) + space_match.group(2)
    match2 = re.search(r'\b\d{4,8}\b', message)
    return match2.group(0) if match2 else "Copy"

def mask_number(num):
    num = str(num)
    if len(num) > 5:
        return f"{num[:2]}𝑰𝑵𝑺𝑯𝑼𝑩𝑬{num[-3:]}"
    return num

def send_to_telegram(number, platform, message, otp_code_api=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    otp_code = otp_code_api if otp_code_api else extract_otp(message)
    masked_num = mask_number(number)
    
    # --- 📝 উপরের টেক্সটে আপনার দেওয়া অরিজিনাল বক্স ডিজাইন ---
    text = f"🌟 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑶𝑻𝑷</b> 🌟\n\n"
    text += f"💎 <b>𝑺𝒆𝒓𝒗𝒊𝒄𝒆:</b> {platform.upper()}\n\n"
    
    text += f"┌───────── • ☎️ • ─────────┐\n"
    text += f"    <code>+{masked_num}</code>\n"
    text += f"└──────────────────────────┘\n\n"
    
    text += f"✨ 𝑷𝒐𝒘𝒆𝒓𝒆𝒅 𝒃𝒚 <a href='https://t.me/Minhaz_Official'>𝑴𝒊𝒏𝒉𝒂𝒛</a> ✨"
    
    # --- 🔘 নিচে ছোট ছোট বাটন পাশাপাশি (Compact Design) ---
    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"🔑 {otp_code}", "copy_text": {"text": otp_code}},
                {"text": "📝 𝑭𝒖𝒍𝒍 𝑴𝒔𝒈", "copy_text": {"text": message[:256]}}
            ],
            [
                {"text": "🔥 𝑮𝒆𝒕 𝑵𝒖𝒎𝒃𝒆𝒓", "url": "https://t.me/INSHUBE_BOT"},
                {"text": "🌟 𝑪𝒉𝒂𝒏𝒏𝒆𝒍", "url": "https://t.me/Minhaz_Official"}
            ]
        ]
    }

    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML", 
        "reply_markup": keyboard,
        "disable_web_page_preview": True
    }
    
    # --- 🛠️ Auto-Retry & Timeout Fix Logic ---
    max_retries = 3
    for attempt in range(max_retries):
        try: 
            response = requests.post(url, json=payload, timeout=20)
            if not response.json().get("ok"):
                print(f"⚠️ Telegram Error: {response.text}")
            break 
        except requests.exceptions.ReadTimeout:
            print(f"⚠️ Telegram Timeout. Retrying... ({attempt + 1}/{max_retries})")
            time.sleep(2) 
        except Exception as e: 
            print(f"❌ Telegram Send Error: {e}")
            break

# ================= Fetch From API 1 =================
def fetch_api_1():
    headers = {"x-api-key": API_1_KEY}
    params = {"page": 1, "limit": FETCH_RECORDS}
    try:
        response = requests.get(API_1_URL, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"): return data.get("data", [])
    except: pass
    return []

# ================= Fetch From API 2 =================
def fetch_api_2():
    params = {"token": API_2_TOKEN, "records": FETCH_RECORDS}
    try:
        response = requests.get(API_2_URL, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success": return data.get("data", [])
    except: pass
    return []

def main():
    print("🚀 DUAL ENGINE Running... (Custom Box + Compact Buttons)")
    
    while True:
        # ----------------- Check API 1 -----------------
        otps_1 = fetch_api_1()
        for otp in reversed(otps_1):
            raw_msg = otp.get("message_text") or otp.get("sms") or otp.get("message") or otp.get("text") or otp.get("content") or ""
            message = str(raw_msg).strip()
            
            if not message or message.lower() in ['none', 'null', '']: continue
                
            number = str(otp.get("number", "Unknown"))
            platform = str(otp.get("platform", "Service"))
            dt = str(otp.get("received_at", "time"))
            otp_code = str(otp.get("otp_code", ""))
            
            otp_id = hashlib.md5(f"API1_{dt}_{number}_{message}".encode()).hexdigest()
            
            if otp_id not in seen_otps:
                send_to_telegram(number, platform, message, otp_code)
                seen_otps.append(otp_id)
                print(f"✅ [API 1] OTP Forwarded: {otp_code}")
                time.sleep(0.5)
                
        # ----------------- Check API 2 -----------------
        otps_2 = fetch_api_2()
        for otp in reversed(otps_2):
            message = str(otp.get("message", "")).strip()
            
            if not message or message.lower() in ['none', 'null', '']: continue
                
            number = str(otp.get("num", "Unknown Number"))
            platform = str(otp.get("cli", "Unknown"))
            dt = str(otp.get("dt", "time"))
            
            otp_id = hashlib.md5(f"API2_{dt}_{number}_{message}".encode()).hexdigest()
            
            if otp_id not in seen_otps:
                otp_code = extract_otp(message)
                send_to_telegram(number, platform, message, otp_code)
                seen_otps.append(otp_id)
                print(f"✅ [API 2] OTP Forwarded: {otp_code}")
                time.sleep(0.5)

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
