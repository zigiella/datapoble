#!/usr/bin/env python3
"""Pipeline de PRODUCCIÓ de la lectura de fitxa (§3): escriptor (es) → traductor (ca).

Decisió Bea (2026-06-13): els prompts de IA es fan SEMPRE en castellà amb un model potent
(escriptor = claude-opus-4.8, el guanyador de l'eval) i després es tradueix al català amb un
model més barat (sonnet-4.6), amb re-chequeo determinista que els NÚMEROS no canvien.

Per a cada municipi: assembla el full de fets → escriptor opus-4.8 amb la guia ES → JSON en
castellà → verificador (regles dures, llista negra ES, confabulació de xifres) amb RE-INTENT
(fins a MAX_RETRY, retroalimentant l'error) → traductor sonnet-4.6 → JSON en català →
verificador (llista negra CA) + preservació de números (els del ca == els de l'es). Si una
banda no supera la verificació després dels re-intents, s'escriu una LECTURA DE RESERVA
determinista (sense xifres inventades, `_gen="fallback"`) perquè la UI no mostri mai
al·lucinacions ni quedi trencada.

Sortida COMMITTEJADA i versionada: `data/web/lectures.bergueda.json`, amb forma
`{ine5: {"ca": <lectura>, "es": <lectura>}}`. La UI (fitxa de municipi) en llegeix la branca
del seu locale; `copy-data.mjs` la copia a `static/data/`. Els bolcats crus (es/ca) també es
desen a `data/eval/` (gitignored) per a auditoria.

Requereix OPENROUTER_API_KEY (a Actions; MAI es committeja). Ús:
    python tools/gen_fitxa.py                 # els 31 munis del Berguedà (del dataset)
    python tools/gen_fitxa.py --muni 25100    # un sol municipi (smoke / cèntims)
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
    DATASET, ETCA, NUM_RE, REQUIRED, _candidates, _fact_numbers,
    assemble, call_model, load_territorial,
)

REPO = Path(__file__).resolve().parents[1]
GUIA_ES = REPO / "docs" / "guia-escritura-es.md"
OUTDIR = REPO / "data" / "eval"
ARTIFACT = REPO / "data" / "web" / "lectures.bergueda.json"

WRITER = "anthropic/claude-opus-4.8"
TRANSLATOR = "anthropic/claude-sonnet-4.6"
MAX_RETRY = 2  # re-intents per banda (es i ca) retroalimentant l'error de verificació

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

INSTR_ES = ("Escribe la lectura pública de este municipio siguiendo EXACTAMENTE la guía del system. "
            "Responde SOLO con el JSON del esquema, sin texto fuera.\n\nPLIEGO DE HECHOS:\n")


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
    obj = extract_obj(content)
    res["valid_json"] = obj is not None
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


def hard_fail(v: dict) -> bool:
    """Una sortida és inacceptable si: no és JSON, falten camps, usa la llista negra, posa
    vaguedats en claims de mesura, o inventa xifres fora del full (confabulació)."""
    return bool(not v["valid_json"] or v["missing"] or v["blacklist"]
                or v["hedge_mesura"] or v["unmatched"] or not v["contra_ok"])


def extract_obj(txt: str) -> dict | None:
    s, e = txt.find("{"), txt.rfind("}")
    if s >= 0 and e > s:
        try:
            return json.loads(txt[s:e + 1])
        except json.JSONDecodeError:
            return None
    return None


def fact_val(facts: dict, clau: str):
    for f in facts.get("fets", []):
        if f.get("clau") == clau:
            return f.get("valor")
    return None


def fallback_obj(facts: dict, lang: str) -> dict:
    """Lectura de RESERVA determinista: cap xifra inventada, cap relat. La UI la detecta
    (`_gen="fallback"`, veredicte buit) i degrada (mostra els cinc números i la maquinària,
    sense la lectura narrativa). Honest: val més «no en tenim» que una al·lucinació."""
    conf = fact_val(facts, "confianca")
    motiu = ("redacció automàtica de reserva: la sortida del model no va superar la verificació"
             if lang == "ca"
             else "redacción automática de reserva: la salida del modelo no superó la verificación")
    return {
        "ine5": facts["ine5"],
        "veredicte": {"text": "", "evidencia": []},
        "perfil_public": "",
        "lectures": {"ciutadania": [], "visitant": [], "govern": []},
        "contra_lectura": {"text": "", "evidencia": []},
        "dades_que_falten": [],
        "preguntes": {"propies": [], "comarca": [], "miralls": []},
        "confianca": {"nivell": conf or "baixa", "motius": [motiu]},
        "_gen": "fallback",
    }


def _retry_note(v: dict, only_es=None, only_ca=None) -> str:
    probs = []
    if not v.get("valid_json"):
        probs.append("el JSON no era válido")
    if v.get("missing"):
        probs.append("faltaban campos obligatorios: " + ", ".join(v["missing"]))
    if v.get("blacklist"):
        probs.append("usaste términos/signos prohibidos: " + ", ".join(v["blacklist"]))
    if v.get("hedge_mesura"):
        probs.append("usaste vaguedades en claims de medida (to=mesura): " + ", ".join(v["hedge_mesura"]))
    if v.get("unmatched"):
        probs.append("escribiste números que NO están en el pliego de hechos: " + ", ".join(v["unmatched"][:6]))
    if not v.get("contra_ok", True):
        probs.append("falta la contra_lectura (hay divergencia pernocta/carga y debe explicarse)")
    if only_es:
        probs.append("perdiste estos números respecto al original: " + ", ".join(map(str, only_es[:6])))
    if only_ca:
        probs.append("añadiste estos números que no estaban: " + ", ".join(map(str, only_ca[:6])))
    if not probs:
        return ""
    return ("\n\nNOTA DE CORRECCIÓN (intento previo): falló la verificación porque "
            + "; ".join(probs) + ". Corrige SOLO eso, mantén el resto igual. "
            "No inventes ningún número fuera del pliego de hechos.")


def gen_es(facts: dict, guia: str) -> tuple[str | None, dict]:
    """Escriptor (es) amb re-intent retroalimentat. Torna (text|None, última_verif)."""
    base = INSTR_ES + json.dumps(facts, ensure_ascii=False, indent=2)
    last: dict = {}
    for attempt in range(MAX_RETRY + 1):
        prompt = base + (_retry_note(last) if attempt and last else "")
        try:
            txt, _, _ = call_model(WRITER, guia, prompt)
        except Exception as ex:  # xarxa / API / rate-limit → compta com a falla, re-intenta
            last = {"valid_json": False, "missing": [], "unmatched": [], "blacklist": [f"ERR:{ex}"[:60]],
                    "hedge_mesura": [], "contra_ok": True}
            continue
        v = verify(txt, facts, BL_ES, HEDGE_ES)
        if not hard_fail(v):
            return txt, v
        last = v
    return None, last


def gen_ca(es_txt: str, facts: dict) -> tuple[str | None, dict]:
    """Traductor (ca) amb re-intent: verificació + preservació de números es↔ca."""
    last: dict = {}
    only_es: list = []
    only_ca: list = []
    for attempt in range(MAX_RETRY + 1):
        sys_msg = TRAD_SYS + (_retry_note(last, only_es, only_ca) if attempt else "")
        try:
            txt, _, _ = call_model(TRANSLATOR, sys_msg, es_txt)
        except Exception as ex:
            last = {"valid_json": False, "missing": [], "unmatched": [], "blacklist": [f"ERR:{ex}"[:60]],
                    "hedge_mesura": [], "contra_ok": True}
            only_es, only_ca = [], []
            continue
        v = verify(txt, facts, BL_CA, HEDGE_CA)
        only_es = sorted(_nums(es_txt) - _nums(txt))
        only_ca = sorted(_nums(txt) - _nums(es_txt))
        if not hard_fail(v) and not only_es and not only_ca:
            return txt, v
        last = v
    return None, last


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gen_fitxa")
    ap.add_argument("--muni", action="append", help="ine5 (repetible). Buit = els 31 del dataset.")
    args = ap.parse_args(argv)
    if "OPENROUTER_API_KEY" not in os.environ:
        print("FALLA: cal OPENROUTER_API_KEY", file=sys.stderr)
        return 2

    ds = json.loads(DATASET.read_text(encoding="utf-8"))
    guia = GUIA_ES.read_text(encoding="utf-8")
    etca = json.loads(ETCA.read_text(encoding="utf-8")) if ETCA.exists() else {}
    terr = load_territorial()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)

    munis = args.muni or sorted(ds["municipis"].keys())
    artifact: dict = {}
    n_fb_es = n_fb_ca = 0
    print(f"Generant lectures de {len(munis)} municipis (escriptor {WRITER} → traductor {TRANSLATOR})…\n")

    for i, ine5 in enumerate(munis, 1):
        facts = assemble(ine5, ds, etca, terr)
        nom = facts["municipi"]

        # 1) Escriptor (es)
        es_txt, es_v = gen_es(facts, guia)
        if es_txt:
            (OUTDIR / f"{ine5}__ES_opus-4.8.txt").write_text(es_txt, encoding="utf-8")
            es_obj = extract_obj(es_txt)
        else:
            es_obj = None
        if es_obj is None:
            es_obj = fallback_obj(facts, "es")
            n_fb_es += 1
        else:
            es_obj["_gen"] = "model"

        # 2) Traductor (ca) — només si l'es és bo (traduir un fallback no té sentit)
        if es_txt and es_obj.get("_gen") == "model":
            ca_txt, ca_v = gen_ca(es_txt, facts)
            if ca_txt:
                (OUTDIR / f"{ine5}__CA_sonnet-4.6.txt").write_text(ca_txt, encoding="utf-8")
                ca_obj = extract_obj(ca_txt)
            else:
                ca_obj = None
            if ca_obj is None:
                ca_obj = fallback_obj(facts, "ca")
                n_fb_ca += 1
            else:
                ca_obj["_gen"] = "model"
        else:
            ca_obj = fallback_obj(facts, "ca")
            n_fb_ca += 1

        artifact[ine5] = {"ca": ca_obj, "es": es_obj}
        es_tag = "model" if es_obj.get("_gen") == "model" else f"FALLBACK({_summ(es_v)})"
        ca_tag = "model" if ca_obj.get("_gen") == "model" else "FALLBACK"
        print(f"  [{i:2}/{len(munis)}] {nom:24} ({ine5})  es={es_tag}  ca={ca_tag}")

    ARTIFACT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nArtefacte: {ARTIFACT.relative_to(REPO).as_posix()}  ({len(artifact)} munis; "
          f"reserva es={n_fb_es} ca={n_fb_ca})")
    print(f"Bolcats crus a {OUTDIR.relative_to(REPO).as_posix()}/ (local).")
    return 0


def _summ(v: dict) -> str:
    bits = []
    if not v.get("valid_json"):
        bits.append("json")
    if v.get("missing"):
        bits.append("falten")
    if v.get("blacklist"):
        bits.append("negra")
    if v.get("hedge_mesura"):
        bits.append("hedge")
    if v.get("unmatched"):
        bits.append("xifres")
    return ",".join(bits) or "?"


if __name__ == "__main__":
    raise SystemExit(main())
