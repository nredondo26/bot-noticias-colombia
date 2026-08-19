import json
import re
import time
from google import genai
from google.genai import types


def create_client(api_key):
    return genai.Client(api_key=api_key)


POST_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "titulo": types.Schema(type=types.Type.STRING, description="Titulo corto del post"),
        "texto": types.Schema(type=types.Type.STRING, description="Texto completo del post con emojis y hashtags"),
        "imagen_keywords": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(type=types.Type.STRING),
            description="3 palabras clave para buscar imagen",
        ),
    },
    required=["titulo", "texto", "imagen_keywords"],
)


def _call_gemini(client, prompt, structured=False, retries=3, delay=10):
    for attempt in range(retries):
        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
            if structured:
                config.response_mime_type = "application/json"
                config.response_schema = POST_SCHEMA

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=config,
            )
            return response

        except Exception as e:
            is_overload = '503' in str(e) or 'UNAVAILABLE' in str(e).upper()
            if is_overload and attempt < retries - 1:
                wait = delay * (attempt + 1)
                print(f"  Gemini sobrecargado. Reintento {attempt+1}/{retries} en {wait}s...")
                time.sleep(wait)
            else:
                raise


def _normalize_post(data):
    if not isinstance(data, dict):
        return None

    titulo = data.get("titulo") or data.get("title") or data.get("headline") or ""
    texto = data.get("texto") or data.get("text") or data.get("post") or data.get("content") or data.get("mensaje") or ""
    keywords = data.get("imagen_keywords") or data.get("keywords") or data.get("image_keywords") or []

    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",")]

    if not titulo and texto:
        first_line = texto.split("\n")[0]
        if len(first_line) < 80:
            titulo = first_line

    if titulo and texto:
        return {
            "titulo": str(titulo),
            "texto": str(texto),
            "imagen_keywords": [str(k) for k in keywords] if keywords else ["Colombia", "politica", "gobierno"],
        }
    return None


def analyze_and_create_post(client, articles, style_prompt, max_length=500):
    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += (
            f"\n--- Noticia {i} ---\n"
            f"Titulo: {a['title']}\n"
            f"Fuente: {a['source']}\n"
            f"Resumen: {a['summary']}\n"
        )

    prompt = f"""{style_prompt}

A continuacion te presento {len(articles)} noticias recientes de Colombia.
Analiza las mas relevantes y crea UN SOLO post de Facebook que analice
las 3-5 noticias mas importantes, conectandolas entre si si es posible.

REGLAS:
- El post debe tener entre 200 y {max_length} caracteres
- Incluye emojis con moderacion (3-5 maximo)
- Incluye 3-5 hashtags al final
- Tono: analitico, cercano al pueblo, sin ser agresivo
- Las imagen_keywords deben ser palabras en espanol para buscar imagenes

NOTICIAS:
{articles_text}"""

    try:
        response = _call_gemini(client, prompt, structured=True)
        result = json.loads(response.text)
        normalized = _normalize_post(result)
        if normalized:
            return normalized
    except Exception as e:
        print(f"  Gemini structured output fallo: {e}")

    try:
        response = _call_gemini(client, prompt + "\n\nDevuelve un JSON con campos: titulo, texto, imagen_keywords.")
        result = _parse_any_json(response.text)
        if result:
            normalized = _normalize_post(result)
            if normalized:
                return normalized
    except Exception as e:
        print(f"  Gemini fallback tambien fallo: {e}")

    return _local_fallback(articles)


