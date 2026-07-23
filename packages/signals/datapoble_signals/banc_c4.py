"""Banc C4 — parser i validador del full d'etiquetatge (transcripció MECÀNICA).

El full `docs/ajuntaments/banc-c4-etiquetatge.md` és la font de veritat de l'etiquetatge
HUMÀ (Bea, C4 §2 v2: cap agent posa cap golden). Aquest mòdul el transcriu mecànicament
al banc JSON congelable i VALIDA que l'etiquetatge sigui complet i coherent — mai
l'interpreta ni el corregeix.

Regles de validació (C4 §2 v2 + full v2):
- Dues capes: A (files 1–26, flux cru) i B (files 27+, composició per programes).
- `golden` ∈ {elegible, descartable, frontera, fora} — `fora` només vol dir «no entra al
  banc» (amb motiu); no és una classe d'avaluació.
- `semafor` ∈ {verd, groc} NOMÉS quan golden=elegible (buit altrament).
- `motiu` OBLIGATORI a frontera i fora; recomanat a tot arreu (warning si falta).
- Solapament A∩B (C4 §2 v2): una fitxa duplicada (mateix codigoBDNS) s'etiqueta UN cop;
  la seva etiqueta compta al denominador B i al FP-rate d'A alhora.

El recompte que produeix és el que Talaia presenta a Bea abans de CONGELAR. Després de la
congelació, el test de fidelitat (tests/test_banc_c4.py) verifica que el JSON congelat
coincideix amb el full — cap deriva silenciosa.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
FULL_PATH = _REPO_ROOT / "docs" / "ajuntaments" / "banc-c4-etiquetatge.md"

# Banc CONGELAT (veritat d'or del radar). Viu DINS el paquet perquè el pipeline el
# consumeixi sense dependre de l'arbre del repo; el full markdown segueix sent la
# font humana, aquest JSON n'és la transcripció mecànica i immutable.
BANC_CONGELAT_PATH = Path(__file__).resolve().parent / "banc_c4_congelat.json"

GOLDENS = {"elegible", "descartable", "frontera", "fora"}
SEMAFORS = {"verd", "groc"}

# Fila de la taula: | n | [codi](url) | convocant | objecte | benef | ambit | termini | g | s | m |
_ROW = re.compile(
    r"^\|\s*(\d+)\s*\|\s*\[(\d+)\]\([^)]+\)\s*\|"  # num, codigoBDNS
    r"([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|"  # convocant, objecte, benef, ambit, termini
    r"([^|]*)\|([^|]*)\|([^|]*)\|\s*$"  # golden, semafor, motiu
)


@dataclass
class FilaBanc:
    num: int
    codigo_bdns: str
    convocant: str
    objecte: str
    capa: str  # "A" | "B"
    golden: str | None
    semafor: str | None
    motiu: str | None
    errors: list[str] = field(default_factory=list)


def parse_full(path: Path | None = None, frontera_ab: int = 27) -> list[FilaBanc]:
    """Parseja TOTES les files de les taules del full. `frontera_ab`: primera fila de la
    capa B (el full v2 numera seguit: 1–26 = A, 27+ = B)."""
    text = (path or FULL_PATH).read_text(encoding="utf-8")
    files: list[FilaBanc] = []
    # Reassemblatge de files partides: alguna cel·la del full té un salt de línia embegut
    # (defecte conegut del generador de #251 a la fila 4). Una línia que comença amb «| N |»
    # obre fila; les línies següents que NO obren fila ni són separador s'hi concatenen fins
    # que la fila té els 10 camps. No es toca el fitxer (Bea hi està etiquetant): tolerància
    # al parser, fidelitat a la dada.
    _OPEN = re.compile(r"^\|\s*\d+\s*\|")
    assembled: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if _OPEN.match(line):
            assembled.append(line)
        elif assembled and not _ROW.match(assembled[-1]) and line and not line.startswith("|"):
            assembled[-1] = assembled[-1] + " " + line
    for line in assembled:
        m = _ROW.match(line)
        if not m:
            continue
        num = int(m.group(1))
        g = m.group(8).strip().lower() or None
        s = m.group(9).strip().lower() or None
        mo = m.group(10).strip() or None
        files.append(
            FilaBanc(
                num=num,
                codigo_bdns=m.group(2),
                convocant=m.group(3).strip(),
                objecte=m.group(4).strip(),
                capa="A" if num < frontera_ab else "B",
                golden=g,
                semafor=s,
                motiu=mo,
            )
        )
    return files


def valida(files: list[FilaBanc]) -> tuple[list[str], list[str]]:
    """(errors_bloquejants, warnings). Buit el primer = es pot congelar."""
    errors: list[str] = []
    warnings: list[str] = []
    if not files:
        return (["cap fila parsejada — el format de la taula ha canviat?"], [])
    vistos: dict[str, int] = {}
    for f in files:
        pre = f"fila {f.num} (BDNS {f.codigo_bdns})"
        if f.golden is None:
            errors.append(f"{pre}: sense etiqueta golden")
            continue
        if f.golden not in GOLDENS:
            errors.append(f"{pre}: golden «{f.golden}» fora del vocabulari {sorted(GOLDENS)}")
        if f.golden == "elegible":
            if f.semafor not in SEMAFORS:
                errors.append(f"{pre}: elegible sense semafor verd|groc (té «{f.semafor}»)")
        elif f.semafor:
            errors.append(f"{pre}: semafor «{f.semafor}» en una no-elegible")
        if f.golden in ("frontera", "fora") and not f.motiu:
            errors.append(f"{pre}: {f.golden} exigeix motiu")
        if f.golden and not f.motiu:
            warnings.append(f"{pre}: sense motiu (recomanat)")
        if f.codigo_bdns in vistos:
            warnings.append(
                f"{pre}: codigoBDNS duplicat amb la fila {vistos[f.codigo_bdns]} — "
                f"solapament A∩B: s'etiqueta UN cop (C4 §2 v2)"
            )
        vistos[f.codigo_bdns] = f.num
    return errors, warnings


def recompte(files: list[FilaBanc]) -> dict:
    """El recompte per capa que es presenta a Bea abans de congelar."""
    out: dict = {}
    for capa in ("A", "B"):
        sel = [f for f in files if f.capa == capa and f.golden]
        out[capa] = {
            "total": len(sel),
            "elegible": sum(1 for f in sel if f.golden == "elegible"),
            "verd": sum(1 for f in sel if f.golden == "elegible" and f.semafor == "verd"),
            "groc": sum(1 for f in sel if f.golden == "elegible" and f.semafor == "groc"),
            "descartable": sum(1 for f in sel if f.golden == "descartable"),
            "frontera": sum(1 for f in sel if f.golden == "frontera"),
            "fora": sum(1 for f in sel if f.golden == "fora"),
        }
    # denominador del recall (C4 §3 v2): elegibles+fronteres-elegibles de B — les etiquetes
    # frontera NO sumen al denominador fins que Bea no les resolgui a elegible/descartable?
    # NO: C4 v2 diu «clares + fronteres que Bea etiqueti elegibles» — la frontera és una
    # etiqueta FINAL aquí (cas dubtós real); el denominador del recall són les elegibles de B,
    # i les fronteres es reporten a part (FN de frontera es tolera a DECEBEDOR).
    out["denominador_recall_B"] = out["B"]["elegible"]
    return out


def to_banc_json(files: list[FilaBanc]) -> list[dict]:
    """El banc congelable (només files etiquetades, sense les «fora»)."""
    return [
        {
            "num": f.num,
            "codigo_bdns": f.codigo_bdns,
            "capa": f.capa,
            "golden": f.golden,
            "semafor": f.semafor,
            "motiu": f.motiu,
        }
        for f in files
        if f.golden and f.golden != "fora"
    ]


# --- Congelació (veritat d'or del radar) --------------------------------------

_NOTA_CONGELACIO = (
    "Banc CONGELAT — veritat d'or del radar de subvencions (C4). Etiquetatge HUMÀ de "
    "Bea (C4 §2 v2: cap agent, cap model posa cap golden); transcripció MECÀNICA per "
    "datapoble_signals.banc_c4. NO editar a mà: regenera amb "
    "`python -m datapoble_signals.banc_c4 --congela`. La guarda de fidelitat "
    "(packages/signals/tests/test_banc_c4.py) cau si aquest JSON deriva del full o si "
    "valida() no torna 0 errors — ni el full ni el JSON es poden editar en silenci."
)


def construeix_banc_congelat(files: list[FilaBanc] | None = None) -> dict:
    """L'estructura congelable: procedència + recompte + el banc (sense «fora»)."""
    files = parse_full() if files is None else files
    return {
        "_meta": {
            "font": "docs/ajuntaments/banc-c4-etiquetatge.md",
            "etiquetat_per": "Bea (direcció humana) — C4 §2 v2: cap agent, cap model",
            "etiquetatge_origen": "commit 78e8d27 · PR #286 · branca c4/etiquetes-bea",
            "transcripcio": "to_banc_json(parse_full()) — mecànica, sense interpretació",
            "recompte": recompte(files),
            "nota": _NOTA_CONGELACIO,
        },
        "banc": to_banc_json(files),
    }


