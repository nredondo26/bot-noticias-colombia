import json
import os
import requests
from datetime import datetime, timedelta

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
QUEUE_FILE = os.path.join(LOGS_DIR, "queue.json")


def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"articles": [], "last_post_time": None}


def save_queue(queue):
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def add_to_queue(articles):
    queue = load_queue()
    existing_hashes = {a["hash"] for a in queue["articles"]}
    for article in articles:
        key = (article.get("title", "") + article.get("url", "")).lower().strip()
        import hashlib
        h = hashlib.md5(key.encode()).hexdigest()[:16]
        if h not in existing_hashes:
            queue["articles"].append({
                "hash": h,
                "title": article["title"],
                "summary": article.get("summary", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "image_url": article.get("image_url", ""),
                "added_at": datetime.now().isoformat(),
            })
    save_queue(queue)
    return len(queue["articles"])


def get_next_article():
    queue = load_queue()
    if not queue["articles"]:
        return None
    return queue["articles"][0]


def pop_next_article():
    queue = load_queue()
    if not queue["articles"]:
        return None
    article = queue["articles"].pop(0)
    queue["last_post_time"] = datetime.now().isoformat()
    save_queue(queue)
    return article


def queue_size():
    queue = load_queue()
    return len(queue["articles"])


def can_post_now(cooldown_hours=2):
    queue = load_queue()
    if not queue["last_post_time"]:
        return True
    last = datetime.fromisoformat(queue["last_post_time"])
    return datetime.now() - last >= timedelta(hours=cooldown_hours)


def cleanup_old_articles(days=2):
    queue = load_queue()
    cutoff = datetime.now() - timedelta(days=days)
    queue["articles"] = [
        a for a in queue["articles"]
        if datetime.fromisoformat(a["added_at"]) > cutoff
    ]
    save_queue(queue)
