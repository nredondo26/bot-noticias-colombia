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
    "noticias virales mundo hoy",
    "crisis humanitaria mundo",
    "guerra rusia ucrania ultima hora",
    "conflicto medio oriente israel palestina",
    "eeuu politica trump elecciones",
    "china economia guerra comercial",
    "latinoamerica izquierda gobierno",
    "clima desastres naturales emergencia",
    "tecnologia inteligencia artificial avances",
    "economia mundial crisis inflacion",
    "migracion refugiados crisis",
    "corrupcion escandalos politicos mundo",
    "derechos humanos violaciones",
    "palestina genocide guerra",
    "india crecimiento economico",
]

NEWS_COUNTRY = "CO"
NEWS_LANGUAGE = "es-419"
NEWS_MAX_ARTICLES = 20

POST_STYLE = (
    "Eres el analista politico de la pagina 'Voz del Pueblo'. "
    "Escribes posts de Facebook sobre noticias de ALTO IMPACTO y VIRALIDAD "
    "de todo el mundo y Colombia. Analizas conflictos, politica internacional, "
    "derechos humanos, economia, tecnologia, desastres naturales, corrupcion, "
    "guerras, migracion y cualquier noticia que genere debate. "
    "Enfoque: la gente comun debe entender que pasa en el mundo y como le afecta. "
    "Si hay injusticia, la senalas. Si hay algo positivo, lo reconoces. "
    "Tono: critico, informativo, cercano al pueblo. "
    "Usa emojis con moderacion. Incluye hashtags relevantes."
)

POST_MAX_LENGTH = 500

IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

REPORT_RECIPIENT_ID = os.environ.get("REPORT_RECIPIENT_ID", "2572243889888389")

POSTS_PER_RUN = 10
