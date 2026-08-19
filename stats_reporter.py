import requests
import json
from datetime import datetime


def get_post_stats(post_id, access_token):
    url = f"https://graph.facebook.com/v21.0/{post_id}"
    params = {
        "access_token": access_token,
        "fields": "id,message,likes.summary(true),comments.summary(true),shares,created_time",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        return {
            "post_id": post_id,
            "message": data.get("message", "")[:80],
            "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
            "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
            "shares": data.get("shares", {}).get("count", 0),
            "created_time": data.get("created_time", ""),
        }
    except Exception as e:
        print(f"  Error obteniendo stats: {e}")
        return None


def get_page_stats(page_id, access_token):
    url = f"https://graph.facebook.com/v21.0/{page_id}"
    params = {
        "access_token": access_token,
        "fields": "fan_count,talking_about_count,followers_count",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        return {
            "fans": data.get("fan_count", 0),
            "talking_about": data.get("talking_about_count", 0),
            "followers": data.get("followers_count", 0),
        }
    except Exception:
        return {}


def generate_daily_report(api_key, published_today, page_id, access_token):
    from ai_analyzer import create_client, _call_gemini

    stats = []
    total_likes = 0
    total_comments = 0
    total_shares = 0

    for post in published_today:
        post_id = post.get("post_id", "")
        if not post_id:
            continue
        stat = get_post_stats(post_id, access_token)
        if stat:
            stats.append(stat)
            total_likes += stat["likes"]
            total_comments += stat["comments"]
            total_shares += stat["shares"]

    page_stats = get_page_stats(page_id, access_token)

    report = f"""REPORTE DIARIO - VOZ DEL PUEBLO
Fecha: {datetime.now().strftime('%d/%m/%Y')}
Posts publicados: {len(published_today)}

ESTADISTICAS TOTALES:
  Likes: {total_likes}
  Comentarios: {total_comments}
  Compartidos: {total_shares}
  Seguidores: {page_stats.get('followers', 'N/A')}
  Hablando de ti: {page_stats.get('talking_about', 'N/A')}

MEJORES POSTS:
"""
    stats.sort(key=lambda x: x["likes"] + x["comments"] + x["shares"], reverse=True)
    for i, s in enumerate(stats[:5], 1):
        report += f"  {i}. {s['message']}... (L:{s['likes']} C:{s['comments']} S:{s['shares']})\n"

    return report
