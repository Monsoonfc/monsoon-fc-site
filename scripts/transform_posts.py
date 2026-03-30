"""
transform_posts.py - Transforma posts do Instagram em materias profissionais.
Analisa legendas, categoriza, gera titulo, subtitulo e corpo do texto
no formato de artigo jornalistico para o site do Monsoon FC.
"""
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / "data" / "posts.json"
ARTICLES_PATH = BASE_DIR / "data" / "articles.json"


def clean_caption(caption):
    """Remove hashtags, emojis e formatacao do Instagram."""
    text = re.sub(r'#\w+', '', caption)
    text = re.sub(r'@\w+', lambda m: m.group(0), text)  # preserva @mentions
    text = re.sub(r'[^\w\s@.,!?:;\-\'"()/\n\u00C0-\u024F]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def extract_title(caption_clean):
    """Extrai titulo da primeira frase significativa."""
    lines = [l.strip() for l in caption_clean.split('\n') if l.strip()]
    if not lines:
        return "Monsoon FC"

    first = lines[0]
    # Se primeira linha e curta e impactante, usa como titulo
    if len(first) <= 80:
        return first.rstrip('.!').strip()

    # Senao, pega ate o primeiro ponto ou exclamacao
    match = re.match(r'^(.{15,70}[.!?])', first)
    if match:
        return match.group(1).rstrip('.!?').strip()

    # Trunca em 70 chars
    return first[:70].rsplit(' ', 1)[0] + '...'


def extract_subtitle(caption_clean, title):
    """Extrai subtitulo da segunda frase ou resumo."""
    lines = [l.strip() for l in caption_clean.split('\n') if l.strip()]
    for line in lines:
        if line != title and len(line) > 20 and len(line) <= 150:
            return line.rstrip('.!?').strip()
    return None


def categorize_post(caption, score):
    """Categoriza o post automaticamente."""
    caption_lower = caption.lower()

    if score:
        return "resultado"

    keywords = {
        "contratacao": [
            "anuncia", "contrata", "reforco", "chegada", "bem-vindo",
            "bem vindo", "apresenta", "novo jogador", "novo reforco",
            "movimentacao no monsoon", "acertou com", "fechou com",
        ],
        "renovacao": [
            "renova", "renovacao", "continua no", "permanece",
            "segue no comando", "contrato renovado",
        ],
        "parceria": [
            "parceiro", "parceria", "patrocinio", "patrocinador",
            "apoio", "sponsor", "anuncia oficialmente a chegada",
        ],
        "institucional": [
            "nota oficial", "comunicado", "informa", "esclarece",
            "fundado em", "historia do clube",
        ],
        "bastidores": [
            "treino", "treinamento", "pre-jogo", "concentracao",
            "vestiario", "bastidores", "dia de monsoon",
        ],
        "torcida": [
            "torcida", "torcedor", "monsooniano", "apoio da",
            "arquibancada", "camisa",
        ],
        "resultado": [
            "vitoria", "derrota", "empate", "gol", "placar",
            "venceu", "perdeu", "classificacao", "permanencia",
        ],
        "especial": [
            "dia internacional", "dia da mulher", "natal",
            "ano novo", "aniversario", "homenagem",
        ],
    }

    for category, words in keywords.items():
        for word in words:
            if word in caption_lower:
                return category

    return "noticia"


def generate_body(caption_clean, category):
    """Gera corpo do artigo a partir da legenda limpa."""
    lines = [l.strip() for l in caption_clean.split('\n') if l.strip()]

    if len(lines) <= 1:
        return caption_clean

    # Pula a primeira linha (titulo) e monta o corpo
    body_lines = lines[1:]
    body = '\n\n'.join(body_lines)
    return body


def transform_post(post):
    """Transforma um post do Instagram em artigo."""
    caption = post.get("caption", "")
    if not caption or len(caption) < 20:
        return None

    caption_clean = clean_caption(caption)
    if len(caption_clean) < 15:
        return None

    score = post.get("score")
    category = categorize_post(caption, score)
    title = extract_title(caption_clean)
    subtitle = extract_subtitle(caption_clean, title)
    body = generate_body(caption_clean, category)

    # Titulo especial para resultados
    if score and category == "resultado":
        title = f"Monsoon FC {score['home']} x {score['away']}"

    # Convert absolute paths to relative (media/...)
    thumb = post.get("thumbnail_web") or post.get("thumbnail") or ""
    thumb = thumb.replace("\\", "/")
    media_idx = thumb.find("/media/")
    if media_idx != -1:
        thumb = thumb[media_idx + 1:]  # "media/..."
    elif thumb and not thumb.startswith("media/"):
        thumb = ""

    article = {
        "id": post["post_id"],
        "shortcode": post["shortcode"],
        "date": post["date_display"],
        "timestamp": post["timestamp"],
        "category": category,
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "thumbnail": post.get("thumbnail"),
        "thumbnail_web": thumb if thumb else None,
        "local_paths": post.get("local_paths", []),
        "score": score,
        "likes": post.get("likes", 0),
        "instagram_url": post.get("instagram_url", ""),
        "media_type": post.get("media_type", "photo"),
    }

    return article


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        posts = json.load(f)

    articles = []
    categories_count = {}

    for post in posts:
        article = transform_post(post)
        if article:
            articles.append(article)
            cat = article["category"]
            categories_count[cat] = categories_count.get(cat, 0) + 1

    ARTICLES_PATH.parent.mkdir(exist_ok=True)
    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(articles)} materias geradas de {len(posts)} posts")
    print(f"     Categorias:")
    for cat, count in sorted(categories_count.items(), key=lambda x: -x[1]):
        print(f"       {cat}: {count}")


if __name__ == "__main__":
    main()
