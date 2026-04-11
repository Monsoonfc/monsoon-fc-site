"""
login_from_chrome.py — Extrai sessao do Instagram do Chrome e salva para o instaloader
"""
import sqlite3
import shutil
import json
import os
import sys
import tempfile
from pathlib import Path

CHROME_COOKIES_PATH = Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data" / "Default" / "Network" / "Cookies"
INSTA_SESSION_DIR = Path.home() / ".config" / "instaloader"


def get_instagram_cookies():
    """Extrai cookies do Instagram do Chrome (somente cookies nao-criptografados nao funciona no Win).
    No Windows, usa abordagem alternativa via browser_cookie3 ou manual."""

    # Tenta usar browser_cookie3
    try:
        import browser_cookie3
        cj = browser_cookie3.chrome(domain_name=".instagram.com")
        cookies = {}
        for c in cj:
            cookies[c.name] = c.value
        return cookies
    except ImportError:
        print("[INFO] Instalando browser_cookie3...")
        os.system(f'"{sys.executable}" -m pip install browser_cookie3 -q')
        try:
            import browser_cookie3
            cj = browser_cookie3.chrome(domain_name=".instagram.com")
            cookies = {}
            for c in cj:
                cookies[c.name] = c.value
            return cookies
        except Exception as e:
            print(f"[ERRO] Falha ao extrair cookies: {e}")
            return None
    except Exception as e:
        print(f"[ERRO] Falha ao extrair cookies: {e}")
        return None


def create_instaloader_session(cookies, username):
    """Cria arquivo de sessao do instaloader a partir dos cookies."""
    import requests

    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=".instagram.com")

    INSTA_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_file = INSTA_SESSION_DIR / f"session-{username}"

    import pickle
    with open(session_file, "wb") as f:
        pickle.dump(session.cookies, f)

    print(f"[OK] Sessao salva em: {session_file}")
    return session_file


def verify_session(username):
    """Verifica se a sessao funciona."""
    import instaloader
    L = instaloader.Instaloader(
        request_timeout=15,
        max_connection_attempts=2,
        quiet=True,
    )
    try:
        L.load_session_from_file(username)
        profile = instaloader.Profile.from_username(L.context, username)
        print(f"[OK] Sessao valida! Perfil: {profile.full_name} ({profile.followers} seguidores)")
        return True
    except Exception as e:
        print(f"[ERRO] Sessao invalida: {e}")
        return False


def main():
    username = "monsoon_fc_"

    print(f"[*] Extraindo cookies do Instagram do Chrome...")
    print(f"    IMPORTANTE: Feche o Chrome antes de continuar!")

    cookies = get_instagram_cookies()
    if not cookies:
        print("[ERRO] Nao foi possivel extrair cookies.")
        sys.exit(1)

    sessionid = cookies.get("sessionid", "")
    if not sessionid:
        print("[ERRO] Cookie 'sessionid' nao encontrado. Voce esta logado no Instagram no Chrome?")
        sys.exit(1)

    print(f"[OK] Encontrados {len(cookies)} cookies do Instagram")

    session_file = create_instaloader_session(cookies, username)

    print(f"[*] Verificando sessao...")
    if verify_session(username):
        print(f"\n[OK] Tudo pronto! O script de atualizacao vai usar essa sessao.")
    else:
        print(f"\n[WARN] Sessao criada mas verificacao falhou. Tente relogar no Instagram no Chrome.")


if __name__ == "__main__":
    main()
