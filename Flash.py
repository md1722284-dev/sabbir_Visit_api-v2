from flask import Flask, jsonify
import aiohttp
import asyncio
import json
import os
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

async def visit_task(session, url, token, payload, sem):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "keep-alive"
    }
    async with sem:
        try:
            # এখানে প্রতি রিকোয়েস্টের মাঝে খুব সামান্য বিরতি দেওয়া হয়েছে যাতে স্প্যাম না দেখায়
            await asyncio.sleep(0.05) 
            async with session.post(url, headers=headers, data=payload, ssl=False, timeout=10) as resp:
                # যদি স্ট্যাটাস ২০০ না হয়, তবে লগে প্রিন্ট হবে (Vercel Dashboard এ দেখা যাবে)
                if resp.status != 200:
                    print(f"Failed with status: {resp.status}")
                return resp.status == 200
        except Exception as e:
            print(f"Request Error: {e}")
            return False

@app.route('/visit/<int:uid>')
async def send_visits(uid):
    # টোকেন লোড করার লজিক
    try:
        path = os.path.join(os.path.dirname(__file__), 'token_bd.json')
        with open(path, "r") as f:
            tokens_data = json.load(f)
        tokens = [item["token"] for item in tokens_data if "token" in item]
    except:
        return jsonify({"error": "token_bd.json নট ফাউন্ড!"}), 500

    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    target = 1000 
    
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)
    
    # সেমাফোর কমিয়ে ৫০ করা হয়েছে যাতে রিকোয়েস্টগুলো লাইন ধরে যায়
    sem = asyncio.Semaphore(50) 

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(target):
            tasks.append(visit_task(session, url, tokens[i % len(tokens)], payload, sem))
        
        results = await asyncio.gather(*tasks)
    
    success = sum(1 for r in results if r)
    return jsonify({
        "status": "Completed",
        "uid": uid,
        "success": success,
        "failed": target - success,
        "note": "সব ফেইল হলে বুঝতে হবে Vercel IP ব্লক করা।"
    })
