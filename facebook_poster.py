import os
import requests
import json


def ensure_page_token(page_id, token):
    url = f"https://graph.facebook.com/v21.0/me/accounts"
    params = {"access_token": token}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        pages = data.get("data", [])
        if pages:
            for p in pages:
                if str(p["id"]) == str(page_id):
                    print(f"  Token de pagina obtenido: {p['name']}")
                    return p["access_token"], page_id
            p = pages[0]
            print(f"  Usando pagina: {p['name']} (ID: {p['id']})")
            return p["access_token"], p["id"]
        else:
            url2 = f"https://graph.facebook.com/v21.0/me"
            params2 = {"access_token": token, "fields": "id,name"}
            resp2 = requests.get(url2, params=params2, timeout=10)
            info = resp2.json()
            if "name" in info:
                print(f"  Token de usuario valido: {info['name']}")
                return token, page_id
            return None, None
    except Exception as e:
        print(f"  No se pudo intercambiar token: {e}")
        return None, None


def post_to_facebook(page_id, access_token, message, image_path=None):
    access_token, page_id = ensure_page_token(page_id, access_token)

    if image_path and os.path.exists(image_path):
        return post_with_image(page_id, access_token, message, image_path)
    else:
        return post_text_only(page_id, access_token, message)


def post_with_image(page_id, access_token, message, image_path):
    url = f"https://graph.facebook.com/v21.0/{page_id}/photos"

    with open(image_path, "rb") as img_file:
        files = {"source": img_file}
        data = {
            "message": message,
            "access_token": access_token,
        }

        try:
            resp = requests.post(url, data=data, files=files, timeout=60)
            result = resp.json()

            if "id" in result:
                print(f"  Post publicado con imagen. ID: {result['id']}")
                return {"success": True, "post_id": result["id"], "type": "photo"}
            else:
                error_msg = result.get("error", {}).get("message", "Error desconocido")
                error_code = result.get("error", {}).get("code", 0)
                print(f"  Error al publicar: [{error_code}] {error_msg}")
                return {"success": False, "error": error_msg, "error_code": error_code}

        except Exception as e:
            print(f"  Excepcion al publicar: {e}")
            return {"success": False, "error": str(e)}


def post_text_only(page_id, access_token, message):
    url = f"https://graph.facebook.com/v21.0/{page_id}/feed"

    data = {
        "message": message,
        "access_token": access_token,
    }

    try:
        resp = requests.post(url, data=data, timeout=30)
        result = resp.json()

        if "id" in result:
            print(f"  Post de texto publicado. ID: {result['id']}")
            return {"success": True, "post_id": result["id"], "type": "text"}
        else:
            error_msg = result.get("error", {}).get("message", "Error desconocido")
            error_code = result.get("error", {}).get("code", 0)
            print(f"  Error al publicar: [{error_code}] {error_msg}")
            return {"success": False, "error": error_msg, "error_code": error_code}

    except Exception as e:
        print(f"  Excepcion al publicar: {e}")
        return {"success": False, "error": str(e)}


def verify_token(page_id, access_token):
    access_token, real_page_id = ensure_page_token(page_id, access_token)

    url = f"https://graph.facebook.com/v21.0/{real_page_id}"
    params = {"access_token": access_token, "fields": "name,id"}

    try:
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json()

        if "name" in result:
            print(f"  Token valido para pagina: {result['name']} (ID: {result['id']})")
            return access_token, real_page_id
        else:
            error_msg = result.get("error", {}).get("message", "Token invalido")
            print(f"  Token invalido: {error_msg}")
            return None, None

    except Exception as e:
        print(f"  Error verificando token: {e}")
        return None, None


if __name__ == "__main__":
    from config import FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN

    print("Verificando token de Facebook...")
    valid = verify_token(FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN)

    if valid:
        print("\nPublicando post de prueba...")
        result = post_to_facebook(
            FACEBOOK_PAGE_ID,
            FACEBOOK_PAGE_ACCESS_TOKEN,
            "Este es un post de prueba del bot de noticias automatico. Se eliminara pronto."
        )
        print(f"Resultado: {json.dumps(result, indent=2)}")
