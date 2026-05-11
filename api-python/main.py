from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import redis
import os
import json

app = Flask(__name__)

# Config
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() == "true"

cache = None
if ENABLE_CACHE:
    try:
        cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    except Exception as e:
        print(f"Redis connection failed: {e}")

@app.route("/api/extract")
def extract():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Try cache
    if ENABLE_CACHE and cache:
        cached_data = cache.get(url)
        if cached_data:
            return jsonify(json.loads(cached_data))

    # Extract
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                links.append({"text": link.text.strip(), "href": href})
        
        result = {"url": url, "links": links}

        # Store in cache
        if ENABLE_CACHE and cache:
            cache.set(url, json.dumps(result))

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
