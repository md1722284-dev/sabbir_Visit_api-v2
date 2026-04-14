import asyncio
import aiohttp
import json
from flask import Flask, jsonify
from byte import encrypt_api, Encrypt_ID

app = Flask(__name__)

# সেমাফোর: একসাথে সর্বোচ্চ ৫০০টি রিকোয়েস্ট বের হবে (সার্ভার ভেদে ১০০০ পর্যন্ত করা যায়)
MAX_CONCURRENT_REQUESTS = 500
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0],
        "Connection": "keep-alive" # কানেকশন ধরে রাখার জন্য
    }
    async with semaphore: # সেমাফোর কন্ট্রোল
        try:
            async with session.post(url, headers=headers, data=data, ssl=False, timeout=10) as resp:
                return resp.status == 200
        except:
            return False

async def run_massive_visits(tokens, uid, server_name, target):
    url = get_url(server_name)
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, ttl_dns_cache=300)
    
    # ডেটা একবারই এনক্রিপ্ট করুন (লুপের বাইরে)
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)
    
    total_success = 0
    async with aiohttp.ClientSession(connector=connector) as session:
        # ৫০০০ করে ব্যাচে ভাগ করে কাজ করা (মেমোরি সেভ করার জন্য)
        for i in range(0, target, 5000):
            current_batch_size = min(5000, target - i)
            tasks = []
            
            for j in range(current_batch_size):
                token = tokens[(i + j) % len(tokens)]
                tasks.append(visit(session, url, token, uid, payload))
            
            # ব্যাচ রান করা
            results = await asyncio.gather(*tasks)
            total_success += sum(1 for r in results if r)
            
            print(f"Progress: {total_success}/{target} visits done...")
            
    return total_success

@app.route('/visit/<string:server>/<int:uid>/<int:count>')
async def handle_request(server, uid, count):
    # ১ লাখ ভিজিটের জন্য count প্যারামিটার ব্যবহার করুন
    server = server.upper()
    tokens = load_tokens(server)
    
    if not tokens:
        return jsonify({"error": "No tokens found"}), 500

    # ব্যাকগ্রাউন্ডে কাজ শুরু করা (বড় রিকোয়েস্টের জন্য)
    # নোট: ১ লাখের জন্য এটি কয়েক মিনিট সময় নেবে
    final_success = await run_massive_visits(tokens, uid, server, count)
    
    return jsonify({
        "uid": uid,
        "target": count,
        "success": final_success,
        "status": "Completed"
    })

# টোকেন লোড এবং URL ফাংশন আপনার আগের কোড থেকে এখানে যোগ করবেন