def _serialitza_banc_congelat(files: list[FilaBanc] | None = None) -> str:
    return json.dumps(construeix_banc_congelat(files), ensure_ascii=False, indent=2) + "\n"


def carrega_banc_congelat() -> list[dict]:
    """El banc congelat (veritat d'or): la llista d'etiquetes, sense les «fora»."""
    return json.loads(BANC_CONGELAT_PATH.read_text(encoding="utf-8"))["banc"]


def _main(argv: list[str] | None = None) -> int:
    """`--congela` (re)genera el JSON congelat des del full; `--check` verifica que no ha derivat."""
    import argparse

    parser = argparse.ArgumentParser(prog="datapoble_signals.banc_c4")
    grup = parser.add_mutually_exclusive_group(required=True)
    grup.add_argument("--congela", action="store_true", help="(re)genera el banc congelat des del full")
    grup.add_argument("--check", action="store_true", help="verifica que el banc congelat no ha derivat del full")
    args = parser.parse_args(argv)

    files = parse_full()
    errors, _ = valida(files)
    if errors:
        print("::error:: valida() torna errors — NO es congela:")
        for e in errors:
            print(f"  {e}")
        return 1

    esperat = construeix_banc_congelat(files)
    if args.congela:
        BANC_CONGELAT_PATH.write_text(_serialitza_banc_congelat(files), encoding="utf-8", newline="\n")
        print(f"banc congelat escrit: {BANC_CONGELAT_PATH.name} ({len(esperat['banc'])} files)")
        return 0

    # --check: comparació SEMÀNTICA (immune a finals de línia), no de bytes.
    if not BANC_CONGELAT_PATH.exists():
        print(f"::error:: no existeix {BANC_CONGELAT_PATH.name} — corre --congela")
        return 1
    actual = json.loads(BANC_CONGELAT_PATH.read_text(encoding="utf-8"))
    if actual != esperat:
        print("::error:: el banc congelat ha DERIVAT del full — regenera amb --congela")
        return 1
    print(f"banc congelat al dia ({len(esperat['banc'])} files, 0 errors de validació)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
