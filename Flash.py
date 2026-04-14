from flask import Flask, jsonify, request
import aiohttp
import asyncio
import json
from byte import encrypt_api, Encrypt_ID
from visit_count_pb2 import Info

app = Flask(__name__)

# টোকেন লোড করার ফাংশন (আপনার আগের লজিক অনুযায়ী)
def load_tokens(server_name):
    try:
        path = "token_ind.json" if server_name == "IND" else "token_br.json" if server_name in {"BR", "US", "SAC", "NA"} else "token_bd.json"
        with open(path, "r") as f:
            data = json.load(f)
        return [item["token"] for item in data if "token" in item and item["token"] not in ["", "N/A"]]
    except Exception:
        return []

def get_url(server_name):
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

# ভিজিট পাঠানোর মূল ফাংশন
async def visit(session, url, token, uid, data, sem):
    headers = {
        "ReleaseVersion": "OB53",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0],
        "Connection": "keep-alive"
    }
    async with sem:
        try:
            async with session.post(url, headers=headers, data=data, ssl=False, timeout=10) as resp:
                return resp.status == 200
        except:
            return False

@app.route('/<string:server>/<int:uid>')
async def send_visits(server, uid):
    server = server.upper()
    tokens = load_tokens(server)
    
    if not tokens:
        return jsonify({"error": "No tokens found"}), 500

    target = 1000  # ১০০০ লিমিট
    url = get_url(server)
    
    # এনক্রিপশন একবারই করা হচ্ছে
    encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
    payload = bytes.fromhex(encrypted)
    
    # সেমাফোর দিয়ে কনকারেন্সি কন্ট্রোল
    sem = asyncio.Semaphore(100) 

    async with aiohttp.ClientSession() as session:
        tasks = [visit(session, url, tokens[i % len(tokens)], uid, payload, sem) for i in range(target)]
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r)
    
    return jsonify({
        "status": "Success",
        "uid": uid,
        "success": success_count,
        "failed": target - success_count
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5100)
