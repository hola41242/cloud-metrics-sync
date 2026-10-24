import os
import glob
import time
import threading
import requests
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# ----------------- UPTIMEROBOT HEALTHCHECK -----------------
@app.get("/")
def health():
    return {
        "status": "healthy",
        "service": "Cloud Metrics Worker",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ----------------- BENCODE PARSER -----------------
def bdecode(data):
    def decode_item(idx):
        char = data[idx:idx+1]
        if char == b'i':
            idx += 1
            end = data.index(b'e', idx)
            return int(data[idx:end]), end + 1
        elif char == b'l':
            idx += 1
            res = []
            while data[idx:idx+1] != b'e':
                item, idx = decode_item(idx)
                res.append(item)
            return res, idx + 1
        elif char == b'd':
            idx += 1
            res = {}
            while data[idx:idx+1] != b'e':
                key, idx = decode_item(idx)
                val, idx = decode_item(idx)
                res[key.decode('utf-8', errors='ignore')] = val
            return res, idx + 1
        elif char.isdigit():
            colon = data.index(b':', idx)
            length = int(data[idx:colon])
            start = colon + 1
            return data[start:start+length], start + length
        else:
            raise ValueError(f"Invalid byte at index {idx}")
    res, _ = decode_item(0)
    return res

# ----------------- BACKGROUND WORKER -----------------
def background_worker():
    time.sleep(5)
    print("🚀 Background telemetry & announce loop started...")
    
    tg_token = os.environ.get("TG_BOT_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    if tg_token and tg_chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                data={"chat_id": tg_chat_id, "text": "🟢 [Render Node Online] Background pulse active."}
            )
        except Exception:
            pass

    cycle = 0
    while True:
        cycle += 1
        try:
            # Periodic heartbeat cycle
            print(f"📡 [Cycle {cycle}] Announce heartbeat active at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Send Telegram status every 6 cycles (~3 hours)
            if cycle % 6 == 0 and tg_token and tg_chat_id:
                requests.post(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    data={"chat_id": tg_chat_id, "text": f"📡 [Render Pulse] Still active. Cycle: {cycle}"}
                )
        except Exception as e:
            print(f"Error in pulse loop: {e}")
            
        time.sleep(1800)  # Har 30 min mein ek pulse

@app.on_event("startup")
def run_worker():
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
