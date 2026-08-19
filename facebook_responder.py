import requests


def get_post_comments(post_id, access_token):
    url = f"https://graph.facebook.com/v21.0/{post_id}/comments"
    params = {
        "access_token": access_token,
        "fields": "id,message,from,created_time",
        "filter": "stream",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"  Error obteniendo comentarios: {e}")
        return []


def reply_to_comment(comment_id, access_token, message):
    url = f"https://graph.facebook.com/v21.0/{comment_id}/comments"
    data = {"message": message, "access_token": access_token}
    try:
        resp = requests.post(url, data=data, timeout=15)
        result = resp.json()
        if "id" in result:
            return True
        print(f"  Error respondiendo: {result.get('error', {}).get('message', '')}")
        return False
    except Exception as e:
        print(f"  Error respondiendo: {e}")
        return False


def get_recent_posts(page_id, access_token, limit=10):
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"
    params = {"access_token": access_token, "fields": "id,message,created_time", "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=15)
        return resp.json().get("data", [])
    except Exception:
        return []


def generate_reply(api_key, comment_text, post_context=""):
    from ai_analyzer import create_client, _call_gemini
    client = create_client(api_key)

    prompt = f"""Eres el community manager de la pagina "Voz del Pueblo" en Facebook.
Alguien comento en un post de noticias politicas de Colombia:

Comentario: "{comment_text}"
Contexto del post: "{post_context[:200]}"

Genera UNA respuesta corta (maximo 150 caracteres), cordial, que invite al dialogo.
NO seas agresivo. NO respondas hate o spam.
Si el comentario es ofensivo o spam, responde algo neutro como "Gracias por tu comentario".
Devuelve SOLO el texto de la respuesta, sin comillas ni formato."""

    try:
        response = _call_gemini(client, prompt)
        reply = response.text.strip().strip('"').strip("'")
        return reply[:150]
    except Exception:
        return "Gracias por tu comentario. Sigue la pagina para mas noticias."
