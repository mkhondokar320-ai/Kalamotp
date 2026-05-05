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
BOT_TOKEN = "8364756844:AAFrxV2a9wnpqGfciz8GYllpfn1_nUQmn90"
CHAT_ID = "-1003880345384" 

POLL_INTERVAL = 5 
FETCH_RECORDS = 50 

seen_otps = deque(maxlen=4000)

def extract_otp(message):
    message_str = str(message)
    message_lower = message_str.lower()
    
    # 1. কিওয়ার্ড অনুযায়ী শক্তিশালী সার্চ (ig, fb, g, code, otp, pin)
    keyword_match = re.search(r'(?:ig|fb|g|instagram|facebook|code|otp|pin)[^\d]*(\d{4,10})', message_lower)
    if keyword_match:
        return keyword_match.group(1)
    
    # 2. মাঝখানে স্পেস বা হাইফেন থাকলে (যেমন: 123-456 বা 123 456)
    split_match = re.search(r'\b(\d{3,4})[\s-](\d{3,4})\b', message_str)
    if split_match: 
        return split_match.group(1) + split_match.group(2)
    
    # 3. ইউনিভার্সাল ফিল্টার (মেসেজের ভেতর থেকে যেকোনো সংখ্যা বের করবে)
    numbers = re.findall(r'\d+', message_str)
    if numbers:
        # প্রথমে চেষ্টা করবে ৪ থেকে ১০ ডিজিটের স্ট্যান্ডার্ড ওটিপি ধরতে
        for n in numbers:
            if 4 <= len(n) <= 10:
                return n
        # যদি না পায়, তাহলে মেসেজে পাওয়া প্রথম সংখ্যাটাই দিয়ে দেবে (সর্বোচ্চ ১০ ডিজিট)
        return numbers[0][:10]
        
    return "Copy"

def mask_number(num):
    num = str(num)
    if len(num) > 5:
        return f"{num[:2]}𝑰𝑵𝑺𝑯𝑼𝑩𝑬{num[-3:]}"
    return num

def send_to_telegram(number, platform, message, final_otp_code):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    masked_num = mask_number(number)
    
    # --- 📝 Text Design ---
    text = f"🌟 <b>𝑰𝑵𝑺 𝑯𝑼𝑩𝑬 𝑶𝑻𝑷</b> 🌟\n\n"
    text += f"💎 <b>𝑺𝒆𝒓𝒗𝒊𝒄𝒆:</b> {platform.upper()}\n\n"
    
    text += f"┌───────── • ☎️ • ─────────┐\n"
    text += f"    <code>+{masked_num}</code>\n"
    text += f"└──────────────────────────┘\n"
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"🔑 {final_otp_code}", "copy_text": {"text": final_otp_code}}
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
    
    # --- 🛠️ Retry Logic ---
    max_retries = 3
    for attempt in range(max_retries):
        try: 
            response = requests.post(url, json=payload, timeout=20)
            if not response.json().get("ok"):
                print(f"⚠️ Telegram Error: {response.text}")
            break 
        except requests.exceptions.ReadTimeout:
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
    print("🚀 ALL OTP EXTRACTOR Running... (Max Precision Mode)")
    
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
            
            # 🔥 "None" Bug Fix: API যদি None বা উল্টাপাল্টা কিছু দেয়, সরাসরি Extract করবে
            api_otp = otp.get("otp_code")
            if not api_otp or str(api_otp).lower() == "none" or str(api_otp).strip() == "":
                final_otp = extract_otp(message)
            else:
                api_otp_str = str(api_otp)
                # API এর ওটিপি যদি ৪ থেকে ১০ ডিজিটের মধ্যে হয়, তবেই সেটা নেবে
                if 4 <= len(api_otp_str) <= 10:
                    final_otp = api_otp_str
                else:
                    final_otp = extract_otp(message)
            
            otp_id = hashlib.md5(f"API1_{dt}_{number}_{message}".encode()).hexdigest()
            
            if otp_id not in seen_otps:
                send_to_telegram(number, platform, message, final_otp)
                seen_otps.append(otp_id)
                print(f"✅ [API 1] OTP Forwarded: {final_otp}")
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
                final_otp = extract_otp(message)
                send_to_telegram(number, platform, message, final_otp)
                seen_otps.append(otp_id)
                print(f"✅ [API 2] OTP Forwarded: {final_otp}")
                time.sleep(0.5)

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
