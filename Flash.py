from flask import Flask, jsonify
import aiohttp
import asyncio
import json
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

# টেস্টিং ফাংশন: ভিজিট কাজ করছে কি না দেখার জন্য
async def single_visit(uid):
    # token_bd.json থেকে প্রথম টোকেনটি নেওয়া
    try:
        with open("token_bd.json", "r") as f:
            tokens = json.load(f)
            token = tokens[0]["token"]
    except:
        return "Token Error: token_bd.json ফাইলটি চেক করুন"

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)
    
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=payload, ssl=False) as resp:
            return resp.status

# মেইন রুট
@app.route('/')
def home():
    return "<h1>Vercel Testing Bot is Running!</h1>"

# চেক করার জন্য রুট: /test/UID
@app.route('/test/<int:uid>')
async def test_route(uid):
    # সরাসরি await ব্যবহার করা হয়েছে, যা flask[async] এ কাজ করবে
    status = await single_visit(uid)
    return jsonify({
        "uid": uid,
        "http_status": status,
        "message": "সাকসেস!" if status == 200 else "ফেইল (টোকেন সমস্যা হতে পারে)"
    })

if __name__ == "__main__":
    app.run()
