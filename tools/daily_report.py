#!/usr/bin/env python3
"""
Resum diari de riusdegent -> correu a la direccio humana (Bea).

Compila l'activitat del dia (commits per agent, PRs, entrades de bitacola) i
envia un resum per correu. Pensat per correr a GitHub Actions:
  - cron a les 21:00 Europe/Madrid (doble cron 19/20 UTC + guarda DST), o
  - manualment (workflow_dispatch) per a proves.

Filosofia: la *bitacola-as-contract* convertida en resum diari. L'atribucio per
agent surt "gratis" dels commits identity-inline (user.name = nom de l'agent).

Secrets (NOMES per variables d'entorn, mai al repo):
  GMAIL_APP_PASSWORD  -> necessari per enviar (si falta o DRY_RUN=1, nomes imprimeix)
  OPENROUTER_API_KEY  -> opcional, per al resum executiu amb veu de Talaia
Config (env):
  REPORT_TO   (def. zigiella@gmail.com)
  REPORT_FROM (def. = REPORT_TO)         # Gmail exigeix From = compte autenticat
  REPORT_MODEL(def. openai/gpt-4o-mini)
  DRY_RUN     (1 = no envia, imprimeix)
"""
from __future__ import annotations

import datetime
import json
import os
import smtplib
import ssl
import subprocess
import sys
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from html import escape
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Madrid")
UTC = datetime.timezone.utc
NOW = datetime.datetime.now(TZ)


# --------------------------------------------------------------------------- #
# Utilitats
# --------------------------------------------------------------------------- #
def sh(args: list[str]) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        return (r.stdout or "").strip()
    except Exception as e:  # noqa: BLE001
        print(f"[warn] ordre fallida {args[:2]}: {e}")
        return ""


def gh_json(args: list[str]):
    out = sh(["gh", *args])
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def parse_iso(s: str | None):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def author_name(p: dict) -> str:
    a = p.get("author") or {}
    return a.get("login") or a.get("name") or "?"


# --------------------------------------------------------------------------- #
# Finestra temporal: des de les 21:00 locals anteriors fins ara
# --------------------------------------------------------------------------- #
def window_start() -> datetime.datetime:
    today21 = NOW.replace(hour=21, minute=0, second=0, microsecond=0)
    if NOW >= today21:
        return today21 - datetime.timedelta(days=1)
    # execucio manual abans de les 21h: cobreix les ultimes 24h
    return NOW - datetime.timedelta(days=1)


SINCE = window_start()
SINCE_UTC = SINCE.astimezone(UTC)
EVENT = os.environ.get("GITHUB_EVENT_NAME", "manual")

# Guarda: en cron nomes enviem a les 21h locals (el doble cron 19/20 UTC fa que
# un dels dos encerti les 21h Madrid tant a l'estiu com a l'hivern).
if EVENT == "schedule" and NOW.hour != 21:
    print(f"[skip] no son les 21h a Madrid (ara {NOW.hour}h).")
    sys.exit(0)


# --------------------------------------------------------------------------- #
# Recollida de dades
# --------------------------------------------------------------------------- #
def _is_merger(name: str) -> bool:
    # El compte que fa el squash-merge i els bots no son "agents".
    return name.strip().lower() in {
        "zigiella", "github", "web-flow", "github-actions[bot]",
    }


