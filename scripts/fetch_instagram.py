"""
fetch_instagram.py — Coleta posts do Instagram do Monsoon FC
Usa instaloader para scraping de perfil público sem API do Facebook.
"""
import instaloader
import json
import time
import re
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config.json"
DATA_PATH = Path(__file__).parent.parent / "data" / "posts.json"
MEDIA_DIR = Path(__file__).parent.parent / "media"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_existing_posts():
    if DATA_PATH.exists():
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def get_latest_timestamp(posts):
    if not posts:
        return None
    return max(p["timestamp"] for p in posts)


def classify_media_type(post):
    if post.is_video:
        return "video"
    if post.typename == "GraphSidecar":
        return "carousel"
    return "photo"


def parse_score_from_caption(caption):
    """Detecta placar na legenda: '2x1', '2-1', '2 a 1', '2X1'"""
    if not caption:
        return None
    patterns = [
        r'\b(\d{1,2})\s*[xX×]\s*(\d{1,2})\b',
        r'\b(\d{1,2})\s*[–\-]\s*(\d{1,2})\b',
        r'\b(\d{1,2})\s+a\s+(\d{1,2})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, caption)
        if match:
            return {
                "home": match.group(1),
                "away": match.group(2),
                "raw": match.group(0)
            }
    return None


def download_post_media(L, post):
    """Baixa mídia do post e retorna lista de caminhos locais relativos."""
    post_dir = MEDIA_DIR / str(post.mediaid)
    post_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    try:
        L.download_post(post, target=post_dir)
        for ext in ("*.jpg", "*.jpeg", "*.mp4", "*.webp"):
            downloaded.extend(post_dir.glob(ext))
    except Exception as e:
        print(f"  [WARN] Falha ao baixar midia {post.mediaid}: {e}")

    rel_paths = [str(p).replace("\\", "/") for p in sorted(downloaded)]
    return rel_paths


def fetch_posts(config, existing_posts):
    username = config["instagram_username"]
    history_since = datetime.fromisoformat(config["history_since"])
    latest_ts = get_latest_timestamp(existing_posts)

    L = instaloader.Instaloader(
        sleep=True,
        quiet=False,
        request_timeout=30,
        max_connection_attempts=3,
        download_videos=True,
        download_video_thumbnails=True,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    # Tenta carregar sessao salva
    login_user = os.environ.get("INSTA_USER") or config.get("login_user", "")
    if login_user:
        try:
            L.load_session_from_file(login_user)
            print(f"[OK] Sessao carregada para @{login_user}")
        except FileNotFoundError:
            print(f"[INFO] Sessao nao encontrada para @{login_user}, tentando sem login...")
    else:
        print("[INFO] Sem login, tentando acesso publico...")

    print(f"[*] Buscando posts de @{username}...")
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ConnectionException as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            print(f"[ERRO] Instagram bloqueou requisicoes (rate limit 429).")
            print("[DICA] A sessao pode ter expirado. Recrie com: instaloader -l SEU_USUARIO")
            # Nao falha - usa posts existentes
            return []
        print(f"[ERRO] Ao acessar perfil: {e}")
        print("[DICA] Tente fazer login: instaloader -l SEU_USUARIO_INSTAGRAM")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO] Ao acessar perfil: {e}")
        print("[DICA] Tente fazer login: instaloader -l SEU_USUARIO_INSTAGRAM")
        sys.exit(1)

    print(f"[OK] Perfil encontrado: {profile.full_name} ({profile.followers} seguidores)")

    new_posts = []
    existing_ids = {p["post_id"] for p in existing_posts}
    consecutive_existing = 0
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    for post in profile.get_posts():
        post_dt = post.date_utc.replace(tzinfo=None)

        # Limite histórico
        if post_dt < history_since:
            print(f"[FIM] Limite historico atingido em {post_dt.date()} -- parando.")
            break

        post_ts = post_dt.timestamp()

        # Pular posts já salvos (pode ter pinados no meio)
        if str(post.mediaid) in existing_ids:
            consecutive_existing += 1
            print(f"[SKIP] Post {post.mediaid} ({post_dt.strftime('%d/%m/%Y')}) ja salvo.")
            # Para depois de 5 posts seguidos ja salvos (passou dos novos)
            if consecutive_existing >= 5:
                print(f"[FIM] 5 posts seguidos ja salvos -- parando.")
                break
            continue

        consecutive_existing = 0  # resetar contador

        print(f"[DL] Baixando {post.mediaid} ({post_dt.strftime('%d/%m/%Y')})")

        local_paths = download_post_media(L, post)
        score = parse_score_from_caption(post.caption)
        caption = post.caption or ""

        post_data = {
            "post_id": str(post.mediaid),
            "shortcode": post.shortcode,
            "timestamp": post_ts,
            "date_display": post_dt.strftime("%d/%m/%Y"),
            "caption": caption,
            "likes": post.likes,
            "media_type": classify_media_type(post),
            "local_paths": local_paths,
            "thumbnail": local_paths[0] if local_paths else None,
            "score": score,
            "is_result": score is not None,
            "is_news": bool(caption and len(caption) > 80 and not score),
            "instagram_url": f"https://www.instagram.com/p/{post.shortcode}/",
        }

        new_posts.append(post_data)
        time.sleep(3)  # evita rate-limit

    return new_posts


def main():
    config = load_config()
    existing = load_existing_posts()

    new_posts = fetch_posts(config, existing)

    if not new_posts:
        print("[OK] Nenhum post novo encontrado.")
        return

    all_posts = new_posts + existing
    all_posts = all_posts[:config.get("max_posts", 500)]

    DATA_PATH.parent.mkdir(exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    print(f"[OK] {len(all_posts)} posts salvos ({len(new_posts)} novos).")


if __name__ == "__main__":
    main()
