from flask import Flask, jsonify
import aiohttp
import asyncio
import json
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

# টোকেন লোড করার ফাংশন
def load_tokens():
    try:
        with open("token_bd.json", "r") as f:
            data = json.load(f)
        return [item["token"] for item in data if "token" in item]
    except: return []

async def visit(session, url, token, uid, data, sem):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "keep-alive"
    }
    async with sem:
        try:
            async with session.post(url, headers=headers, data=data, ssl=False, timeout=5) as resp:
                return resp.status == 200
        except: return False

@app.route('/<int:uid>')
async def send_visits(uid):
    tokens = load_tokens()
    if not tokens: return jsonify({"error": "No tokens"}), 500

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    target = 1000 # Vercel-এর জন্য ১০০০ পারফেক্ট
    
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)
    sem = asyncio.Semaphore(200) # স্পিড বাড়ানোর জন্য ২০০ সেমাফোর

    async with aiohttp.ClientSession() as session:
        tasks = [visit(session, url, tokens[i % len(tokens)], uid, payload, sem) for i in range(target)]
        results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r)
    return jsonify({"uid": uid, "success": success, "limit": target})

# Vercel-এর জন্য এটি প্রয়োজন
def handler(event, context):
    return app(event, context)
