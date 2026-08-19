import os
import random
import requests
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from io import BytesIO


def download_image(url):
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content))
    except Exception as e:
        print(f"  Error descargando imagen: {e}")
        return None


def edit_image(img, target_width=1200, target_height=630):
    img = img.convert("RGB")
    img_ratio = img.width / img.height if img.height else 1
    target_ratio = target_width / target_height
    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / img_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    img = img.crop((left, top, left + target_width, top + target_height))
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(0.95)
    img = ImageEnhance.Color(img).enhance(1.1)
    return img


def add_overlay(img, text=""):
    overlay = img.copy().convert("RGBA")
    overlay_draw = ImageDraw.Draw(overlay)

    gradient_height = img.height // 3
    for y in range(gradient_height):
        alpha = int(220 * (y / gradient_height))
        overlay_draw.line([(0, img.height - gradient_height + y), (img.width, img.height - gradient_height + y)],
                          fill=(0, 0, 0, alpha))

    if text:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("arial.ttf", 28)
            except (OSError, IOError):
                font = ImageFont.load_default()

        bbox = overlay_draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (img.width - tw) // 2
        y = img.height - gradient_height + 20
        overlay_draw.text((x, y), text, fill=(255, 255, 255), font=font)

    return overlay.convert("RGB")


def add_brand(img):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()
    draw.text((20, 15), "VOZ DEL PUEBLO", fill=(255, 255, 255), font=font)
    return img


def get_image_for_post(articles, keywords, output_path, overlay_text=""):
    from config import IMAGE_WIDTH, IMAGE_HEIGHT

    print("  Buscando imagen de la noticia...")

    for article in articles[:3]:
        img_url = article.get("image_url", "")
        if img_url:
            print(f"  Imagen encontrada: {img_url[:80]}...")
            img = download_image(img_url)
            if img and img.width > 100 and img.height > 100:
                img = edit_image(img, IMAGE_WIDTH, IMAGE_HEIGHT)
                img = add_brand(img)
                if overlay_text:
                    img = add_overlay(img, overlay_text[:60])
                img.save(output_path, "JPEG", quality=90)
                print(f"  Imagen de noticia guardada: {output_path}")
                return output_path

    print("  No hay imagen. Creando imagen con reflexion...")
    return create_reflection_image(output_path, articles, overlay_text, IMAGE_WIDTH, IMAGE_HEIGHT)


def create_reflection_image(output_path, articles, text="Colombia", W=1200, H=630):
    import math

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    palettes = [
        [(180, 30, 30), (220, 100, 30), (20, 60, 130)],
        [(20, 100, 180), (30, 180, 120), (180, 200, 30)],
        [(120, 30, 140), (200, 50, 80), (30, 80, 160)],
        [(30, 120, 100), (200, 140, 30), (180, 40, 80)],
        [(200, 60, 30), (30, 80, 180), (100, 180, 30)],
    ]
    colors = palettes[hash(text) % len(palettes)]

    for y in range(H):
        t = y / H
        if t < 0.5:
            t2 = t / 0.5
            r = int(colors[0][0] * (1 - t2) + colors[1][0] * t2)
            g = int(colors[0][1] * (1 - t2) + colors[1][1] * t2)
            b = int(colors[0][2] * (1 - t2) + colors[1][2] * t2)
        else:
            t2 = (t - 0.5) / 0.5
            r = int(colors[1][0] * (1 - t2) + colors[2][0] * t2)
            g = int(colors[1][1] * (1 - t2) + colors[2][1] * t2)
            b = int(colors[1][2] * (1 - t2) + colors[2][2] * t2)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    for i in range(6):
        cx = random.randint(0, W)
        cy = random.randint(0, H)
        size = random.randint(80, 250)
        for ring in range(size, 0, -3):
            alpha = int(20 * (1 - ring / size))
            r2 = colors[i % 3][0]
            g2 = colors[i % 3][1]
            b2 = colors[i % 3][2]
            bright = min(255, r2 + alpha * 3)
            draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring],
                         outline=(bright, min(255, g2 + alpha * 2), min(255, b2 + alpha * 2)))

    for i in range(40):
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.randint(1, 4)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255))

    draw.line([(0, 3), (W, 3)], fill=(255, 255, 255), width=4)
    draw.line([(0, H - 3), (W, H - 3)], fill=(255, 255, 255), width=4)

    try:
        font_quote = ImageFont.truetype("C:/Windows/Fonts/ariali.ttf", 30)
        font_brand = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except (OSError, IOError):
        font_quote = ImageFont.load_default()
        font_brand = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    headlines = [a["title"][:80] for a in articles[:3]]
    quote_text = headlines[0] if headlines else "Las noticias del dia en Colombia"

    words = quote_text.split()
    lines = []
    current_line = ""
    for word in words:
        test = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test, font=font_quote)
        if bbox[2] - bbox[0] > W - 160:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    total_height = len(lines) * 44
    start_y = (H - total_height) // 2 - 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_quote)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = start_y + i * 44
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=font_quote)
        draw.text((x, y), line, fill=(255, 255, 255), font=font_quote)

    draw.line([(W // 2 - 120, start_y + len(lines) * 44 + 15), (W // 2 + 120, start_y + len(lines) * 44 + 15)],
              fill=(255, 255, 255), width=3)

    brand = "VOZ DEL PUEBLO"
    bbox_b = draw.textbbox((0, 0), brand, font=font_brand)
    tw_b = bbox_b[2] - bbox_b[0]
    draw.text(((W - tw_b) // 2 + 2, H - 55 + 2), brand, fill=(0, 0, 0), font=font_brand)
    draw.text(((W - tw_b) // 2, H - 55), brand, fill=(255, 255, 255), font=font_brand)

    sub = "Analisis Politico del Dia"
    bbox_s = draw.textbbox((0, 0), sub, font=font_sub)
    tw_s = bbox_s[2] - bbox_s[0]
    draw.text(((W - tw_s) // 2, H - 28), sub, fill=(220, 220, 220), font=font_sub)

    img.save(output_path, "JPEG", quality=90)
    print(f"  Imagen con reflexion creada: {output_path}")
    return output_path


if __name__ == "__main__":
    from news_scraper import get_trending_news
    from config import ASSETS_DIR

    os.makedirs(ASSETS_DIR, exist_ok=True)
    articles = get_trending_news(max_articles=3)
    if articles:
        test_path = os.path.join(ASSETS_DIR, "test_reflection.jpg")
        result = get_image_for_post(articles, ["Colombia"], test_path, "Noticias del Dia")
        print(f"Resultado: {result}")
