from flask import Flask, jsonify
import aiohttp
import asyncio
import json
import os
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

# টোকেন লোড করার ফাংশন
def load_tokens():
    try:
        # Vercel-এ ফাইল পাথ ঠিক রাখতে
        path = os.path.join(os.path.dirname(__file__), 'token_bd.json')
        with open(path, "r") as f:
            data = json.load(f)
        return [item["token"] for item in data if "token" in item and item["token"] != ""]
    except:
        return []

# ভিজিট পাঠানোর ফাংশন
async def visit_task(session, url, token, payload, sem):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "keep-alive"
    }
    async with sem:
        try:
            async with session.post(url, headers=headers, data=payload, ssl=False, timeout=5) as resp:
                return resp.status == 200
        except:
            return False

@app.route('/')
def home():
    return "<h1>Vercel High-Speed Visit Bot is Live!</h1>"

@app.route('/visit/<int:uid>')
async def send_visits(uid):
    tokens = load_tokens()
    if not tokens:
        return jsonify({"error": "token_bd.json ফাইলে কোনো টোকেন পাওয়া যায়নি!"}), 500

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    target = 1000 # Vercel-এর জন্য ১০০০ লিমিট পারফেক্ট
    
    # এনক্রিপশন লজিক
    try:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        payload = bytes.fromhex(encrypted)
    except Exception as e:
        return jsonify({"error": f"Encryption failed: {str(e)}"}), 500

    # সেমাফোর ২০০ রাখা হয়েছে যাতে দ্রুত কাজ শেষ হয়
    sem = asyncio.Semaphore(200)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(target):
            token = tokens[i % len(tokens)]
            tasks.append(visit_task(session, url, token, payload, sem))
        
        results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r)
    return jsonify({
        "status": "Success",
        "uid": uid,
        "sent": target,
        "success": success,
        "failed": target - success
    })
