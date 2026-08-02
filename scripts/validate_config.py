#!/usr/bin/env python3
"""Comprueba que .relay.yml declara reglas de verdad, no que la plantilla siga entera.

Un verde aqui significa: este proyecto ha dicho que material tiene, donde puede
estar y que se puede hacer con el. Nada mas, y sobre todo nada menos. La version
anterior daba verde con el fichero de fabrica sin tocar, porque comprobaba que
existieran las claves del vocabulario que la propia plantilla trae: validaba el
andamiaje, no el contenido. Un equipo podia instalarlo, ver el verde y dejar
entrar a una agente cloud sin haber declarado una sola regla.

Uso: python scripts/validate_config.py [ruta]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CLASES = {"repository", "cloud-ok", "local-only", "synthetic-only"}
DERECHOS = {"libre", "solo-agregado", "no-reproducir", "no-publicar", "no-sale"}


def main() -> int:
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else ".relay.yml")
    if not ruta.exists():
        print(f"Falta {ruta}")
        return 1

    try:
        import yaml
    except ImportError:
        # No poder verificar no es lo mismo que estar bien: se dice y se falla.
        print("No puedo verificar: falta PyYAML (pip install pyyaml). Un 'no se' no es un verde.")
        return 1

    try:
        cfg = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        print(f"{ruta} no es YAML valido: {e}")
        return 1

    fallos: list[str] = []
    avisos: list[str] = []

    for clave in ("version", "project", "ownership", "checks", "data_classes", "data_rights"):
        if clave not in cfg:
            fallos.append(f"falta el bloque '{clave}'")
    if fallos:
        print("Configuracion incompleta:\n  - " + "\n  - ".join(fallos))
        return 1

    # La version se ha quedado atras tres veces seguidas al preparar releases:
    # deja de ser mala suerte y pasa a ser comprobacion.
    #
    # Pero SOLO contra el CHANGELOG de Relay. Sin este filtro, la guarda comparaba la
    # version de Relay con la del PROYECTO ANFITRION en cualquier repositorio con su
    # propio CHANGELOG.md en la raiz -- que son casi todos-- y daba rojo por algo que
    # no es un fallo. Un check que salta donde no debe se acaba ignorando donde si
    # debe. (Encontrado al escribir las instrucciones de migracion a 0.6 para otro
    # equipo, 2026-08-02: la guarda era nuestra y el rojo iba a ser suyo.)
    cambios = ruta.parent / "CHANGELOG.md"
    if cambios.exists():
        texto = cambios.read_text(encoding="utf-8")
        titulo = re.search(r"^#\s+(.+)$", texto, re.M)
        es_de_relay = titulo is not None and "relay" in titulo.group(1).lower()
        cabecera = re.search(r"^##\s+([0-9]+\.[0-9.]*[0-9])", texto, re.M)
        if es_de_relay and cabecera and str(cfg.get("version")) != cabecera.group(1):
            fallos.append(
                f"version del fichero ({cfg.get('version')}) distinta de la ultima del CHANGELOG "
                f"({cabecera.group(1)}): una de las dos miente")

    if not cfg.get("project", {}).get("tracker"):
        fallos.append("project.tracker sin declarar: no se sabe donde viven las tareas")

    # El corazon: el mapa de materiales. Vacio = nadie ha declarado nada.
    mapa = cfg.get("data_map") or {}
    if not mapa:
        fallos.append(
            "data_map vacio: este proyecto no ha declarado ningun material.\n"
            "    Mientras siga asi, nadie puede saber que puede ver una agente cloud y\n"
            "    Relay no esta protegiendo nada. Declara al menos el material sensible; si\n"
            "    de verdad no hay ninguno, declara un item unico (clase repository, derechos\n"
            "    libre) para que conste que se ha pensado."
        )
    else:
        raiz = ruta.parent
        for nombre, item in mapa.items():
            if not isinstance(item, dict):
                fallos.append(f"data_map.{nombre}: debe declarar clase, derechos y rutas")
                continue
            clase, derechos, rutas = item.get("clase"), item.get("derechos"), item.get("rutas")
            if clase not in CLASES:
                fallos.append(
                    f"data_map.{nombre}.clase='{clase}': desconocida. Validas: {', '.join(sorted(CLASES))}")
            if derechos not in DERECHOS:
                fallos.append(
                    f"data_map.{nombre}.derechos='{derechos}': desconocido. Validos: {', '.join(sorted(DERECHOS))}")
            if not rutas:
                fallos.append(
                    f"data_map.{nombre}: sin rutas. Una etiqueta sin ficheros no le dice a nadie "
                    "a que material te refieres")
            else:
                for r in rutas:
                    if not list(raiz.glob(r)) and not (raiz / r).exists():
                        avisos.append(f"data_map.{nombre}: '{r}' no existe hoy en el repositorio")

    for a in avisos:
        print(f"aviso: {a}")
    if fallos:
        print("\nConfiguracion Relay NO valida:\n  - " + "\n  - ".join(fallos))
        return 1

    n = len(mapa)
    print(f"Configuracion Relay valida: {n} material{'es' if n != 1 else ''} declarado{'s' if n != 1 else ''}"
          + (f", {len(avisos)} aviso(s)" if avisos else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
