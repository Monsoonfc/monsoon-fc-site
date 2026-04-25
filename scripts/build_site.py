"""
build_site.py - Gera o site estatico do Monsoon FC a partir das materias processadas.
"""
import json
import re
import shutil
import unicodedata
from pathlib import Path
from datetime import datetime, timezone

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("[ERRO] Instale as dependencias: pip install -r requirements.txt")
    raise

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
ARTICLES_PATH = BASE_DIR / "data" / "articles.json"
POSTS_PATH = BASE_DIR / "data" / "posts.json"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
MEDIA_DIR = BASE_DIR / "media"
OUTPUT_DIR = BASE_DIR / "output"
LOJA_DIR = BASE_DIR / "loja"

CATEGORY_LABELS = {
    "resultado": "Resultados",
    "contratacao": "Contratacoes",
    "renovacao": "Renovacoes",
    "parceria": "Parcerias",
    "institucional": "Institucional",
    "bastidores": "Bastidores",
    "torcida": "Torcida",
    "especial": "Especial",
    "noticia": "Noticias",
}


def load_data():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)
    articles = []
    if ARTICLES_PATH.exists():
        with open(ARTICLES_PATH, encoding="utf-8") as f:
            articles = json.load(f)
    elif POSTS_PATH.exists():
        with open(POSTS_PATH, encoding="utf-8") as f:
            articles = json.load(f)
    return config, articles


def fix_media_paths(articles):
    for a in articles:
        thumb = a.get("thumbnail_web") or a.get("thumbnail")
        if thumb:
            a["thumbnail_web"] = thumb.replace("\\\\", "/")
        else:
            a["thumbnail_web"] = None
        # Adicionar URL da pagina interna do artigo
        if a.get("shortcode"):
            a["article_url"] = f"noticias/{a['shortcode']}.html"
    return articles


def partition_articles(articles):
    results = [a for a in articles if a.get("category") == "resultado" or a.get("score")]
    contratacoes = [a for a in articles if a.get("category") == "contratacao"]
    parcerias = [a for a in articles if a.get("category") == "parceria"]
    noticias = [a for a in articles if a.get("category") not in ("resultado",)]
    total_likes = sum(a.get("likes", 0) for a in articles)
    return {
        "all": articles,
        "latest": articles[:6],
        "results": results,
        "latest_results": results[:3],
        "contratacoes": contratacoes,
        "parcerias": parcerias,
        "noticias": noticias,
        "categories": get_categories(articles),
        "total_likes": total_likes,
    }


def get_categories(articles):
    cats = {}
    for a in articles:
        cat = a.get("category", "noticia")
        if cat not in cats:
            cats[cat] = {"key": cat, "label": CATEGORY_LABELS.get(cat, cat.title()), "count": 0}
        cats[cat]["count"] += 1
    return sorted(cats.values(), key=lambda x: -x["count"])


def render_pages(config, partitions, env, now_str):
    pages = [
        ("index.html", OUTPUT_DIR / "index.html", {"articles": partitions["latest"], "results": partitions["latest_results"], "categories": partitions["categories"]}),
        ("feed.html", OUTPUT_DIR / "feed" / "index.html", {"articles": partitions["all"], "categories": partitions["categories"]}),
        ("results.html", OUTPUT_DIR / "resultados" / "index.html", {"articles": partitions["results"]}),
        ("news.html", OUTPUT_DIR / "noticias" / "index.html", {"articles": partitions["noticias"], "categories": partitions["categories"]}),
    ]
    for template_name, out_path, extra_ctx in pages:
        template = env.get_template(template_name)
        ctx = {
            "config": config,
            "now": now_str,
            "total_articles": len(partitions["all"]),
            "total_likes": partitions.get("total_likes", 0),
            **extra_ctx,
        }
        rendered = template.render(**ctx)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        print(f"[OK] Gerado: {out_path.relative_to(OUTPUT_DIR.parent)}")


def render_individual_articles(config, articles, env, now_str):
    """Gera uma pagina HTML para cada materia."""
    try:
        template = env.get_template("article.html")
    except Exception as e:
        print(f"[WARN] Template article.html nao encontrado: {e}")
        return 0

    out_dir = OUTPUT_DIR / "noticias"
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for i, article in enumerate(articles):
        shortcode = article.get("shortcode")
        if not shortcode:
            continue

        # Pegar 4 materias relacionadas (mesma categoria, exceto a atual)
        same_cat = [a for a in articles if a.get("category") == article.get("category") and a.get("shortcode") != shortcode]
        related = same_cat[:4]
        for r in related:
            r["category"] = CATEGORY_LABELS.get(r.get("category", "noticia"), r.get("category", "Noticia"))

        category_label = CATEGORY_LABELS.get(article.get("category", "noticia"), "Noticia")

        rendered = template.render(
            config=config,
            now=now_str,
            article=article,
            category_label=category_label,
            related=related,
            total_articles=len(articles),
        )

        out_path = out_dir / f"{shortcode}.html"
        out_path.write_text(rendered, encoding="utf-8")
        count += 1

    print(f"[OK] {count} paginas individuais geradas em {out_dir}")
    return count


def copy_assets():
    static_dest = OUTPUT_DIR / "static"
    if static_dest.exists():
        shutil.rmtree(static_dest, ignore_errors=True)
    shutil.copytree(STATIC_DIR, static_dest, dirs_exist_ok=True)
    media_dest = OUTPUT_DIR / "media"
    if media_dest.exists():
        shutil.rmtree(media_dest, ignore_errors=True)
    if MEDIA_DIR.exists():
        shutil.copytree(MEDIA_DIR, media_dest, dirs_exist_ok=True)
        print(f"[OK] Midia copiada: {MEDIA_DIR}")


def copy_loja():
    """Copia a pasta loja/ para output/loja/ sem processar."""
    if LOJA_DIR.exists():
        loja_dest = OUTPUT_DIR / "loja"
        if loja_dest.exists():
            shutil.rmtree(loja_dest, ignore_errors=True)
        shutil.copytree(LOJA_DIR, loja_dest, dirs_exist_ok=True)
        print(f"[OK] Loja copiada: {LOJA_DIR}")


def main():
    config, articles = load_data()
    articles = fix_media_paths(articles)
    partitions = partition_articles(articles)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    env.filters["format_number"] = lambda n: f"{n:,.0f}".replace(",", ".")
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    copy_assets()
    render_pages(config, partitions, env, now_str)
    render_individual_articles(config, articles, env, now_str)
    copy_loja()
    cats = partitions["categories"]
    cat_str = " | ".join(f"{c['label']}: {c['count']}" for c in cats[:5])
    print(f"\n[OK] Site gerado em: {OUTPUT_DIR}")
    print(f"  {len(articles)} materias | {cat_str}")


if __name__ == "__main__":
    main()
