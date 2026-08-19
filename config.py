import os

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

NEWS_QUERIES = [
    "gobierno Colombia",
    "politica Colombia izquierda",
    "ley reforma Colombia beneficios",
    "noticias Colombia viral",
    "gobierno popular Colombia trabajadores",
]

NEWS_COUNTRY = "CO"
NEWS_LANGUAGE = "es-419"
NEWS_MAX_ARTICLES = 20

POST_STYLE = (
    "Eres un analista politico independiente de Colombia. "
    "Escribes para una pagina de Facebook que analiza noticias de gobierno "
    "con enfoque en politicas de izquierda que benefician a la gente comun "
    "y personas menos favorecidas. Si la derecha hace algo positivo para el pueblo, "
    "tambien lo reconoce. Tono: critico, informativo, cercano al pueblo colombiano. "
    "Usa emojis con moderacion. Incluye hashtags relevantes."
)

POST_MAX_LENGTH = 500

IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

POSTS_PER_RUN = 10
