"""
ResellRadar Ingestion Control Server (FastAPI)
Provides REST & SSE API endpoints for Scraper triggers, live telemetry metrics,
raw data stream queries, and HDFS sync orchestration.
"""

import asyncio
import datetime
import json
import os
import threading
import time
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper.generator import generate_batch, generate_listing
from hdfs_uploader import HDFSUploader

app = FastAPI(title="ResellRadar Data Ingestion API", version="2.8.4")

# Enable CORS for Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Telemetry & Pipeline State
PIPELINE_STATE = {
    "is_running": False,
    "pid": None,
    "category": "all",
    "batch_target": 500,
    "scraped_count": 0,
    "scrapes_per_sec": 0.0,
    "active_threads": 0,
    "success_rate": 99.41,
    "last_run_timestamp": None,
    "current_job_id": None,
    "logs": [
        {"timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S.%f")[:-3], "level": "INFO", "message": "ResellRadar Data Ingestion Control Daemon initialized."},
        {"timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S.%f")[:-3], "level": "INFO", "message": "HDFS cluster listener ready on /data/raw/."}
    ]
}

job_stop_event = threading.Event()
hdfs_uploader = HDFSUploader()

def add_log(level: str, message: str):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    entry = {"timestamp": ts, "level": level, "message": message}
    PIPELINE_STATE["logs"].append(entry)
    if len(PIPELINE_STATE["logs"]) > 200:
        PIPELINE_STATE["logs"].pop(0)

class ScrapeTriggerRequest(BaseModel):
    category: str = "all"
    batch_target: int = 500
    concurrency_threads: int = 16

def run_background_job(category: str, target: int, threads: int):
    global PIPELINE_STATE
    PIPELINE_STATE["is_running"] = True
    PIPELINE_STATE["pid"] = os.getpid()
    PIPELINE_STATE["category"] = category
    PIPELINE_STATE["batch_target"] = target
    PIPELINE_STATE["active_threads"] = threads
    job_stop_event.clear()

    add_log("INFO", f"Job STARTED. Category: '{category}', Target: {target:,} listings, Workers: {threads}.")
    
    start_time = time.time()
    batch_size = min(100, target)
    collected = 0

    while collected < target and not job_stop_event.is_set():
        chunk = min(100, target - collected)
        time.sleep(0.15) # simulate high-speed streaming batch
        
        # Write batch file
        fname = generate_batch(count=chunk, category=category, output_dir="data/raw")
        collected += chunk
        
        elapsed = time.time() - start_time
        speed = round(collected / max(0.1, elapsed), 1)
        
        PIPELINE_STATE["scraped_count"] += chunk
        PIPELINE_STATE["scrapes_per_sec"] = speed
        PIPELINE_STATE["last_run_timestamp"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if collected % 500 == 0 or collected >= target:
            add_log("ACK", f"Scraped batch of {collected:,}/{target:,} listings ({speed} req/s). Saved to {fname}.")

    if job_stop_event.is_set():
        add_log("WARN", f"Job HALTED by user at {collected:,} listings.")
    else:
        add_log("SUCCESS", f"Job COMPLETED successfully. Total {target:,} listings exported to data/raw/.")

    PIPELINE_STATE["is_running"] = False
    PIPELINE_STATE["active_threads"] = 0
    PIPELINE_STATE["scrapes_per_sec"] = 0.0

@app.get("/api/status")
def get_status():
    hdfs_conn = hdfs_uploader.check_hdfs_connection()
    manifest = hdfs_uploader.sync_manifest

    # Total listings count in raw directory
    total_raw_listings = 0
    raw_dir = "data/raw"
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.endswith(".json"):
                fpath = os.path.join(raw_dir, f)
                try:
                    with open(fpath, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                        if isinstance(data, list):
                            total_raw_listings += len(data)
                except Exception:
                    pass

    return {
        "pipeline_state": PIPELINE_STATE,
        "raw_storage": {
            "total_listings_scraped": max(total_raw_listings, PIPELINE_STATE["scraped_count"]),
            "raw_files_count": len([f for f in os.listdir(raw_dir) if f.endswith(".json")]) if os.path.exists(raw_dir) else 0,
            "raw_path": os.path.abspath(raw_dir)
        },
        "hdfs_telemetry": {
            "status": hdfs_conn["status"],
            "type": hdfs_conn["type"],
            "endpoint": hdfs_conn["endpoint"],
            "hdfs_path": hdfs_uploader.hdfs_path,
            "pushed_files_count": len(manifest.get("pushed_files", [])),
            "total_bytes_pushed": manifest.get("total_bytes_pushed", 0),
            "last_sync_timestamp": manifest.get("last_sync_timestamp")
        }
    }

@app.post("/api/scrape/trigger")
def trigger_scrape(req: ScrapeTriggerRequest, background_tasks: BackgroundTasks):
    if PIPELINE_STATE["is_running"]:
        return {"status": "ERROR", "message": "Scrape pipeline is already running."}
    
    background_tasks.add_task(run_background_job, req.category, req.batch_target, req.concurrency_threads)
    return {"status": "ACCEPTED", "message": f"Scrape job initiated for {req.batch_target:,} {req.category} listings."}

@app.post("/api/scrape/stop")
def stop_scrape():
    if not PIPELINE_STATE["is_running"]:
        return {"status": "INFO", "message": "No active scrape job running."}
    job_stop_event.set()
    return {"status": "SUCCESS", "message": "Stop signal sent to worker daemons."}

@app.get("/api/preview")
def preview_data(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None
):
    raw_dir = "data/raw"
    all_items = []

    if os.path.exists(raw_dir):
        files = sorted([os.path.join(raw_dir, f) for f in os.listdir(raw_dir) if f.endswith(".json")], key=os.path.getmtime, reverse=True)
        for fpath in files[:10]: # Read from recent 10 files
            try:
                with open(fpath, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        all_items.extend(data)
            except Exception:
                pass

    # Filter
    filtered = []
    for item in all_items:
        if category and category.lower() != "all" and category.lower() not in item.get("category", "").lower():
            continue
        if source and source.lower() != "all" and source.lower() not in item.get("source_platform", "").lower():
            continue
        if search:
            q = search.lower()
            t = item.get("title", "").lower()
            d = item.get("description", "").lower()
            c = item.get("location_city", "").lower()
            if q not in t and q not in d and q not in c:
                continue
        filtered.append(item)

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = filtered[start_idx:end_idx]

    return {
        "total": len(filtered),
        "page": page,
        "limit": limit,
        "items": paginated_items
    }

@app.post("/api/hdfs/sync")
def sync_hdfs():
    res = hdfs_uploader.sync_to_hdfs()
    add_log("ACK", f"HDFS Sync completed ({res['files_pushed_count']} files pushed, {res['bytes_pushed']:,} bytes).")
    return res

@app.get("/api/logs")
def get_logs():
    return {"logs": PIPELINE_STATE["logs"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
