"""
add_manual_post.py
Adiciona manualmente um post do Instagram ao posts.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
DATA_PATH = BASE_DIR / "data" / "posts.json"

def shortcode_to_mediaid(shortcode):
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    result = 0
    for char in shortcode:
        result = result * 64 + alphabet.index(char)
    return result

# Dados do reel DXzqymlRuaL
shortcode = "DXzqymlRuaL"
mediaid = shortcode_to_mediaid(shortcode)

# Data: 2026-05-01T19:12:56.000Z
post_dt = datetime(2026, 5, 1, 19, 12, 56, tzinfo=timezone.utc)
timestamp = post_dt.timestamp()

caption = """A preparacao de alto rendimento vai alem das quatro linhas.

E e nesse cenario que a Pano Bianco Academia, junto com o nosso preparador fisico @nobremarcusvinicius, desenvolve o trabalho fisico dos nossos atletas, com metodologia, acompanhamento especializado e estrutura alinhada as exigencias do futebol profissional.

Uma parceria que contribui diretamente para o desempenho do tubarao do litoral dentro de campo.

#MonsoonFC #TubaraodoLitoral #AltoRendimento #PreparacaoFisica #Parceria"""

new_post = {
    "post_id": str(mediaid),
    "shortcode": shortcode,
    "timestamp": timestamp,
    "date_display": "01/05/2026",
    "caption": caption,
    "likes": 134,
    "media_type": "video",
    "local_paths": [],
    "thumbnail": None,
    "thumbnail_web": None,
    "score": None,
    "is_result": False,
    "is_news": False,
    "instagram_url": f"https://www.instagram.com/reel/{shortcode}/"
}

# Carrega posts existentes
posts = json.load(open(DATA_PATH, encoding="utf-8"))

# Verifica se ja existe
existing_ids = {p["post_id"] for p in posts}
if new_post["post_id"] in existing_ids:
    print(f"[AVISO] Post {shortcode} ja existe no banco!")
else:
    # Insere no topo (mais recente primeiro)
    posts.insert(0, new_post)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Post adicionado: {shortcode} (mediaid: {mediaid})")
    print(f"[OK] Total: {len(posts)} posts")
    print(f"[OK] Categoria sera: parceria (tem 'parceria' na legenda)")
