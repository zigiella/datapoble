#!/usr/bin/env python3
"""Pipeline de generació de la lectura de fitxa (§3): escriptor (es) → traductor (ca).

Decisió Bea (2026-06-13): els prompts de IA es fan SEMPRE en castellà amb un model potent
(escriptor = claude-opus-4.8, el guanyador de l'eval) i després es tradueix al català amb un
model més barat (sonnet-4.6), amb re-chequeo determinista que els NÚMEROS no canvien.

Per a cada municipi: assembla el full de fets → escriptor opus-4.8 amb la guia ES → JSON en
castellà → verificador (regles dures, llista negra ES) → traductor sonnet-4.6 → JSON en català
→ verificador (llista negra CA) + preservació de números (els del ca == els de l'es).

Requereix OPENROUTER_API_KEY (a Actions). Sortides LOCALS a data/eval/ (gitignored). Ús:
    python tools/gen_fitxa.py                 # 3 munis
    python tools/gen_fitxa.py --muni 08052
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_writer import (  # noqa: E402
    DATASET, ETCA, MUNIS, NUM_RE, REQUIRED, _candidates, _fact_numbers,
    assemble, call_model, load_territorial,
)

REPO = Path(__file__).resolve().parents[1]
GUIA_ES = REPO / "docs" / "guia-escritura-es.md"
OUTDIR = REPO / "data" / "eval"

WRITER = "anthropic/claude-opus-4.8"
TRANSLATOR = "anthropic/claude-sonnet-4.6"

BL_ES = re.compile(
    r"\b(debido a|a causa de|provoca|causa que|el más|la más|el mejor|el peor|sin duda|clarísimo|"
    r"revoluciona|cambia las reglas|marca un antes y un después|lleva al siguiente nivel|reinventa|"
    r"genera valor|generar valor|cambio de paradigma|transformación integral|a nivel de)\b", re.I)
BL_CA = re.compile(
    r"\b(a causa de|degut a|provoca|causa que|el més|la més|el millor|el pitjor|sens dubte|claríssim|"
    r"revoluciona|canvia les regles|marca un abans i un després|porta al següent nivell|reinventa|"
    r"genera valor|generar valor|canvi de paradigma|transformació integral|a nivell de)\b", re.I)
# Hedges: prohibits NOMÉS dins de claims amb to="mesura" (dada assentada). A to="inferencia" són obligats.
HEDGE_ES = re.compile(
    r"\b(podría|podrían|puede ayudar|pueden ayudar|tiende a|tienden a|sería útil|en cierto modo|"
    r"de alguna manera|quizá|quizás|tal vez|aproximadamente|alrededor de|en torno a|parece que)\b", re.I)
HEDGE_CA = re.compile(
    r"\b(podria|podrien|pot ajudar|poden ajudar|tendeix a|tendeixen a|seria útil|en certa manera|"
    r"d'alguna manera|potser|tal vegada|aproximadament|al voltant de|sembla que)\b", re.I)

TRAD_SYS = (
    "Ets traductor tècnic. Et donen un JSON amb text en CASTELLÀ. Tradueix al CATALÀ NOMÉS els "
    "valors de text redactat (els camps `text`, `perfil_public`, `motius`, i els arrays "
    "`dades_que_falten` i `preguntes`). Mantén EXACTAMENT IGUAL, sense tocar: totes les claus del "
    "JSON, els valors del camp `to`, els arrays `evidencia`, el camp `ine5`, el `nivell` de "
    "confiança, i TOTS ELS NÚMEROS (xifres, percentatges, rangs). No reordenis res. Respon NOMÉS "
    "amb el JSON, sense text fora."
)


def _nums(text: str) -> set[float]:
    out: set[float] = set()
    for tok in NUM_RE.findall(text):
        for c in _candidates(tok):
            if not (2018 <= c <= 2027):
                out.add(round(c, 2))
    return out


def verify(content: str, facts: dict, bl: re.Pattern, hedge: re.Pattern | None = None) -> dict:
    res = {"valid_json": False, "missing": [], "unmatched": [], "blacklist": [],
           "hedge_mesura": [], "contra_ok": True}
    s, e = content.find("{"), content.rfind("}")
    obj = None
    if s >= 0 and e > s:
        try:
            obj = json.loads(content[s:e + 1])
            res["valid_json"] = True
        except json.JSONDecodeError:
            pass
    if obj:
        res["missing"] = [f for f in REQUIRED if f not in obj]
        if facts.get("divergencia_pernocta_carrega"):
            cl = obj.get("contra_lectura") or {}
            res["contra_ok"] = bool(cl.get("text") if isinstance(cl, dict) else cl)
        # Hedge conscient del `to`: «podria/tendeix a…» NOMÉS és falla dins d'un claim to="mesura".
        if hedge is not None:
            lec = obj.get("lectures")
            hits = set()
            for claims in (lec.values() if isinstance(lec, dict) else []):
                for c in (claims if isinstance(claims, list) else []):
                    if isinstance(c, dict) and c.get("to") == "mesura":
                        hits.update(m.group(0).lower() for m in hedge.finditer(c.get("text") or ""))
            res["hedge_mesura"] = sorted(hits)
    allowed = _fact_numbers(facts)
    for tok in NUM_RE.findall(content):
        cands = {c for c in _candidates(tok) if not (2018 <= c <= 2027)}
        if cands and not any(abs(c - a) <= max(1.0, 0.02 * abs(c)) for c in cands for a in allowed):
            res["unmatched"].append(tok.strip())
    bl_hits = {m.group(0).lower() for m in bl.finditer(content)}
    if "—" in content:  # guió llarg (—) prohibit al text de la fitxa
        bl_hits.add("—")
    res["blacklist"] = sorted(bl_hits)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gen_fitxa")
    ap.add_argument("--muni", action="append")
    args = ap.parse_args(argv)
    if "OPENROUTER_API_KEY" not in os.environ:
        print("FALLA: cal OPENROUTER_API_KEY", file=sys.stderr)
        return 2

    ds = json.loads(DATASET.read_text(encoding="utf-8"))
    guia = GUIA_ES.read_text(encoding="utf-8")
    etca = json.loads(ETCA.read_text(encoding="utf-8")) if ETCA.exists() else {}
    terr = load_territorial()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    instr = ("Escribe la lectura pública de este municipio siguiendo EXACTAMENTE la guía del system. "
             "Responde SOLO con el JSON del esquema, sin texto fuera.\n\nPLIEGO DE HECHOS:\n")

    for ine5 in (args.muni or MUNIS):
        facts = assemble(ine5, ds, etca, terr)
        nom = facts["municipi"]
        # 1) Escriptor (es)
        es_txt, es_u, es_dt = call_model(WRITER, guia, instr + json.dumps(facts, ensure_ascii=False, indent=2))
        (OUTDIR / f"{ine5}__ES_opus-4.8.txt").write_text(es_txt, encoding="utf-8")
        ves = verify(es_txt, facts, BL_ES, HEDGE_ES)
        # 2) Traductor (ca)
        ca_txt, ca_u, ca_dt = call_model(TRANSLATOR, TRAD_SYS, es_txt)
        (OUTDIR / f"{ine5}__CA_sonnet-4.6.txt").write_text(ca_txt, encoding="utf-8")
        vca = verify(ca_txt, facts, BL_CA, HEDGE_CA)
        # Preservació de números es↔ca
        only_es = _nums(es_txt) - _nums(ca_txt)
        only_ca = _nums(ca_txt) - _nums(es_txt)
        nums_ok = not only_es and not only_ca
        print(f"\n=== {nom} ({ine5}) ===")
        print(f"  ESCRIPTOR opus-4.8 (es):  json={ves['valid_json']} falten={ves['missing']} "
              f"xifres_no_verif={len(ves['unmatched'])} negra={ves['blacklist']} hedge_mesura={ves['hedge_mesura']} "
              f"contra_ok={ves['contra_ok']} {es_dt:.0f}s")
        print(f"  TRADUCTOR sonnet-4.6 (ca): json={vca['valid_json']} negra={vca['blacklist']} "
              f"hedge_mesura={vca['hedge_mesura']} "
              f"numeros_preservats={nums_ok} {'(diff es:' + str(sorted(only_es)) + ' ca:' + str(sorted(only_ca)) + ')' if not nums_ok else ''} {ca_dt:.0f}s")
    print(f"\nSortides a {OUTDIR.relative_to(REPO).as_posix()}/ (local).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
