import csv
import html
import math
from pathlib import Path

REPORTS_DIR = Path("reports")
OUTPUT_DIR  = REPORTS_DIR / "bar_graphs"

# 4 cenarios do trabalho
SCENARIOS = {
    "python_cache":   "Python\n(com cache)",
    "python_nocache": "Python\n(sem cache)",
    "ruby_cache":     "Ruby\n(com cache)",
    "ruby_nocache":   "Ruby\n(sem cache)",
}

SCENARIO_COLORS = {
    "python_cache":   "#2563eb",
    "python_nocache": "#93c5fd",
    "ruby_cache":     "#dc2626",
    "ruby_nocache":   "#fca5a5",
}

VUS = [1, 5, 10]

# Metricas retiradas do CSV do Locust
METRICS = {
    "Average Response Time": {"label": "Tempo medio de resposta (ms)", "suffix": "avg"},
    "50%":                   {"label": "Mediana P50 (ms)",              "suffix": "p50"},
    "90%":                   {"label": "P90 (ms)",                      "suffix": "p90"},
    "95%":                   {"label": "P95 (ms)",                      "suffix": "p95"},
    "Requests/s":            {"label": "Throughput (req/s)",            "suffix": "throughput"},
    "failure_rate":          {"label": "Taxa de falha (%)",             "suffix": "taxa_falha"},
}


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_aggregated(scenario: str, vu: int):
    path = REPORTS_DIR / f"{scenario}_{vu}vu_stats.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Name", "").strip().lower() == "aggregated":
                total    = as_float(row.get("Request Count", 0))
                failures = as_float(row.get("Failure Count", 0))
                row["failure_rate"] = (failures / total * 100) if total > 0 else 0.0
                return row
    return None


def nice_max(value):
    if value <= 0:
        return 1
    power = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * power:
            return m * power
    return value * 1.2


def fmt(v):
    if v >= 1000: return f"{v:.0f}"
    if v >= 10:   return f"{v:.1f}"
    if v >= 1:    return f"{v:.2f}"
    return f"{v:.3f}"


def build_bar_svg(title, y_label, labels, values, colors, output_path):
    W, H       = 800, 520
    L, R, T, B = 90, 50, 70, 110
    pw = W - L - R
    ph = H - T - B
    n  = len(labels)

    y_max   = nice_max(max(values) if any(v > 0 for v in values) else 1)
    gap     = 28
    bar_w   = (pw - gap * (n + 1)) / n

    def yp(v):
        return T + ph - (min(v, y_max) / y_max * ph)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{W/2}" y="38" text-anchor="middle" font-family="Arial" font-size="15" font-weight="700">{html.escape(title)}</text>',
        f'<line x1="{L}" y1="{T+ph}" x2="{L+pw+8}" y2="{T+ph}" stroke="#111827" stroke-width="1.5"/>',
        f'<line x1="{L}" y1="{T+ph}" x2="{L}" y2="{T-8}" stroke="#111827" stroke-width="1.5"/>',
        f'<text transform="translate(18 {T+ph//2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]

    for tick in range(1, 6):
        v  = y_max * tick / 5
        y  = yp(v)
        lines.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L+pw}" y2="{y:.1f}" stroke="#e5e7eb" stroke-dasharray="4,3"/>')
        lines.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{fmt(v)}</text>')

    for i, (lbl, val, color) in enumerate(zip(labels, values, colors)):
        x    = L + gap * (i + 1) + bar_w * i
        y    = yp(val)
        bh   = T + ph - y
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{color}" rx="3" stroke="#00000033" stroke-width="1"/>')
        lines.append(f'<text x="{x+bar_w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Arial" font-size="11" font-weight="700" fill="#111827">{fmt(val)}</text>')
        for j, part in enumerate(lbl.split("\n")):
            lines.append(f'<text x="{x+bar_w/2:.1f}" y="{T+ph+22+j*15}" text-anchor="middle" font-family="Arial" font-size="12">{html.escape(part)}</text>')

    lines.append("</svg>")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    for vu in VUS:
        for metric_key, meta in METRICS.items():
            lbls, vals, cols = [], [], []
            for scen, scen_lbl in SCENARIOS.items():
                row = load_aggregated(scen, vu)
                val = 0.0
                if row:
                    val = row["failure_rate"] if metric_key == "failure_rate" else as_float(row.get(metric_key, 0))
                lbls.append(scen_lbl)
                vals.append(val)
                cols.append(SCENARIO_COLORS[scen])

            title = f"{meta['label']} — {vu} usuario(s) virtual(is)"
            fname = f"{meta['suffix']}_{vu}vu.svg"
            build_bar_svg(title, meta["label"], lbls, vals, cols, OUTPUT_DIR / fname)
            count += 1

    print(f"Graficos de barras: {OUTPUT_DIR}  ({count} arquivos)")


if __name__ == "__main__":
    main()
