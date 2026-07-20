"""Localized phrase templates for answers and refusals (ca / es).

Kept separate from the router so wording can change without touching logic, and
so adding a locale (en/fr later) is one dict. Number formatting follows the
locale convention used across datapoble: comma as decimal separator, dot as
thousands separator (ca/es).
"""

from __future__ import annotations

from .catalog import DEFAULT_LOCALE

# --- number formatting (ca/es: 1.234,5) ---------------------------------------


def format_number(value, locale: str = DEFAULT_LOCALE) -> str:
    """Format a number in ca/es style (``.`` thousands, ``,`` decimals)."""
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        s = f"{value:,}".replace(",", ".")
        return s
    if isinstance(value, float):
        # Trim to at most 2 decimals, drop trailing zeros, swap separators.
        s = f"{value:,.2f}"
        s = s.replace(",", "§").replace(".", ",").replace("§", ".")
        return s
    return str(value)


# --- phrase templates ----------------------------------------------------------
# Each is a format string; placeholders are filled by the router.

PHRASES: dict[str, dict[str, str]] = {
    "ca": {
        "value_for": "{label} de {municipi}: {value}{unit}.",
        "ranking_top": "El municipi amb {sup} {label} és {municipi} ({value}{unit}).",
        # The doctrine's `empat`: the data shares the top, so we do not name a
        # winner it does not single out.
        "ranking_tie": (
            "No puc dir quin municipi té {sup} {label}: n'hi ha {n} que "
            "comparteixen exactament el mateix valor ({value}{unit}), i les "
            "dades no els distingeixen. Són: {municipis}."
        ),
        "ranking_list_intro": "Rànquing per {label}:",
        "ranking_row": "{rank}. {municipi}: {value}{unit}",
        "correlation": (
            "La correlació (Spearman) entre {label_a} i {label_b} és "
            "{rho} sobre {n} municipis."
        ),
        "superlative_max": "més",
        "superlative_min": "menys",
        "unit_join": " ",
        "refusal_out_of_catalog": (
            "No puc respondre: la pregunta no es correspon amb cap mètrica del "
            "catàleg semàntic. Mètriques disponibles: {metrics}."
        ),
        "refusal_planned": (
            "La mètrica «{label}» està definida al contracte però encara no "
            "està calculada (status: planned), així que encara no la puc "
            "consultar."
        ),
        # Retirada ≠ pendent. Dir «encara no» d'una mètrica deprecada és
        # prometre que tornarà, i la decisió va ser justament que no.
        # (Còpia pendent del vot narratiu de Bea.)
        "refusal_deprecated": (
            "La mètrica «{label}» va estar publicada però s'ha retirat del "
            "catàleg, així que ja no la consulto. No tornarà en aquesta forma."
        ),
        "refusal_unknown_municipality": (
            "No reconec el municipi «{name}» dins l'àmbit de dades "
            "(Berguedà). Comprova el topònim."
        ),
        "refusal_unsupported": (
            "Entenc que preguntes per «{label}», però no sé convertir aquesta "
            "pregunta concreta en una consulta sobre les marts. Prova de "
            "preguntar per un municipi, un rànquing o una relació."
        ),
        "refusal_guardrail": (
            "Petició bloquejada pels guardarraïls: només lectura, només "
            "mètriques del contracte, mai sobre dades crues (raw). Motiu: {why}"
        ),
        "refusal_budget_exceeded": (
            "Avui hem arribat al límit de consultes d'IA. Les consultes "
            "directes sobre el catàleg segueixen funcionant; torna-ho a provar "
            "demà per a les preguntes en llenguatge lliure. Gràcies per la "
            "paciència!"
        ),
        "refusal_rate_limited": (
            "Has fet moltes consultes seguides. Espera uns segons i torna-ho a "
            "provar, si us plau. Gràcies!"
        ),
        # Deliberately neutral and discreet: it must NOT reveal that any unlock
        # word exists. Just a plain statement of policy.
        "refusal_political_gated": (
            "Aquest observatori no respon preguntes sobre orientació de vot."
        ),
        "note_prefix": "Nota: ",
        "provenance_line": (
            "Font: {source} ({date}). Fórmula: {formula}."
        ),
    },
    "es": {
        "value_for": "{label} de {municipi}: {value}{unit}.",
        "ranking_top": "El municipio con {sup} {label} es {municipi} ({value}{unit}).",
        # El `empat` de la doctrina: los datos comparten el máximo, así que no
        # nombramos un ganador que no señalan.
        "ranking_tie": (
            "No puedo decir qué municipio tiene {sup} {label}: hay {n} que "
            "comparten exactamente el mismo valor ({value}{unit}), y los datos "
            "no los distinguen. Son: {municipis}."
        ),
        "ranking_list_intro": "Ranking por {label}:",
        "ranking_row": "{rank}. {municipi}: {value}{unit}",
        "correlation": (
            "La correlación (Spearman) entre {label_a} y {label_b} es "
            "{rho} sobre {n} municipios."
        ),
        "superlative_max": "mayor",
        "superlative_min": "menor",
        "unit_join": " ",
        "refusal_out_of_catalog": (
            "No puedo responder: la pregunta no se corresponde con ninguna "
            "métrica del catálogo semántico. Métricas disponibles: {metrics}."
        ),
        "refusal_planned": (
            "La métrica «{label}» está definida en el contrato pero aún no "
            "está calculada (status: planned), así que todavía no puedo "
            "consultarla."
        ),
        "refusal_deprecated": (
            "La métrica «{label}» estuvo publicada pero se ha retirado del "
            "catálogo, así que ya no la consulto. No volverá en esta forma."
        ),
        "refusal_unknown_municipality": (
            "No reconozco el municipio «{name}» dentro del ámbito de datos "
            "(Berguedà). Comprueba el topónimo."
        ),
        "refusal_unsupported": (
            "Entiendo que preguntas por «{label}», pero no sé convertir esta "
            "pregunta concreta en una consulta sobre las marts. Prueba a "
            "preguntar por un municipio, un ranking o una relación."
        ),
        "refusal_guardrail": (
            "Petición bloqueada por los guardarraíles: solo lectura, solo "
            "métricas del contrato, nunca sobre datos crudos (raw). Motivo: {why}"
        ),
        "refusal_budget_exceeded": (
            "Hoy hemos alcanzado el límite de consultas de IA. Las consultas "
            "directas sobre el catálogo siguen funcionando; vuelve a intentarlo "
            "mañana para las preguntas en lenguaje libre. ¡Gracias por la "
            "paciencia!"
        ),
        "refusal_rate_limited": (
            "Has hecho muchas consultas seguidas. Espera unos segundos y "
            "vuelve a intentarlo, por favor. ¡Gracias!"
        ),
        # Neutral y discreto: NO debe revelar que existe ninguna palabra de
        # desbloqueo. Solo una declaración llana de la política.
        "refusal_political_gated": (
            "Este observatorio no responde preguntas sobre orientación de voto."
        ),
        "note_prefix": "Nota: ",
        "provenance_line": (
            "Fuente: {source} ({date}). Fórmula: {formula}."
        ),
    },
}


def t(locale: str, key: str, **kwargs) -> str:
    """Look up and format a phrase for ``locale`` (falling back to default)."""
    table = PHRASES.get(locale) or PHRASES[DEFAULT_LOCALE]
    template = table.get(key) or PHRASES[DEFAULT_LOCALE].get(key, key)
    return template.format(**kwargs)
