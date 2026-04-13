"""
collect_analytics.py — Coleta contagem de visitas e salva historico diario
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

ANALYTICS_PATH = Path(__file__).parent.parent / "data" / "analytics.json"
COUNTER_URL = "https://visitor-badge.laobi.icu/badge?page_id=monsoonfc.monsoon-fc-site"


def load_analytics():
    if ANALYTICS_PATH.exists():
        with open(ANALYTICS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"daily": [], "monthly_reports": []}


def save_analytics(data):
    ANALYTICS_PATH.parent.mkdir(exist_ok=True)
    with open(ANALYTICS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_counter_value():
    import re
    try:
        req = urllib.request.Request(COUNTER_URL)
        with urllib.request.urlopen(req, timeout=10) as resp:
            svg = resp.read().decode("utf-8")
            # Extrair numero do SVG: >123</text><a
            match = re.search(r'>(\d+)</text><a', svg)
            if match:
                return int(match.group(1))
            print("[WARN] Nao encontrou contagem no SVG")
            return None
    except Exception as e:
        print(f"[WARN] Falha ao consultar contador: {e}")
        return None


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    analytics = load_analytics()

    count = get_counter_value()
    if count is None:
        print("[WARN] Nao foi possivel obter contagem. Pulando.")
        return

    # Verificar se ja registrou hoje
    existing_dates = {d["date"] for d in analytics["daily"]}
    if today in existing_dates:
        # Atualizar o valor de hoje
        for d in analytics["daily"]:
            if d["date"] == today:
                prev = d.get("total_count", 0)
                d["total_count"] = count
                d["visits_today"] = count - prev if count > prev else d.get("visits_today", 0)
                print(f"[OK] Atualizado {today}: total={count}")
                break
    else:
        # Calcular visitas do dia
        if analytics["daily"]:
            last = analytics["daily"][-1]["total_count"]
            visits_today = count - last if count > last else 0
        else:
            visits_today = count

        analytics["daily"].append({
            "date": today,
            "total_count": count,
            "visits_today": visits_today,
        })
        print(f"[OK] Registrado {today}: total={count}, hoje={visits_today}")

    # Manter apenas ultimos 90 dias
    analytics["daily"] = analytics["daily"][-90:]

    save_analytics(analytics)


if __name__ == "__main__":
    main()
