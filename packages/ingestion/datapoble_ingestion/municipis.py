"""Registre de municipis: el Berguedà (pilot, 31) i tot Catalunya (947).

Clau: codi Idescat de 6 dígits (= INE5 + dígit de control), tal com l'usen RTC,
residus i EMEX. ``ine5`` és els 5 primers dígits → clau de join del contracte.

``BERGUEDA`` (hardcoded) és el pilot. ``CATALUNYA`` (carregat del registre
``data/territorial/municipis-catalunya.csv``, generat per
``tools/deriva_municipis_catalunya.py``) són els 947, per a l'extensió a tot el país
(F1 de docs/pla-catalunya-profund.md). Els connectors per-muni (EMEX, demografia/origen)
prenen un d'aquests dos diccionaris ``codi6 -> nom``.

Avís (codi): Gósol és al Berguedà però té prefix de província Lleida (25). El seu
codi Idescat és 251001 → ine5 derivat = 25100. El codi INE canònic de Gósol és
25101; la diferència ve del dígit de control d'Idescat. Per al join INTERN entre
RTC/residus/EMEX és consistent (totes tres fonts usen 251001). Per a l'electoral
(``ntc4-rnwr``, fora d'aquest PR), que usa l'INE canònic, caldrà un crosswalk per
als municipis amb prefix no-08. Documentat per a Talaia.
"""
from __future__ import annotations

# codi6 -> nom oficial (català)
BERGUEDA: dict[str, str] = {
    "080116": "Avià",
    "080168": "Bagà",
    "080229": "Berga",
    "080240": "Borredà",
    "080459": "Capolat",
    "080497": "Casserres",
    "080500": "Castellar del Riu",
    "080522": "Castellar de n'Hug",
    "080575": "Castell de l'Areny",
    "080787": "l'Espunyola",
    "080804": "Fígols",
    "080924": "Gironella",
    "080930": "Gisclareny",
    "080996": "Guardiola de Berguedà",
    "081304": "Montclar",
    "081326": "Montmajor",
    "081424": "la Nou de Berguedà",
    "081445": "Olvan",
    "081666": "la Pobla de Lillet",
    "081751": "Puig-reig",
    "081770": "la Quar",
    "081884": "Sagàs",
    "081901": "Saldes",
    "082166": "Sant Jaume de Frontanyà",
    "082554": "Santa Maria de Merlès",
    "082687": "Cercs",
    "082938": "Vallcebre",
    "082994": "Vilada",
    "083089": "Viver i Serrateix",
    "089030": "Sant Julià de Cerdanyola",
    "251001": "Gósol",
}

assert len(BERGUEDA) == 31, "El Berguedà té 31 municipis"

# ine5 (5 primers dígits del codi Idescat) -> nom. Clau de join del contracte i
# clau ``territori_codi`` de l'electoral (``ntc4-rnwr``).
# Verificat en viu (2026-06-02): ntc4-rnwr usa AQUEST mateix codi (no l'INE
# canònic). Gósol = 25100 al dataset electoral i a mart_municipi (coincideixen);
# l'INE canònic 25101 correspon a "la Granadella" en aquest dataset. Per tant el
# crosswalk Gósol és identitat aquí (vegeu seeds/crosswalk_ine5.csv).
BERGUEDA_INE5: dict[str, str] = {codi6[:5]: nom for codi6, nom in BERGUEDA.items()}

assert len(BERGUEDA_INE5) == 31, "31 ine5 únics"
assert BERGUEDA_INE5.get("25100") == "Gósol"


# --- Tot Catalunya (947) -------------------------------------------------------
# Registre derivat (codi6 ↔ ine5 ↔ nom canònics) de la geometria ICGC + l'ARC.
# Carregat de fitxer perquè és dada (947 files), no codi; es regenera amb
# tools/deriva_municipis_catalunya.py. Càrrega tova: si el fitxer no hi és (clon
# sense generar-lo), CATALUNYA queda buit i els connectors del pilot (default
# BERGUEDA) segueixen funcionant — no trenquem el pilot ni el CI.
def load_catalunya() -> dict[str, str]:
    """``codi6 -> nom`` dels 947 municipis de Catalunya (registre derivat)."""
    import csv

    from .config import REPO_ROOT

    path = REPO_ROOT / "data" / "territorial" / "municipis-catalunya.csv"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            out[row["codi6"]] = row["nom"]
    return out


CATALUNYA: dict[str, str] = load_catalunya()
CATALUNYA_INE5: dict[str, str] = {codi6[:5]: nom for codi6, nom in CATALUNYA.items()}

# El Berguedà ha de ser un subconjunt exacte del registre de tot CAT (si està carregat).
if CATALUNYA:
    assert set(BERGUEDA) <= set(CATALUNYA), "els 31 codi6 del Berguedà han de ser dins del registre CAT"
