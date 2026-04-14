from flask import Flask, jsonify
import aiohttp
import asyncio
from byte import encrypt_api, Encrypt_ID
# আপনার অন্যান্য ইমপোর্টগুলো ঠিক থাকবে...

app = Flask(__name__)

# একসাথে ১০০টি করে রিকোয়েস্ট প্রসেস হবে (Vercel-এর জন্য পারফেক্ট)
semaphore = asyncio.Semaphore(100)

async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0]
    }
    async with semaphore:
        try:
            # টাইমআউট ৫ সেকেন্ড রাখলে Vercel-এ এরর কম আসবে
            async with session.post(url, headers=headers, data=data, ssl=False, timeout=5) as resp:
                return resp.status == 200
        except:
            return False

@app.route('/<string:server>/<int:uid>')
async def send_visits(server, uid):
    server = server.upper()
    tokens = load_tokens(server) # আপনার টোকেন লোড ফাংশন
    
    if not tokens:
        return jsonify({"error": "No tokens found"}), 500

    target = 1000  # এখানে আমরা ১০০০ লিমিট ফিক্সড করে দিলাম
    url = get_url(server)
    
    # এনক্রিপশন লজিক
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    data = bytes.fromhex(encrypted)

    async with aiohttp.ClientSession() as session:
        # ১০০০টি টাস্ক তৈরি করা হচ্ছে
        tasks = [visit(session, url, tokens[i % len(tokens)], uid, data) for i in range(target)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    
    return jsonify({
        "status": "Success",
        "uid": uid,
        "sent": target,
        "success": success_count,
        "fail": target - success_count
    })
