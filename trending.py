import requests
import re


def get_trending_hashtags(country="Colombia"):
    hashtags = set()

    try:
        resp = requests.get(
            "https://trends.google.com/trending?geo=CO&hours=24",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        text = resp.text
        found = re.findall(r'#(\w+)', text)
        hashtags.update(h.lower() for h in found if len(h) > 3 and not re.match(r'^[0-9a-f]{3,8}$', h))
    except Exception:
        pass

    try:
        resp = requests.get(
            "https://twstalker.com/trending/colombia",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        found = re.findall(r'#(\w+)', resp.text)
        hashtags.update(h.lower() for h in found if len(h) > 3 and not re.match(r'^[0-9a-f]{3,8}$', h))
    except Exception:
        pass

    always_used = [
        "colombia", "politica", "noticias", "gobierno",
        "colombianos", "pueblo", "reforma", "justicia",
    ]
    hashtags.update(always_used)

    return list(hashtags)[:15]


def pick_relevant_hashtags(text, available_hashtags, min_hashtags=3, max_hashtags=5):
    text_lower = text.lower()
    scored = []
    for tag in available_hashtags:
        if tag in text_lower:
            scored.append((tag, 3))
        else:
            scored.append((tag, 1))

    scored.sort(key=lambda x: x[1], reverse=True)
    result = [f"#{tag}" for tag, _ in scored[:max_hashtags]]

    fallback = ["noticias", "colombia", "actualidad", "politica", "pueblo"]
    for fb in fallback:
        if len(result) >= min_hashtags:
            break
        tag_str = f"#{fb}"
        if tag_str not in result:
            result.append(tag_str)

    return result
