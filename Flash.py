from flask import Flask, jsonify
import aiohttp
import asyncio
import json
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

# টোকেন লোড করার ছোট ফাংশন
def get_test_token():
    try:
        with open("token_bd.json", "r") as f:
            data = json.load(f)
        return data[0]["token"] # শুধু প্রথম টোকেনটি নিবে টেস্টের জন্য
    except:
        return None

@app.route('/')
def home():
    return "<h1>Vercel Testing Bot is Running!</h1>"

@app.route('/test/<int:uid>')
async def test_visit(uid):
    token = get_test_token()
    if not token:
        return jsonify({"error": "token_bd.json ফাইলে কোনো টোকেন নেই!"}), 500

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    
    # এনক্রিপশন লজিক
    try:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        payload = bytes.fromhex(encrypted)
    except Exception as e:
        return jsonify({"error": f"Encryption failed: {str(e)}"}), 500

    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=payload, ssl=False, timeout=10) as resp:
                status = resp.status
                return jsonify({
                    "uid": uid,
                    "http_status": status,
                    "message": "সাকসেস হয়েছে!" if status == 200 else "টোকেনটি OB52 এর হতে পারে, তাই কাজ করেনি।"
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Vercel এর জন্য প্রয়োজনীয়
def handler(app, event, context):
    return app(event, context)
