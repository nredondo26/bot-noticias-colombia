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

POSTS_PER_RUN = 5
PUBLISHED_FILE = os.path.join(LOGS_DIR, "published.json")


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


def validate_config():
    errors = []
    if "TU_GEMINI_API_KEY_AQUI" in GEMINI_API_KEY or not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY no configurada")
    if "TU_PAGE_ID_AQUI" in FACEBOOK_PAGE_ID or not FACEBOOK_PAGE_ID:
        errors.append("FACEBOOK_PAGE_ID no configurado")
    if "TU_PAGE_ACCESS_TOKEN_AQUI" in FACEBOOK_PAGE_ACCESS_TOKEN or not FACEBOOK_PAGE_ACCESS_TOKEN:
        errors.append("FACEBOOK_PAGE_ACCESS_TOKEN no configurado")
    return errors


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


def run(dry_run=False):
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("INICIANDO BOT DE NOTICIAS FACEBOOK")
    logger.info("=" * 60)

    errors = validate_config()
    if errors:
        for e in errors:
            logger.error(f"CONFIG: {e}")
        return False

    logger.info("Paso 1: Buscando noticias...")
    articles = get_trending_news(language=NEWS_LANGUAGE, country=NEWS_COUNTRY, max_articles=20)

    if not articles:
        logger.warning("No se encontraron noticias. Abortando.")
        return False

    history = load_published()

    new_articles = [a for a in articles if not is_published(a, history)]

    if not new_articles:
        logger.warning("Todas las noticias ya fueron publicadas anteriormente.")
        return False

    to_post = new_articles[:POSTS_PER_RUN]
    logger.info(f"  {len(new_articles)} noticias nuevas. Publicando {len(to_post)} posts.")

    for i, a in enumerate(to_post, 1):
        logger.info(f"  {i}. {a['title'][:80]} ({a['source']})")

    logger.info("Paso 2: Verificando token de Facebook...")
    page_token, real_page_id = verify_token(FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN)
    if not page_token:
        logger.error("Token de Facebook invalido. Abortando.")
        return False

    os.makedirs(ASSETS_DIR, exist_ok=True)
    published_count = 0

    for i, article in enumerate(to_post, 1):
        logger.info(f"\n--- Post {i}/{len(to_post)} ---")
        logger.info(f"  Noticia: {article['title'][:80]}")

        logger.info("  Generando post con Gemini...")
        post_data = create_post_for_article(GEMINI_API_KEY, article, "", 500)
        logger.info(f"  Texto: {post_data['texto'][:80]}...")

        logger.info("  Buscando imagen...")
        today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(ASSETS_DIR, f"post_{today_str}_{i}.jpg")

        result_image = get_image_for_post(
            [article],
            post_data["imagen_keywords"],
            image_path,
            overlay_text=post_data["titulo"][:60],
        )

        if dry_run:
            logger.info(f"  [DRY-RUN] Post generado:")
            logger.info(f"  {post_data['texto'][:150]}...")
            if os.path.exists(image_path):
                os.remove(image_path)
            continue

        logger.info("  Publicando en Facebook...")
        fb_result = post_to_facebook(
            real_page_id,
            page_token,
            post_data["texto"],
            result_image,
        )

        if fb_result["success"]:
            logger.info(f"  PUBLICADO! ID: {fb_result['post_id']}")
            mark_published(article, fb_result["post_id"], history)
            save_published(history)
            published_count += 1
        else:
            logger.error(f"  Error: {fb_result.get('error', 'Desconocido')}")

        if os.path.exists(image_path):
            os.remove(image_path)

    if dry_run:
        logger.info(f"\n[DRY-RUN] {len(to_post)} posts generados (no publicados).")
    else:
        logger.info(f"\nPublicados {published_count}/{len(to_post)} posts exitosamente.")

    logger.info("Bot finalizado.")
    return published_count > 0


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv or "--prueba" in sys.argv
    if dry_run:
        print("Modo PRUEBA activado.\n")
    success = run(dry_run=dry_run)
    sys.exit(0 if success else 1)
