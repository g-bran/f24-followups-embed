#!/usr/bin/env python3
"""
build_board.py — Self-contained. Lee el datastore de Make 104408 (solo agregados:
conteos por etapa del ladder de follow-ups; SIN nombres ni teléfonos) y escribe
index.html. GitHub Pages lo sirve → iframe embebido en GHL.

Sin secretos en el código (MAKE_API_TOKEN viene de los secrets del repo).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

DATASTORE_ID = 104408
STAGE_LABELS = {0: "Activo / reactivado", 1: "Etapa 1 (retirada)", 2: "Nudge 2h",
                3: "Nudge 22h", 4: "Plantilla D3", 5: "Plantilla D8", 6: "Plantilla D18 (fin)"}
LADDER = [0, 2, 3, 4, 5, 6]
BG = "#0f1115"; CARD = "#181b22"; INK = "#f3f4f6"; MUTE = "#9aa3af"
LINE = "#2a2f3a"; YEL = "#f5c518"; RED = "#e23b3b"; GRN = "#34d399"; BLU = "#60a5fa"


def list_records(ds_id: int) -> list[dict]:
    token = os.environ.get("MAKE_API_TOKEN")
    zone = os.environ.get("MAKE_API_ZONE", "us2") or "us2"
    if "." not in zone:
        zone = f"{zone}.make.com"
    if not token:
        raise RuntimeError("Falta MAKE_API_TOKEN")
    base = f"https://{zone}/api/v2/data-stores/{ds_id}/data"
    out, offset = [], 0
    while True:
        url = f"{base}?pg%5Blimit%5D=100&pg%5Boffset%5D={offset}"
        req = urllib.request.Request(url, headers={
            "Authorization": "Token " + token, "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=45) as r:
            payload = json.loads(r.read().decode())
        recs = payload.get("records", payload.get("data", []))
        if not recs:
            break
        out.extend(rec.get("data", rec) for rec in recs)
        if len(recs) < 100 or len(out) >= 5000:
            break
        offset += 100
    return out


def _age_days(iso):
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - d).total_seconds() / 86400
    except Exception:
        return None


def analyze(records):
    by_stage, escalated, muted, stale = {}, 0, 0, 0
    for r in records:
        s = r.get("followup_stage")
        by_stage[s] = by_stage.get(s, 0) + 1
        if r.get("escalated"):
            escalated += 1
        if r.get("bot_muted_until"):
            muted += 1
        a = _age_days(r.get("lastMessageAt"))
        if a is not None and a > 21:
            stale += 1
    return {"total": len(records), "by_stage": by_stage, "escalated": escalated,
            "muted": muted, "stale_21d": stale,
            "generated": datetime.now(timezone.utc).isoformat()}


def _bar(label, count, total, color):
    pct = (count / total * 100) if total else 0
    return (f"<div style='margin:7px 0;'><div style='display:flex;justify-content:space-between;"
            f"font-size:13px;color:{INK};margin-bottom:3px;'><span>{label}</span>"
            f"<span style='color:{MUTE};'>{count} · {pct:.0f}%</span></div>"
            f"<div style='background:{LINE};border-radius:6px;height:10px;overflow:hidden;'>"
            f"<div style='width:{max(pct,1.5):.1f}%;height:100%;background:{color};'></div></div></div>")


def _stat(label, val, color=INK, sub=""):
    sh = f"<div style='color:{MUTE};font-size:11px;margin-top:2px;'>{sub}</div>" if sub else ""
    return (f"<div style='flex:1;min-width:120px;background:{CARD};border:1px solid {LINE};"
            f"border-radius:12px;padding:12px 14px;'><div style='color:{MUTE};font-size:11px;"
            f"text-transform:uppercase;letter-spacing:.5px;'>{label}</div><div style='color:{color};"
            f"font-size:24px;font-weight:800;margin-top:3px;'>{val}</div>{sh}</div>")


def render(a):
    total, bs = a["total"], a["by_stage"]
    bars = ""
    for s in LADDER:
        c = bs.get(s, 0)
        col = GRN if s == 0 else (YEL if s in (2, 3) else (BLU if s == 4 else RED))
        bars += _bar(STAGE_LABELS.get(s, str(s)), c, total, col)
    if bs.get(None, 0):
        bars += _bar("Sin etapa", bs[None], total, MUTE)
    gen = a["generated"][:16].replace("T", " ")
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Follow-ups F24</title></head>
<body style="margin:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;padding:20px 16px 30px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div style="font-weight:800;color:{YEL};font-size:18px;">FERRE24 · FOLLOW-UPS</div>
    <div style="color:{MUTE};font-size:12px;">{gen} UTC</div></div>
  <h1 style="color:{INK};font-size:23px;margin:8px 0 4px;">Estado del ladder WhatsApp</h1>
  <p style="color:{MUTE};font-size:14px;line-height:1.5;margin:0 0 16px;">{total} leads en seguimiento.
  Distribución por etapa abajo — dónde se apilan = dónde se enfrían sin avanzar.</p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;">
    {_stat("Leads totales", total)}{_stat("Escalados a Edgar", a['escalated'], GRN, "tomados por humano")}
    {_stat("Bot muteado", a['muted'], YEL)}{_stat("Fríos &gt;21d", a['stale_21d'], RED, "sin actividad")}</div>
  <div style="background:{CARD};border:1px solid {LINE};border-radius:14px;padding:16px;">
    <div style="color:{INK};font-size:15px;font-weight:700;margin-bottom:8px;">Por etapa del ladder</div>{bars}</div>
  <div style="margin-top:14px;color:{MUTE};font-size:12px;line-height:1.5;">Lectura: si la mayoría vive en
  D8/D18 sin convertir, el problema es el copy/oferta de los nudges, no el volumen. El oro está en el nudge 2h/22h.</div>
  <div style="margin-top:16px;border-top:1px solid {LINE};padding-top:10px;text-align:center;color:{MUTE};font-size:11px;">
    Monitor automático · SPEKGEN · se actualiza 2×/día</div>
</div></body></html>"""


if __name__ == "__main__":
    html = render(analyze(list_records(DATASTORE_ID)))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html regenerado")