def collect_work():
    """Activitat per AGENT, reconstruida des dels commits dels PRs del dia.

    A `main` els squash-merge s'atribueixen al compte que mergeja; els commits
    identity-inline dels agents (user.name = Llegenda/Bruixola/Sondeig/...) viuen
    al PR, aixi que els llegim d'alla amb `gh pr view --json commits`.
    """
    merged = gh_json(["pr", "list", "--state", "merged", "--limit", "60",
                      "--json", "number,title,mergedAt,url"])
    allp = gh_json(["pr", "list", "--state", "all", "--limit", "60",
                    "--json", "number,title,createdAt,url,state"])
    openp = gh_json(["pr", "list", "--state", "open", "--limit", "60",
                     "--json", "number,title,url,isDraft"])

    status: dict[int, str] = {}
    title: dict[int, str] = {}
    link: dict[int, str] = {}

    def remember(p: dict, st: str) -> None:
        n = p["number"]
        status.setdefault(n, st)
        title.setdefault(n, p.get("title", ""))
        link.setdefault(n, p.get("url", ""))

    for p in merged:
        if after(p.get("mergedAt")):
            remember(p, "mergejat avui")
    for p in allp:
        if after(p.get("createdAt")):
            remember(p, "obert avui")
    for p in openp:
        remember(p, "obert (draft)" if p.get("isDraft") else "obert (pendent)")

    by_agent: dict[str, list[tuple[int, str]]] = {}
    pr_agents: dict[int, set[str]] = {}
    for n in status:
        d = gh_json(["pr", "view", str(n), "--json", "commits"])
        commits = d.get("commits", []) if isinstance(d, dict) else []
        for c in commits:
            head = c.get("messageHeadline", "")
            for a in (c.get("authors") or []):
                name = (a.get("name") or a.get("login") or "").strip()
                if not name or _is_merger(name):
                    continue
                if (n, head) not in by_agent.get(name, []):
                    by_agent.setdefault(name, []).append((n, head))
                pr_agents.setdefault(n, set()).add(name)

    prs = [{"n": n, "title": title.get(n, ""), "status": status[n],
            "url": link.get(n, ""), "agents": sorted(pr_agents.get(n, set()))}
           for n in sorted(status, reverse=True)]
    return by_agent, prs


def collect_bitacora() -> list[tuple[str, str]]:
    raw = sh(["git", "log", f"--since={SINCE.isoformat()}", "--name-only",
              "--pretty=format:", "--", "bitacora/"])
    files = sorted({l.strip() for l in raw.splitlines() if l.strip().endswith(".md")})
    entries: list[tuple[str, str]] = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                entries.append((f, fh.read().strip()))
        except OSError:
            pass
    return entries


def after(ts: str | None) -> bool:
    d = parse_iso(ts)
    return bool(d and d >= SINCE_UTC)


BY_AGENT, PRS = collect_work()
BITACORA = collect_bitacora()


