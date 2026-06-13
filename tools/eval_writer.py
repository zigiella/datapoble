#!/usr/bin/env python3
"""Eval del motor d'escriptura de la fitxa (§3) — compara models via OpenRouter.

Per a un subconjunt de municipis del Berguedà, assembla el «full de fets», demana a cada
model una lectura pública (JSON) seguint la guia (`docs/guia-escriptura.md`) i la passa pel
**verificador determinista** (cada xifra de la sortida ha d'existir al full de fets; camps
obligatoris; llista negra; contra-lectura si divergència). Reporta, per model: validesa,
xifres no verificades (confabulació), hits de llista negra, cost i latència.

Requereix `OPENROUTER_API_KEY` a l'entorn (NO es committeja). Les sortides es desen LOCALMENT
a `data/eval/` (gitignored). Cost d'una passada: cèntims.

Ús:  python tools/eval_writer.py            # tots els munis × tots els models
     python tools/eval_writer.py --muni 08052 --model anthropic/claude-opus-4.8
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATASET = REPO / "data" / "web" / "municipis.bergueda.json"
GUIA = REPO / "docs" / "guia-escriptura.md"
ETCA = REPO / "data" / "web" / "etca-validacio.json"
TERRITORIAL = REPO / "data" / "territorial" / "tipus_territorial_bergueda.csv"
OUTDIR = REPO / "data" / "eval"

MODELS = [
    "openai/gpt-5.5-pro",
    "anthropic/claude-opus-4.8",
    "anthropic/claude-opus-4.7",
    "anthropic/claude-sonnet-4.6",
    "minimax/minimax-m3",
    "deepseek/deepseek-v4-pro",
]
MUNIS = ["25100", "08022", "08052"]  # Gósol, Berga, Castellar de n'Hug

# Mètriques que entren al full de fets (curades; el writer en treu el relat).
FACT_KEYS = [
    "poblacio", "pct_noprincipal", "hab_per_hab", "index_envelliment",
    "rtc_per_1000hab", "kwh_hab", "kg_hab_any", "vidre_hab",
    "poblacio_pernocta_est", "gap_pernocta_pct", "carrega_funcional_est",
    "index_turisme", "restauracio_estab", "IETR", "IETR_stock", "IETR_impact",
    "tipologia", "confianca", "confianca_score", "divergencia_senyals",
]
GAP_SENS = 0.10  # banda ±10% de base (igual que la fitxa)


def naturesa(source: str) -> str:
    return "inferencia" if "derivat" in (source or "").lower() else "mesura"


def assemble(ine5: str, ds: dict, etca: dict, terr: dict) -> dict:
    row = ds["municipis"][ine5]
    v = row["values"]
    fets = []
    for k in FACT_KEYS:
        val = v.get(k)
        if val is None:
            continue
        fets.append({"clau": k, "etiqueta": ds["metrics"][k]["label"]["ca"], "valor": val, "to": naturesa(ds["metrics"][k]["source"])})
    out = {"municipi": row["nom"], "ine5": ine5, "fets": fets}

    # Computats: rang de pernocta + «no concloent» + divergència (igual que la fitxa).
    est = v.get("poblacio_pernocta_est")
    padro = v.get("poblacio")
    if isinstance(est, (int, float)) and isinstance(padro, (int, float)) and padro:
        low, high = est / (1 + GAP_SENS), est / (1 - GAP_SENS)
        pct_low, pct_high = (low / padro - 1) * 100, (high / padro - 1) * 100
        out["pernocta_rang"] = {"baix": round(low), "alt": round(high), "punt_mig": est,
                                "gap_pct_baix": round(pct_low, 1), "gap_pct_alt": round(pct_high, 1),
                                "no_concloent": bool(pct_low < 0 < pct_high)}
    carr = v.get("carrega_funcional_est")
    if isinstance(est, (int, float)) and isinstance(carr, (int, float)):
        out["divergencia_pernocta_carrega"] = bool(est > carr)
    # ETCA (si el municipi hi és cobert).
    em = next((m for m in etca.get("municipis", []) if m["ine5"] == ine5 and m.get("covered")), None)
    if em:
        out["etca_idescat"] = {"poblacio_etca": em["etca"], "error_nostre_pct": em["err_pernocta_pct"]}
    if ine5 in terr:
        out["tipus_territorial"] = terr[ine5]
    return out


def load_territorial() -> dict:
    out = {}
    if TERRITORIAL.exists():
        import csv
        for r in csv.DictReader(TERRITORIAL.open(encoding="utf-8")):
            out[r["ine5"]] = r["tipus_territorial"]
    return out


# ---- Verificador determinista ----
NUM_RE = re.compile(r"[-+]?\d[\d.]*(?:,\d+)?%?")
BLACKLIST = re.compile(r"\b(perquè|a causa de|degut a|provoca|causa que|el més|la més|el millor|el pitjor|sens dubte|claríssim)\b", re.I)
REQUIRED = ["veredicte", "lectures", "contra_lectura", "preguntes", "confianca"]


def _candidates(tok: str) -> set[float]:
    """Valors candidats d'un token, provant les DUES convencions (català: «.» milers / «,»
    decimal; anglès: «,» milers / «.» decimal) → robust a com escrigui el model."""
    t = tok.strip().replace("%", "").replace("+", "").replace(" ", "")
    out: set[float] = set()
    for cand in (t.replace(".", "").replace(",", "."), t.replace(",", "")):
        try:
            out.add(float(cand))
        except ValueError:
            pass
    return out


def _fact_numbers(facts: dict) -> set[float]:
    nums: set[float] = set()

    def add(x):
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            nums.add(float(x))
            nums.add(float(round(x)))

    def walk(o):
        if isinstance(o, dict):
            for val in o.values():
                walk(val)
        elif isinstance(o, list):
            for it in o:
                walk(it)
        else:
            add(o)
    walk(facts)
    try:
        nums.add(float(int(facts.get("ine5", "x"))))  # l'ine5 no és confabulació
    except (ValueError, TypeError):
        pass
    return nums


def verify(content: str, facts: dict) -> dict:
    res = {"valid_json": False, "missing_fields": [], "unmatched_numbers": [], "blacklist": [], "contra_ok": True}
    # Extreu el bloc JSON.
    s, e = content.find("{"), content.rfind("}")
    obj = None
    if s >= 0 and e > s:
        try:
            obj = json.loads(content[s:e + 1])
            res["valid_json"] = True
        except json.JSONDecodeError:
            pass
    if obj:
        res["missing_fields"] = [f for f in REQUIRED if f not in obj]
        if facts.get("divergencia_pernocta_carrega"):
            cl = obj.get("contra_lectura") or {}
            res["contra_ok"] = bool((cl.get("text") if isinstance(cl, dict) else cl))
    # Xifres no verificades (confabulació): compara amb els fets (tolerància, doble convenció).
    allowed = _fact_numbers(facts)
    for tok in NUM_RE.findall(content):
        cands = {c for c in _candidates(tok) if not (2018 <= c <= 2027)}  # ignora anys
        if not cands:
            continue
        if not any(abs(c - a) <= max(1.0, 0.02 * abs(c)) for c in cands for a in allowed):
            res["unmatched_numbers"].append(tok.strip())
    res["blacklist"] = list({m.group(0).lower() for m in BLACKLIST.finditer(content)})
    return res


def call_model(model: str, system: str, user: str) -> tuple[str, dict, float]:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.3, "max_tokens": 4096,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://riusdegent.cat", "X-Title": "riusdegent writer eval"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    dt = time.time() - t0
    if d.get("error"):  # OpenRouter pot tornar error dins un cos 200
        raise RuntimeError(str(d["error"])[:160])
    msg = (d.get("choices") or [{}])[0].get("message", {})
    # Models de raonament poden deixar `content` buit (tokens gastats en raonament): no peta,
    # cau a string buida → el verificador ho marca com a JSON invàlid (sortida fallida).
    content = msg.get("content") or msg.get("reasoning") or ""
    return content, d.get("usage", {}), dt


def pricing() -> dict:
    try:
        req = urllib.request.Request("https://openrouter.ai/api/v1/models",
                                     headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return {m["id"]: m.get("pricing", {}) for m in d.get("data", [])}
    except Exception:
        return {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="eval_writer")
    ap.add_argument("--muni", action="append")
    ap.add_argument("--model", action="append")
    args = ap.parse_args(argv)
    if "OPENROUTER_API_KEY" not in os.environ:
        print("FALLA: cal OPENROUTER_API_KEY a l'entorn", file=sys.stderr)
        return 2

    ds = json.loads(DATASET.read_text(encoding="utf-8"))
    guia = GUIA.read_text(encoding="utf-8")
    etca = json.loads(ETCA.read_text(encoding="utf-8")) if ETCA.exists() else {}
    terr = load_territorial()
    price = pricing()
    OUTDIR.mkdir(parents=True, exist_ok=True)

    munis = args.muni or MUNIS
    models = args.model or MODELS
    instr = ("Escriu la lectura pública d'aquest municipi seguint EXACTAMENT la guia del system. "
             "Respon NOMÉS amb el JSON de l'esquema, sense cap text fora.\n\nFULL DE FETS:\n")

    summary = []
    for ine5 in munis:
        facts = assemble(ine5, ds, etca, terr)
        user = instr + json.dumps(facts, ensure_ascii=False, indent=2)
        for model in models:
            tag = f"{ine5}__{model.replace('/', '_')}"
            try:
                content, usage, dt = call_model(model, guia, user)
            except Exception as ex:
                print(f"  ERR {tag}: {ex}")
                summary.append({"muni": facts["municipi"], "model": model, "error": str(ex)[:80]})
                continue
            (OUTDIR / f"{tag}.txt").write_text(content, encoding="utf-8")
            ver = verify(content, facts)
            pr = price.get(model, {})
            cost = (usage.get("prompt_tokens", 0) * float(pr.get("prompt", 0) or 0)
                    + usage.get("completion_tokens", 0) * float(pr.get("completion", 0) or 0))
            row = {"muni": facts["municipi"], "model": model,
                   "json_ok": ver["valid_json"], "falten": len(ver["missing_fields"]),
                   "xifres_no_verif": len(ver["unmatched_numbers"]),
                   "llista_negra": len(ver["blacklist"]), "contra_ok": ver["contra_ok"],
                   "tok_out": usage.get("completion_tokens", 0), "cost_usd": round(cost, 4), "lat_s": round(dt, 1)}
            summary.append(row)
            flags = []
            if not ver["valid_json"]:
                flags.append("JSON-no")
            if ver["missing_fields"]:
                flags.append("falten:" + ",".join(ver["missing_fields"]))
            if ver["unmatched_numbers"]:
                flags.append(f"xifres?:{ver['unmatched_numbers'][:5]}")
            if ver["blacklist"]:
                flags.append("negra:" + ",".join(ver["blacklist"]))
            print(f"  {facts['municipi']:20} {model:32} json={ver['valid_json']!s:5} "
                  f"xifres_no_verif={len(ver['unmatched_numbers']):2} negra={len(ver['blacklist'])} "
                  f"${cost:.4f} {dt:.0f}s {'· ' + '; '.join(flags) if flags else 'OK'}")
    (OUTDIR / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSortides a {OUTDIR.relative_to(REPO).as_posix()}/ (local). Resum: _summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
