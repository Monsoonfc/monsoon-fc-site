"""
generate_report.py — Gera relatorio mensal de visitas do site Monsoon FC
Cria uma GitHub Issue com o resumo dos ultimos 30 dias.
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ANALYTICS_PATH = Path(__file__).parent.parent / "data" / "analytics.json"


def load_analytics():
    if ANALYTICS_PATH.exists():
        with open(ANALYTICS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"daily": [], "monthly_reports": []}


def generate_report():
    analytics = load_analytics()
    daily = analytics.get("daily", [])

    if not daily:
        print("[WARN] Sem dados de visitas. Nenhum relatorio gerado.")
        return None

    # Filtrar ultimos 30 dias
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    last_30 = [d for d in daily if d["date"] >= cutoff]

    if not last_30:
        print("[WARN] Sem dados nos ultimos 30 dias.")
        return None

    total_visits = sum(d.get("visits_today", 0) for d in last_30)
    avg_daily = total_visits / len(last_30) if last_30 else 0
    max_day = max(last_30, key=lambda d: d.get("visits_today", 0))
    min_day = min(last_30, key=lambda d: d.get("visits_today", 0))
    current_total = last_30[-1].get("total_count", 0)

    period_start = last_30[0]["date"]
    period_end = last_30[-1]["date"]

    # Gerar tabela de visitas diarias
    table_rows = ""
    for d in last_30:
        visits = d.get("visits_today", 0)
        bar = "█" * min(int(visits / max(1, max_day.get("visits_today", 1)) * 20), 20)
        table_rows += f"| {d['date']} | {visits:,} | {bar} |\n"

    report = f"""## 📊 Relatório de Visitas — Monsoon FC

**Período:** {period_start} a {period_end} ({len(last_30)} dias)

### Resumo

| Métrica | Valor |
|---------|-------|
| 🔢 Total de visitas no período | **{total_visits:,}** |
| 📈 Média diária | **{avg_daily:.0f}** visitas/dia |
| 🏆 Dia com mais visitas | **{max_day['date']}** ({max_day.get('visits_today', 0):,} visitas) |
| 📉 Dia com menos visitas | **{min_day['date']}** ({min_day.get('visits_today', 0):,} visitas) |
| 🌐 Total acumulado (all-time) | **{current_total:,}** |

### Visitas Diárias

| Data | Visitas | Gráfico |
|------|---------|---------|
{table_rows}

---
*Relatório gerado automaticamente em {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}*
*Site: https://monsoonfc.github.io/monsoon-fc-site/*
"""

    # Registrar no historico
    analytics.setdefault("monthly_reports", []).append({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "period_start": period_start,
        "period_end": period_end,
        "total_visits": total_visits,
        "avg_daily": round(avg_daily),
        "days_tracked": len(last_30),
    })

    with open(ANALYTICS_PATH, "w", encoding="utf-8") as f:
        json.dump(analytics, f, ensure_ascii=False, indent=2)

    return report


def main():
    report = generate_report()
    if report:
        # Salvar report em arquivo temporario para o workflow criar a Issue
        report_path = Path(__file__).parent.parent / "data" / "last_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] Relatorio salvo em {report_path}")
        print(report)
    else:
        print("[INFO] Nenhum relatorio gerado.")


if __name__ == "__main__":
    main()
