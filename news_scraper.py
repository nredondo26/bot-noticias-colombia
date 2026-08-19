import feedparser
import requests
import re
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup


def build_google_news_url(query, language="es-419", country="CO"):
    encoded = quote_plus(query)
    return (
        f"https://news.google.com/rss/search?q={encoded}+when:1d"
        f"&hl={language}&gl={country}&ceid={country}:{language.split('-')[0]}"
    )


def clean_html(html_text):
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def extract_image_from_entry(entry):
    media = entry.get("media_content", [])
    if media and isinstance(media, list):
        url = media[0].get("url", "")
        if url:
            return url

    media_thumb = entry.get("media_thumbnail", [])
    if media_thumb and isinstance(media_thumb, list):
        url = media_thumb[0].get("url", "")
        if url:
            return url

    enclosures = entry.get("enclosures", [])
    for enc in enclosures:
        if enc.get("type", "").startswith("image"):
            return enc.get("href", "")

    content_html = entry.get("content", [{}])
    if isinstance(content_html, list) and content_html:
        html_text = content_html[0].get("value", "")
    else:
        html_text = str(content_html)
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html_text)
    if match:
        return match.group(1)

    return ""


def fetch_news(queries, language="es-419", country="CO", max_articles=30):
    all_articles = []
    seen_titles = set()

    for query in queries:
        url = build_google_news_url(query, language, country)
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                title_lower = title.lower()

                skip = False
                for seen in seen_titles:
                    if seen in title_lower or title_lower in seen:
                        skip = True
                        break
                if skip:
                    continue

                summary = clean_html(entry.get("summary", ""))
                if len(summary) < 30:
                    continue

                published = entry.get("published", "")
                source_url = entry.get("link", "")
                image_url = extract_image_from_entry(entry)

                article = {
                    "title": title,
                    "summary": summary,
                    "url": source_url,
                    "source": entry.get("source", {}).get("title", "Google News"),
                    "published": published,
                    "query": query,
                    "image_url": image_url,
                }

                all_articles.append(article)
                seen_titles.add(title_lower)
                time.sleep(0.3)

        except Exception as e:
            print(f"  Error buscando '{query}': {e}")
            continue

    all_articles.sort(key=lambda x: len(x.get("summary", "")), reverse=True)
    return all_articles[:max_articles]


def get_trending_news(queries=None, language="es-419", country="CO", max_articles=30):
    from config import NEWS_QUERIES

    if queries is None:
        queries = NEWS_QUERIES

    print(f"Buscando noticias en {len(queries)} fuentes...")
    articles = fetch_news(queries, language, country, max_articles)
    print(f"Se encontraron {len(articles)} noticias unicas.")
    return articles


if __name__ == "__main__":
    articles = get_trending_news()
    for i, a in enumerate(articles, 1):
        print(f"\n--- Noticia {i} ---")
        print(f"Titulo: {a['title']}")
        print(f"Fuente: {a['source']}")
        print(f"Resumen: {a['summary'][:150]}...")
