"""
update_and_deploy.py — Atualiza o site Monsoon FC automaticamente
Busca posts do Instagram, transforma em materias, gera o site e faz deploy.
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
PYTHON = sys.executable


def run(cmd, desc):
    print(f"\n{'='*50}")
    print(f"[*] {desc}...")
    print(f"{'='*50}")
    result = subprocess.run(
        cmd,
        cwd=str(PROJECT_DIR),
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERRO] {desc} falhou (codigo {result.returncode})")
        return False
    print(f"[OK] {desc}")
    return True


def git_has_changes():
    result = subprocess.run(
        ["git", "status", "--porcelain", "data/", "media/", "output/"],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def main():
    print(f"\n{'#'*50}")
    print(f"  MONSOON FC — Atualizacao Automatica")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'#'*50}")

    # 1. Buscar posts do Instagram
    ok = run(
        [PYTHON, "scripts/fetch_instagram.py"],
        "Buscando posts do Instagram"
    )
    if not ok:
        print("[WARN] Falha ao buscar posts. Continuando com dados existentes...")

    # 2. Transformar posts em materias
    ok = run(
        [PYTHON, "scripts/transform_posts.py"],
        "Transformando posts em materias"
    )
    if not ok:
        print("[ERRO] Falha na transformacao. Abortando.")
        sys.exit(1)

    # 3. Gerar site estatico
    ok = run(
        [PYTHON, "scripts/build_site.py"],
        "Gerando site estatico"
    )
    if not ok:
        print("[ERRO] Falha na geracao do site. Abortando.")
        sys.exit(1)

    # 4. Verificar se tem mudancas
    if not git_has_changes():
        print("\n[OK] Nenhuma mudanca detectada. Site ja esta atualizado!")
        return

    # 5. Commit e push
    today = datetime.now().strftime("%Y-%m-%d")

    subprocess.run(["git", "add", "data/", "media/", "output/"], cwd=str(PROJECT_DIR))
    subprocess.run(
        ["git", "commit", "-m", f"chore: atualizar conteudo Instagram {today}"],
        cwd=str(PROJECT_DIR),
    )

    print("\n[*] Enviando para o GitHub...")
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERRO] git push falhou: {result.stderr}")
        sys.exit(1)
    print("[OK] Push para main concluido")

    # 6. Deploy gh-pages
    print("\n[*] Atualizando gh-pages...")
    subprocess.run(
        ["git", "subtree", "split", "--prefix", "output", "-b", "gh-pages"],
        cwd=str(PROJECT_DIR),
    )
    result = subprocess.run(
        ["git", "push", "-f", "origin", "gh-pages"],
        cwd=str(PROJECT_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERRO] Deploy gh-pages falhou: {result.stderr}")
        sys.exit(1)

    print(f"\n{'#'*50}")
    print(f"  [OK] Site atualizado com sucesso!")
    print(f"  https://monsoonfc.github.io/monsoon-fc-site/")
    print(f"{'#'*50}")


if __name__ == "__main__":
    main()
