# -*- coding: utf-8 -*-
"""
Asmary Field Services — Web Dashboard Application
"""
import os
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from scraper import run_scraper

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CACHE_FILE = DATA_DIR / "tenders.json"

# State tracking for scanning
scan_status = {
    "is_scanning": False,
    "current_page": 0,
    "total_pages": 50,
    "total_scanned": 0,
    "last_completed": None,
    "error": None
}

def load_cached_data():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"tenders": [], "last_updated": None, "total_scanned": 0}
    return {"tenders": [], "last_updated": None, "total_scanned": 0}

def save_data(data):
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def background_scan_job(pages=50):
    global scan_status
    scan_status["is_scanning"] = True
    scan_status["current_page"] = 0
    scan_status["total_pages"] = pages
    scan_status["error"] = None

    def on_progress(current, total, total_found):
        scan_status["current_page"] = current
        scan_status["total_pages"] = total
        scan_status["total_scanned"] = total_found

    try:
        results = run_scraper(pages_to_scan=pages, progress_callback=on_progress)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        save_payload = {
            "last_updated": timestamp,
            "total_scanned_notices": results["total_scanned_notices"],
            "pages_scanned": results["pages_scanned"],
            "matched_count": results["matched_count"],
            "tenders": results["tenders"]
        }
        save_data(save_payload)
        scan_status["last_completed"] = timestamp
    except Exception as e:
        scan_status["error"] = str(e)
    finally:
        scan_status["is_scanning"] = False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/tenders")
def get_tenders():
    data = load_cached_data()
    return jsonify(data)

@app.route("/api/status")
def get_status():
    return jsonify(scan_status)

@app.route("/api/scan", methods=["POST"])
def trigger_scan():
    global scan_status
    if scan_status["is_scanning"]:
        return jsonify({"success": False, "message": "اسکن در حال اجرا است."}), 400

    pages = request.json.get("pages", 50) if request.is_json else 50
    thread = threading.Thread(target=background_scan_job, args=(pages,))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True, "message": f"اسکن {pages} صفحه آغاز شد."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
