import os
import sys
import json
import hashlib
import logging
from datetime import datetime

from config import (
    GEMINI_API_KEY, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN,
    NEWS_COUNTRY, NEWS_LANGUAGE, NEWS_MAX_ARTICLES,
    ASSETS_DIR, LOGS_DIR,
)
from news_scraper import get_trending_news
from ai_analyzer import create_post_for_article
from image_handler import get_image_for_post
from facebook_poster import post_to_facebook, verify_token
from post_queue import add_to_queue, pop_next_article, queue_size, can_post_now, cleanup_old_articles
from facebook_responder import get_post_comments, reply_to_comment, get_recent_posts, generate_reply
from trending import get_trending_hashtags, pick_relevant_hashtags
from stats_reporter import generate_daily_report

PUBLISHED_FILE = os.path.join(LOGS_DIR, "published.json")
RESPONDED_FILE = os.path.join(LOGS_DIR, "responded_comments.json")


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOGS_DIR, f"{today}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_published():
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"published": []}


def save_published(data):
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def article_hash(article):
    key = (article.get("title", "") + article.get("url", "")).lower().strip()
    return hashlib.md5(key.encode()).hexdigest()[:16]


def is_published(article, history):
    h = article_hash(article)
    return h in [p["hash"] for p in history.get("published", [])]


def mark_published(article, post_id, history):
    h = article_hash(article)
    history["published"].append({
        "hash": h,
        "title": article["title"][:100],
        "url": article.get("url", ""),
        "post_id": post_id,
        "timestamp": datetime.now().isoformat(),
    })


def load_responded():
    if os.path.exists(RESPONDED_FILE):
        with open(RESPONDED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"responded": []}


def save_responded(data):
    with open(RESPONDED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_news_and_fill_queue(logger):
    logger.info("Buscando noticias nuevas...")
    articles = get_trending_news(language=NEWS_LANGUAGE, country=NEWS_COUNTRY, max_articles=20)

    if not articles:
        logger.warning("No se encontraron noticias.")
        return

    history = load_published()
    new_articles = [a for a in articles if not is_published(a, history)]

    if not new_articles:
        logger.info("No hay noticias nuevas para agregar a la cola.")
        return

    added = add_to_queue(new_articles)
    logger.info(f"  Cola actual: {added} noticias pendientes")


def post_one_article(logger):
    if not can_post_now(cooldown_hours=2):
        logger.info("Cooldown activo. Esperando 2 horas entre posts.")
        return False

    article = pop_next_article()
    if not article:
        logger.info("Cola vacia. Buscando mas noticias...")
        fetch_news_and_fill_queue(logger)
        article = pop_next_article()
        if not article:
            logger.warning("No hay noticias disponibles.")
            return False

    logger.info(f"Publicando: {article['title'][:80]}")

    page_token, real_page_id = verify_token(FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN)
    if not page_token:
        logger.error("Token invalido.")
        return False

    logger.info("  Generando post...")
    post_data = create_post_for_article(GEMINI_API_KEY, article, "", 800)

    hashtags = get_trending_hashtags()
    post_hashtags = pick_relevant_hashtags(post_data["texto"], hashtags, 5)
    if post_hashtags:
        post_data["texto"] += "\n\n" + " ".join(post_hashtags)

    logger.info("  Buscando imagen...")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(ASSETS_DIR, f"post_{today_str}.jpg")

    result_image = get_image_for_post(
        [article],
        post_data["imagen_keywords"],
        image_path,
        overlay_text=post_data["titulo"][:60],
    )

    logger.info("  Publicando en Facebook...")
    fb_result = post_to_facebook(real_page_id, page_token, post_data["texto"], result_image)

    if os.path.exists(image_path):
        os.remove(image_path)

    if fb_result["success"]:
        logger.info(f"  PUBLICADO! ID: {fb_result['post_id']}")
        history = load_published()
        mark_published(article, fb_result["post_id"], history)
        save_published(history)
        return True
    else:
        logger.error(f"  Error: {fb_result.get('error', '')}")
        return False


def auto_reply_comments(logger):
    logger.info("Verificando comentarios para responder...")
    page_token, real_page_id = verify_token(FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN)
    if not page_token:
        return

    posts = get_recent_posts(real_page_id, page_token, limit=5)
    responded = load_responded()

    for post in posts:
        post_id = post["id"]
        comments = get_post_comments(post_id, page_token)
        for comment in comments:
            comment_id = comment["id"]
            if comment_id in responded.get("responded", []):
                continue
            msg = comment.get("message", "")
            if not msg or len(msg) < 5:
                continue
            if comment.get("from", {}).get("id") == real_page_id:
                continue

            reply_text = generate_reply(GEMINI_API_KEY, msg, post.get("message", ""))
            if reply_text:
                success = reply_to_comment(comment_id, page_token, reply_text)
                if success:
                    responded.setdefault("responded", []).append(comment_id)
                    logger.info(f"  Respondido a '{msg[:40]}...': {reply_text[:50]}")

    save_responded(responded)


def send_daily_report(logger):
    logger.info("Generando reporte diario...")
    page_token, real_page_id = verify_token(FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN)
    if not page_token:
        return

    history = load_published()
    today = datetime.now().strftime("%Y-%m-%d")
    published_today = [
        p for p in history.get("published", [])
        if p.get("timestamp", "").startswith(today)
    ]

    if not published_today:
        logger.info("No hubo posts hoy. Saltando reporte.")
        return

    report = generate_daily_report(GEMINI_API_KEY, published_today, real_page_id, page_token)
    logger.info(f"\n{report}")

    post_to_facebook(real_page_id, page_token, report)
    logger.info("Reporte publicado en la pagina.")


def run(mode="single", dry_run=False):
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("BOT DE NOTICIAS FACEBOOK - VOZ DEL PUEBLO")
    logger.info(f"Modo: {mode}")
    logger.info("=" * 60)

    if mode == "fetch":
        fetch_news_and_fill_queue(logger)
        return True

    if mode == "reply":
        auto_reply_comments(logger)
        return True

    if mode == "report":
        send_daily_report(logger)
        return True

    if mode == "single":
        cleanup_old_articles()
        if queue_size() < 3:
            fetch_news_and_fill_queue(logger)
        success = post_one_article(logger)
        auto_reply_comments(logger)
        return success

    if mode == "full":
        cleanup_old_articles()
        fetch_news_and_fill_queue(logger)
        posted = 0
        for i in range(10):
            if queue_size() == 0:
                fetch_news_and_fill_queue(logger)
            if queue_size() == 0:
                break
            if posted > 0 and not can_post_now(cooldown_hours=0):
                import time
                time.sleep(5)
            if post_one_article(logger):
                posted += 1
        auto_reply_comments(logger)
        logger.info(f"Total publicados: {posted}")
        return posted > 0

    return False


if __name__ == "__main__":
    mode = "single"
    dry_run = False

    for arg in sys.argv[1:]:
        if arg == "--full":
            mode = "full"
        elif arg == "--fetch":
            mode = "fetch"
        elif arg == "--reply":
            mode = "reply"
        elif arg == "--report":
            mode = "report"
        elif arg == "--dry-run":
            dry_run = True

    success = run(mode=mode, dry_run=dry_run)
    sys.exit(0 if success else 1)
