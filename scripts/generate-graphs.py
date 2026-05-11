import csv
import html
import math
from collections import defaultdict
from pathlib import Path

REPORTS_DIR = Path("reports")
GRAPHS_DIR  = REPORTS_DIR / "graphs"

SCENARIOS = {
    "python_cache":   {"label": "Python (com cache)",   "color": "#2563eb"},
    "python_nocache": {"label": "Python (sem cache)",   "color": "#93c5fd"},
    "ruby_cache":     {"label": "Ruby (com cache)",     "color": "#dc2626"},
    "ruby_nocache":   {"label": "Ruby (sem cache)",     "color": "#fca5a5"},
}

VUS = [1, 5, 10]

METRICS = {
    "Average Response Time": "Tempo medio de resposta (ms)",
    "50%":                   "Mediana P50 (ms)",
    "95%":                   "P95 (ms)",
    "Requests/s":            "Throughput (req/s)",
}


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_all():
    """Carrega todos os CSVs de stats, retorna dict[cenario][vu] = row_aggregated."""
    data = defaultdict(dict)
    for scenario in SCENARIOS:
        for vu in VUS:
            path = REPORTS_DIR / f"{scenario}_{vu}vu_stats.csv"
            if not path.exists():
                continue
            with path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("Name", "").strip().lower() == "aggregated":
                        data[scenario][vu] = row
                        break
    return data


def write_summary(data):
    """Gera summary.csv com todas as metricas de todos os cenarios."""
    path = REPORTS_DIR / "summary.csv"
    fields = ["cenario", "vu", "avg_ms", "p50_ms", "p90_ms", "p95_ms",
              "p99_ms", "req_per_s", "failure_pct", "total_requests"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for scenario in SCENARIOS:
            for vu in VUS:
                row = data[scenario].get(vu)
                if not row:
                    continue
                total    = as_float(row.get("Request Count", 0))
                failures = as_float(row.get("Failure Count", 0))
                w.writerow({
                    "cenario":        scenario,
                    "vu":             vu,
                    "avg_ms":         as_float(row.get("Average Response Time", 0)),
                    "p50_ms":         as_float(row.get("50%", 0)),
                    "p90_ms":         as_float(row.get("90%", 0)),
                    "p95_ms":         as_float(row.get("95%", 0)),
                    "p99_ms":         as_float(row.get("99%", 0)),
                    "req_per_s":      as_float(row.get("Requests/s", 0)),
                    "failure_pct":    round((failures / total * 100) if total > 0 else 0.0, 2),
                    "total_requests": int(total),
                })
    print(f"Resumo: {path}")


def nice_max(value):
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * power:
            return m * power
    return value * 1.2


def make_line_svg(title, x_label, y_label, series, output_path):
    """Grafico de linhas: X=VUs, uma linha por cenario."""
    W, H       = 860, 520
    L, R, T, B = 80, 210, 60, 70
    pw = W - L - R
    ph = H - T - B

    all_y = [v for pts in series.values() for v in pts.values() if v > 0]
    y_max = nice_max(max(all_y) if all_y else 1)

    def xp(vu):
        idx = VUS.index(vu)
        return L + idx * (pw / max(len(VUS) - 1, 1))

    def yp(v):
        return T + ph - (min(v, y_max) / y_max * ph)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{(W-R+L)/2}" y="38" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{L}" y1="{T+ph}" x2="{L+pw+8}" y2="{T+ph}" stroke="#111827" stroke-width="1.5"/>',
        f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T+ph}" stroke="#111827" stroke-width="1.5"/>',
        f'<text x="{L+pw/2}" y="{H-15}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(x_label)}</text>',
        f'<text transform="translate(18 {T+ph//2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]

    for tick in range(6):
        v  = y_max * tick / 5
        y  = yp(v)
        lines.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="#e5e7eb" stroke-dasharray="4,3"/>')
        lines.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{v:.0f}</text>')

    for vu in VUS:
        x = xp(vu)
        lines.append(f'<line x1="{x:.1f}" y1="{T+ph}" x2="{x:.1f}" y2="{T+ph+6}" stroke="#111827"/>')
        lines.append(f'<text x="{x:.1f}" y="{T+ph+22}" text-anchor="middle" font-family="Arial" font-size="13">{vu} VU(s)</text>')

    for idx, (scen_key, pts) in enumerate(series.items()):
        meta  = SCENARIOS[scen_key]
        color = meta["color"]
        label = meta["label"]
        sorted_pts = [(vu, pts[vu]) for vu in VUS if vu in pts]
        if not sorted_pts:
            continue
        coords = " ".join(f"{xp(x):.1f},{yp(y):.1f}" for x, y in sorted_pts)
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{coords}"/>')
        for x, y in sorted_pts:
            lines.append(f'<circle cx="{xp(x):.1f}" cy="{yp(y):.1f}" r="5" fill="{color}" stroke="#fff" stroke-width="1.5"/>')

        # Legenda à direita
        lx = L + pw + 20
        ly = T + idx * 32
        lines.append(f'<rect x="{lx}" y="{ly}" width="14" height="14" fill="{color}" rx="2"/>')
        lines.append(f'<text x="{lx+20}" y="{ly+11}" font-family="Arial" font-size="13">{html.escape(label)}</text>')

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all()

    if not any(data[s] for s in SCENARIOS):
        raise SystemExit("Nenhum CSV encontrado em reports/. Rode os testes primeiro.")

    write_summary(data)

    count = 0
    for metric_key, metric_label in METRICS.items():
        series = {}
        for scen in SCENARIOS:
            pts = {vu: as_float(data[scen][vu].get(metric_key, 0))
                   for vu in VUS if vu in data[scen]}
            if pts:
                series[scen] = pts

        safe  = metric_key.lower().replace("/", "s").replace("%", "pct").replace(" ", "_")
        fname = GRAPHS_DIR / f"comparacao_{safe}.svg"
        make_line_svg(
            title=f"Comparacao de Cenarios — {metric_label}",
            x_label="Usuarios Virtuais",
            y_label=metric_label,
            series=series,
            output_path=fname,
        )
        count += 1

    print(f"Graficos de linha: {GRAPHS_DIR}  ({count} arquivos)")


if __name__ == "__main__":
    main()