def _local_fallback(articles):
    if not articles:
        return {
            "titulo": "Analisis Politico del Dia",
            "texto": "No se encontraron noticias recientes para analizar.",
            "imagen_keywords": ["Colombia", "politica"],
        }

    headlines = [a["title"] for a in articles[:5]]
    main = articles[0]

    keyword_pool = []
    for a in articles:
        for w in a["title"].split():
            if len(w) > 4 and w.lower() not in ("para", "como", "desde", "sobre", "entre", "otros", "otras", "este", "esta", "pero", "mas", "con", "una", "por", "que", "del", "las", "los", "una", "uno", "hay", "fue", "ser", "han", "estan", "hizo", "sido", "tiene", "van", "puede", "hoy", "ayer", "nuevo", "nueva", "todos", "toda"):
                keyword_pool.append(w.strip(".,;:!?()¿¡\"'"))
    top_keywords = list(dict.fromkeys(keyword_pool))[:3]
    if len(top_keywords) < 3:
        top_keywords.extend(["Colombia", "politica", "gobierno"][: 3 - len(top_keywords)])

    summary_lines = []
    for i, h in enumerate(headlines[:3], 1):
        summary_lines.append(f"{i}. {h}")

    titulo = f"Noticias del Dia: {main['source']}"
    texto = (
        f"Colombia vive momentos importantes. Te compartimos los titulares del dia:\n\n"
        + "\n".join(summary_lines)
        + "\n\nSeguiremos informando para que la gente comun tenga acceso a la informacion. "
        "Que piensas tu? Dejanos tu opinion en los comentarios."
        "\n\n#Colombia #PoliticaColombia #NoticiasColombia #GobiernoColombia"
    )

    return {
        "titulo": titulo,
        "texto": texto,
        "imagen_keywords": top_keywords,
    }


def _local_fallback_single(article):
    title = article["title"]
    source = article.get("source", "Fuente")
    summary = article.get("summary", "")[:150]

    keyword_pool = []
    for w in title.split():
        if len(w) > 4 and w.lower() not in ("para", "como", "desde", "sobre", "entre", "mas", "con", "una", "por", "que", "del", "las", "los"):
            keyword_pool.append(w.strip(".,;:!?()¿¡\"'"))
    keywords = list(dict.fromkeys(keyword_pool))[:3]
    if len(keywords) < 3:
        keywords.extend(["Colombia", "politica", "gobierno"][: 3 - len(keywords)])

    texto = f"{title}\n\n{summary}\n\nQue opinas? Dejanos tu comentario 👇\n\n#Colombia #PoliticaColombia #NoticiasColombia"

    return {
        "titulo": title[:80],
        "texto": texto[:500],
        "imagen_keywords": keywords,
    }


def _parse_any_json(text):
    raw = text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    normalized = raw.replace("\\n", "\n").replace('\\"', '"').replace('\\\\', '\\')

    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', normalized, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None


def create_single_post(api_key, articles):
    from config import POST_STYLE, POST_MAX_LENGTH
    client = create_client(api_key)
    return analyze_and_create_post(client, articles, POST_STYLE, POST_MAX_LENGTH)


def create_post_for_article(api_key, article, style_prompt="", max_length=500):
    from config import POST_STYLE, POST_MAX_LENGTH
    if not style_prompt:
        style_prompt = POST_STYLE
    client = create_client(api_key)

    prompt = f"""{style_prompt}

Escribe UN SOLO post de Facebook para esta noticia:

Titulo: {article['title']}
Fuente: {article['source']}
Resumen: {article['summary']}

REGLAS:
- El post debe tener entre 400 y 800 caracteres. NO seas corto, escribe un analisis completo.
- Si la noticia viene de una pagina o medio especifico, mencionalo y referencia la fuente.
- Escribe como si le hablaras a la gente del pueblo, con contexto y opinion.
- Incluye emojis con moderacion (3-5 maximo)
- Incluye 3-5 hashtags relevantes al final
- Tono: analitico, cercano al pueblo, sin ser agresivo
- imagen_keywords: 3 palabras en espanol relacionadas con la noticia
- NO inventes informacion. Solo comenta lo que dice la noticia.
- Si es sobre corrupcion o algo negativo, pide reflexion a los seguidores.
- Si hay datos o cifras, mencionalos.
- Cierra con una pregunta o invitacion al debate."""

    try:
        response = _call_gemini(client, prompt, structured=True)
        result = json.loads(response.text)
        normalized = _normalize_post(result)
        if normalized:
            return normalized
    except Exception as e:
        print(f"  Gemini fallo para '{article['title'][:40]}': {e}")

    return _local_fallback_single(article)


if __name__ == "__main__":
    from config import GEMINI_API_KEY
    from news_scraper import get_trending_news

    articles = get_trending_news(max_articles=5)
    if articles:
        result = create_single_post(GEMINI_API_KEY, articles)
        print("\n=== POST GENERADO ===")
        print(f"Titulo: {result['titulo']}")
        print(f"Texto: {result['texto']}")
        print(f"Keywords imagen: {result['imagen_keywords']}")