# --------------------------------------------------------------------------- #
# Resum executiu (veu de Talaia, via OpenRouter) -- opcional, degrada be
# --------------------------------------------------------------------------- #
def narrative(facts: str) -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    system = (
        "Ets Talaia, coordinadora del projecte riusdegent (observatori de dades "
        "territorials). Escrius el resum executiu del dia per a la Bea (direccio "
        "humana). Veu: catala, sobria, honesta (inclosos els problemes i els 'no'), "
        "ma esquerra + exigencia. 5-9 linies. Destaca el que importa: que s'ha "
        "aconseguit, troballes, decisions i problemes oberts. NO inventis res: "
        "fes servir nomes els fets que et passo. Comenca directe, sense saluts."
    )
    body = json.dumps({
        "model": os.environ.get("REPORT_MODEL", "openai/gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": facts[:12000]},
        ],
        "max_tokens": 700,
        "temperature": 0.4,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/zigiella/datapoble",
            "X-Title": "riusdegent daily report",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001
        print(f"[info] resum executiu omes ({e}).")
        return None


# --------------------------------------------------------------------------- #
# Construccio del cos (text pla + HTML del mateix material)
# --------------------------------------------------------------------------- #
def build_facts_text() -> str:
    L: list[str] = []
    if BY_AGENT:
        L.append("## Que ha fet cadascu (per agent)")
        for agent in sorted(BY_AGENT):
            items = BY_AGENT[agent]
            L.append(f"- {agent} ({len(items)} commits):")
            L += [f"    - PR#{n} · {head}" for n, head in items[:25]]
    if PRS:
        L.append("\n## PRs del dia")
        for p in PRS:
            ags = ", ".join(p["agents"]) if p["agents"] else "?"
            L.append(f"- #{p['n']} [{p['status']}] {p['title']} — {ags}")
    if BITACORA:
        L.append("\n## Entrades de bitacola del dia (informes dels agents)")
        for f, content in BITACORA:
            L.append(f"\n### {f}\n{content}")
    if not (BY_AGENT or PRS or BITACORA):
        L.append("_Avui no hi ha activitat registrada en aquesta finestra._")
    return "\n".join(L)


def build_text(summary: str | None, facts: str) -> str:
    head = f"RESUM DIARI · riusdegent · {NOW.strftime('%d/%m/%Y')}\n"
    head += f"(activitat des de {SINCE.strftime('%d/%m %H:%M')} fins ara)\n"
    parts = [head]
    if summary:
        parts.append("## El que importa avui (Talaia)\n" + summary)
    parts.append(facts)
    parts.append("\n--\nGenerat automaticament des de github.com/zigiella/datapoble "
                 "(Actions). Font: commits identity-inline + PRs + bitacola.")
    return "\n\n".join(parts)


def build_html(summary: str | None, facts_text: str) -> str:
    def esc(s: str) -> str:
        return escape(s, quote=False)

    css = (
        "body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#1B212A;"
        "max-width:720px;margin:0 auto;padding:16px;line-height:1.55}"
        "h1{font-size:20px;border-bottom:3px solid #2F6B4F;padding-bottom:6px}"
        "h2{font-size:15px;color:#255741;margin-top:24px}"
        ".sum{background:#F6F7F9;border-left:4px solid #C75D34;padding:12px 16px;"
        "border-radius:6px;white-space:pre-wrap}"
        "pre{background:#F6F7F9;padding:12px;border-radius:6px;white-space:pre-wrap;"
        "font-size:13px;overflow-x:auto}"
        ".foot{color:#6B7889;font-size:12px;margin-top:24px;border-top:1px solid #D9DDE4;"
        "padding-top:8px}"
    )
    html = [f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"]
    html.append(f"<h1>🌊 Resum diari · riusdegent · {NOW.strftime('%d/%m/%Y')}</h1>")
    html.append(f"<p style='color:#6B7889'>Activitat des de {SINCE.strftime('%d/%m %H:%M')} fins ara.</p>")
    if summary:
        html.append("<h2>El que importa avui</h2>")
        html.append(f"<div class='sum'>{esc(summary)}</div>")
    html.append("<h2>Detall</h2>")
    html.append(f"<pre>{esc(facts_text)}</pre>")
    html.append("<div class='foot'>Generat automaticament des de "
                "<a href='https://github.com/zigiella/datapoble'>zigiella/datapoble</a> "
                "(GitHub Actions). Font: commits identity-inline + PRs + bitacola.</div>")
    html.append("</body></html>")
    return "".join(html)


# --------------------------------------------------------------------------- #
# Enviament
# --------------------------------------------------------------------------- #
def send(subject: str, text: str, html: str) -> None:
    to = os.environ.get("REPORT_TO", "zigiella@gmail.com")
    frm = os.environ.get("REPORT_FROM", to)
    pw = os.environ.get("GMAIL_APP_PASSWORD")

    if os.environ.get("DRY_RUN") == "1" or not pw:
        why = "DRY_RUN=1" if os.environ.get("DRY_RUN") == "1" else "sense GMAIL_APP_PASSWORD"
        print(f"=== NO S'ENVIA ({why}) — previsualitzacio ===")
        print("Subject:", subject)
        print(text[:6000])
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Talaia · riusdegent", frm))
    msg["To"] = to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(frm, pw)
        s.sendmail(frm, [to], msg.as_string())
    print(f"[ok] enviat a {to}")


def main() -> int:
    facts = build_facts_text()
    summary = narrative(
        f"Data: {NOW.strftime('%d/%m/%Y')}. Finestra des de {SINCE.isoformat()}.\n\n{facts}"
    )
    subject = f"🌊 riusdegent · resum del {NOW.strftime('%d/%m/%Y')}"
    text = build_text(summary, facts)
    html = build_html(summary, facts)
    send(subject, text, html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
