import os
import textwrap
import subprocess
from PIL import Image, ImageDraw, ImageFont


FONT_PATHS = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

COLORS = [
    ((20, 20, 20), (255, 200, 50)),
    ((10, 10, 30), (0, 200, 255)),
    ((30, 0, 0), (255, 80, 80)),
    ((0, 20, 0), (100, 255, 100)),
    ((20, 10, 30), (200, 100, 255)),
    ((30, 20, 0), (255, 180, 0)),
]


def _get_font(size):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text, max_chars):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += " " + word if current else word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_slide_image(text, output_path, width=1080, height=1920, color_scheme=0, bg_image_path=None):
    bg_color, text_color = COLORS[color_scheme % len(COLORS)]

    if bg_image_path and os.path.exists(bg_image_path):
        try:
            img = Image.open(bg_image_path).convert("RGB")
            img = img.resize((width, height), Image.LANCZOS)
            overlay = Image.new("RGB", (width, height), bg_color)
            img = Image.blend(img, overlay, 0.6)
        except Exception:
            img = Image.new("RGB", (width, height), bg_color)
    else:
        img = Image.new("RGB", (width, height), bg_color)

    draw = ImageDraw.Draw(img)

    font_big = _get_font(52)
    font_small = _get_font(32)

    lines = _wrap_text(text, 28)
    total_height = len(lines) * 70
    start_y = (height - total_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_big)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        y = start_y + i * 70

        draw.text((x + 3, y + 3), line, fill=(0, 0, 0), font=font_big)
        draw.text((x, y), line, fill=text_color, font=font_big)

    brand = "VOZ DEL PUEBLO"
    bbox = draw.textbbox((0, 0), brand, font=font_small)
    bw = bbox[2] - bbox[0]
    draw.text(((width - bw) // 2, height - 150), brand, fill=(200, 200, 200), font=font_small)

    img.save(output_path, quality=90)
    return output_path


def text_to_slides(text, max_chars_per_slide=150):
    words = text.split()
    slides = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars_per_slide:
            current += " " + word if current else word
        else:
            if current:
                slides.append(current.strip())
            current = word
    if current:
        slides.append(current.strip())
    return slides


def create_reel_video(post_text, image_paths, output_path, duration_per_slide=4):
    slides = text_to_slides(post_text, 150)
    if not slides:
        slides = [post_text[:150]]

    temp_dir = os.path.join(os.path.dirname(output_path), "temp_slides")
    os.makedirs(temp_dir, exist_ok=True)

    slide_images = []
    for i, slide_text in enumerate(slides):
        bg_img = image_paths[0] if image_paths and i == 0 else None
        slide_path = os.path.join(temp_dir, f"slide_{i:03d}.jpg")
        create_slide_image(
            slide_text,
            slide_path,
            color_scheme=i % len(COLORS),
            bg_image_path=bg_img,
        )
        slide_images.append(slide_path)

    if len(slide_images) == 1:
        slide_images.append(slide_images[0])

    ffmpeg_input = os.path.join(temp_dir, "input.txt")
    with open(ffmpeg_input, "w", encoding="utf-8") as f:
        for img_path in slide_images:
            f.write(f"file '{img_path}'\n")
            f.write(f"duration {duration_per_slide}\n")
        f.write(f"file '{slide_images[-1]}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", ffmpeg_input,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-preset", "fast",
        "-crf", "23",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"  ffmpeg error: {result.stderr[:200]}")
            return None
    except FileNotFoundError:
        print("  ffmpeg no instalado. Instala ffmpeg para generar videos.")
        return None
    except subprocess.TimeoutExpired:
        print("  ffmpeg timeout")
        return None

    for p in slide_images:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(ffmpeg_input):
        os.remove(ffmpeg_input)
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass

    return output_path
