"""Perfils municipals del radar de subvencions — load + validació (C3 §3/§4/§6bis).

Els perfils viuen a ``config/municipis/<ine5>-<slug>.yaml`` (E5: primera
convenció declarativa del repo). Aquest mòdul els carrega amb validació
**fail-fast** (C3 §3): un perfil mal format NO entra al pipeline amb un default
silenciós — peta al load amb un missatge llegible.

Regles vinculants:
  - C3 §3 · esquema TANCAT: camp desconegut → error; ``actiu`` absent → error
    (cap default implícit); ``pes`` fora de [0,1] → error.
  - C3 §6bis · seguretat de la sortida: ``destinataris`` són CLAUS SIMBÒLIQUES
    (p. ex. ``[BEA]``); una ``@`` → error. El mapa clau→adreça viu NOMÉS als
    secrets del workflow (mai al repo públic).
  - C3 §4 · coherència: l'``<ine5>`` del nom de fitxer ha d'existir a
    ``BERGUEDA_INE5`` (la llista dels 31 segueix sent l'única font del filtre
    territorial dels connectors; el perfil només decideix match i sortida).
  - C3 §3 · ``_default`` és plantilla COPIABLE: cap herència ni merge de
    perfils en v1. El loader de conjunt salta els fitxers que comencen per «_»
    (les plantilles es validen als tests, no es serveixen com a perfils).

Semàntica d'``actiu`` (C3 §3): la ingesta i el filtre corren per a TOTS els
perfils; les SORTIDES (correu R4, publicacions) només per als ``actiu: true``.
Aquest mòdul no genera cap sortida: només carrega i valida.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .config import REPO_ROOT
from .municipis import VALID_INE5

# Directori canònic dels perfils (E5). Injectable als tests.
CONFIG_MUNICIPIS_DIR = REPO_ROOT / "config" / "municipis"

# Esquema TANCAT del perfil (C3 §3) — camp desconegut → error.
CAMPS_PERFIL: frozenset[str] = frozenset(
    {
        "tipus_beneficiari",
        "poblacio",
        "poblacio_any",
        "territori",
        "materies",
        "projectes_en_cartera",
        "cofinancament_max",
        "destinataris",
        "actiu",
    }
)

# v1: l'únic tipus de beneficiari suportat (C3 §3). Fail-fast si apareix res més.
TIPUS_BENEFICIARI_V1 = "ajuntament"

_PATRO_NOM_FITXER = re.compile(r"^(\d{5})-[a-z0-9-]+\.yaml$")


class PerfilError(ValueError):
    """Perfil invàlid — el load falla amb un missatge llegible (C3 §3)."""


def _err(origen: str, missatge: str) -> PerfilError:
    return PerfilError(f"perfil invàlid ({origen}): {missatge}")


def valida_perfil(perfil: dict[str, Any], *, origen: str = "<dict>") -> dict[str, Any]:
    """Valida un perfil contra C3 §3 + §6bis. Retorna el perfil si és vàlid.

    Fail-fast i EXHAUSTIU en l'ordre del contracte: primer l'esquema (camps),
    després cada camp. Mai retorna un perfil «arreglat»: o passa tal qual, o peta.
    """
    if not isinstance(perfil, dict):
        raise _err(origen, f"s'esperava un mapa YAML, no {type(perfil).__name__}")

    desconeguts = sorted(set(perfil) - CAMPS_PERFIL)
    if desconeguts:
        raise _err(origen, f"camps desconeguts: {desconeguts} (esquema tancat, C3 §3)")
    absents = sorted(CAMPS_PERFIL - set(perfil))
    if absents:
        # `actiu` absent és l'error canònic del contracte; la resta d'absències
        # són el mateix pecat (cap default implícit).
        raise _err(origen, f"camps obligatoris absents: {absents} (cap default implícit)")

    if perfil["tipus_beneficiari"] != TIPUS_BENEFICIARI_V1:
        raise _err(
            origen,
            f"tipus_beneficiari={perfil['tipus_beneficiari']!r} — v1 només suporta "
            f"{TIPUS_BENEFICIARI_V1!r} (C3 §3)",
        )

    if not isinstance(perfil["poblacio"], int) or isinstance(perfil["poblacio"], bool) \
            or perfil["poblacio"] <= 0:
        raise _err(origen, f"poblacio={perfil['poblacio']!r} ha de ser un enter > 0 (padró citat)")
    if not isinstance(perfil["poblacio_any"], int) or isinstance(perfil["poblacio_any"], bool):
        raise _err(origen, f"poblacio_any={perfil['poblacio_any']!r} ha de ser un any (int)")

    territori = perfil["territori"]
    if not isinstance(territori, list) or not territori \
            or not all(isinstance(t, str) and t.strip() for t in territori):
        raise _err(origen, "territori ha de ser una llista no buida d'etiquetes (str)")

    materies = perfil["materies"]
    if not isinstance(materies, list) or not materies:
        raise _err(origen, "materies ha de ser una llista no buida de {nom, pes}")
    for i, m in enumerate(materies):
        if not isinstance(m, dict) or set(m) != {"nom", "pes"}:
            raise _err(origen, f"materies[{i}] ha de ser exactament {{nom, pes}} — hi ha {m!r}")
        if not isinstance(m["nom"], str) or not m["nom"].strip():
            raise _err(origen, f"materies[{i}].nom buit o no-text")
        pes = m["pes"]
        if isinstance(pes, bool) or not isinstance(pes, (int, float)) or not 0.0 <= float(pes) <= 1.0:
            raise _err(origen, f"materies[{i}] («{m['nom']}»): pes={pes!r} fora de [0,1] (C3 §3)")

    projectes = perfil["projectes_en_cartera"]
    if not isinstance(projectes, list) or not all(isinstance(p, str) and p.strip() for p in projectes):
        raise _err(origen, "projectes_en_cartera ha de ser una llista de textos (pot ser buida)")

    cofi = perfil["cofinancament_max"]
    if isinstance(cofi, bool) or not isinstance(cofi, (int, float)) or float(cofi) < 0:
        raise _err(origen, f"cofinancament_max={cofi!r} ha de ser un número ≥ 0")

    destinataris = perfil["destinataris"]
    if not isinstance(destinataris, list) or not destinataris \
            or not all(isinstance(d, str) and d.strip() for d in destinataris):
        raise _err(origen, "destinataris ha de ser una llista no buida de claus simbòliques")
    per_arrova = [d for d in destinataris if "@" in d]
    if per_arrova:
        # §6bis: MAI un correu en clar al repo públic. La clau simbòlica es resol
        # al workflow (secret RADAR_DEST_<CLAU>), no aquí.
        raise _err(
            origen,
            f"destinataris amb «@» ({per_arrova}): han de ser claus simbòliques "
            "(p. ex. [BEA]), mai correus (C3 §6bis)",
        )

    if not isinstance(perfil["actiu"], bool):
        raise _err(origen, f"actiu={perfil['actiu']!r} ha de ser un booleà explícit (C3 §3)")

    return perfil


def carrega_perfil(path: Path | str) -> dict[str, Any]:
    """Carrega i valida UN perfil des del seu YAML.

    Per als fitxers que NO comencen per «_», el nom ha de seguir el patró
    ``<ine5>-<slug>.yaml`` amb l'INE5 present a ``BERGUEDA_INE5`` (C3 §4) —
    inclou la trampa de codis: Castellar de n'Hug és 08052 (mai 08051 del
    Cadastre) i la Pobla de Lillet 08166 (mai el 081666 de 6 dígits d'Idescat).
    """
    p = Path(path)
    if not p.exists():
        raise _err(str(p), "el fitxer no existeix")

    if not p.name.startswith("_"):
        m = _PATRO_NOM_FITXER.match(p.name)
        if not m:
            raise _err(p.name, "el nom ha de ser <ine5>-<slug>.yaml (C3 §3)")
        ine5 = m.group(1)
        if ine5 not in VALID_INE5:
            raise _err(
                p.name,
                f"INE5 {ine5} fora de BERGUEDA_INE5 (C3 §4: la llista dels 31 mana)",
            )

    dades = yaml.safe_load(p.read_text(encoding="utf-8"))
    perfil = valida_perfil(dades, origen=p.name)
    if not p.name.startswith("_"):
        perfil = {**perfil, "ine5": p.name[:5]}
    return perfil


def carrega_perfil_per_ine5(
    ine5: str, *, config_dir: Path | str = CONFIG_MUNICIPIS_DIR
) -> dict[str, Any]:
    """Troba i carrega el perfil d'un municipi pel seu INE5."""
    d = Path(config_dir)
    candidats = sorted(d.glob(f"{ine5}-*.yaml"))
    if not candidats:
        raise _err(f"{ine5} @ {d.as_posix()}", "cap perfil <ine5>-<slug>.yaml per a aquest municipi")
    if len(candidats) > 1:
        raise _err(f"{ine5} @ {d.as_posix()}", f"més d'un perfil per al mateix INE5: {[c.name for c in candidats]}")
    return carrega_perfil(candidats[0])


def carrega_perfils(*, config_dir: Path | str = CONFIG_MUNICIPIS_DIR) -> list[dict[str, Any]]:
    """Carrega TOTS els perfils del directori (saltant les plantilles «_*»).

    El filtre (R2) corre per a tots, actius o no (C3 §3); qui decideix sortides
    és R4 mirant ``actiu``.
    """
    d = Path(config_dir)
    return [
        carrega_perfil(p)
        for p in sorted(d.glob("*.yaml"))
        if not p.name.startswith("_")
    ]
