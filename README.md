<!-- Document bilingüe · Documento bilingüe — CA primer, ES després -->

# datapoble

**Observatori de vivenda, turisme i pressió territorial.** Dades obertes verificades, reproductibles i traçables, amb una cara pública dissenyada. Pilot al Berguedà (31 municipis), escalable a Catalunya.

**Observatorio de vivienda, turismo y presión territorial.** Datos abiertos verificados, reproducibles y trazables, con una cara pública diseñada. Piloto en el Berguedà (31 municipios), escalable a Cataluña.

---

## CA · Què és

datapoble integra dades públiques (cadastre, Idescat, Registre de Turisme, residus, energia, eleccions, mobilitat) en una base analítica reproduïble, hi calcula indicadors propis —com l'**Índex d'Exposició Turística-Residencial (IETR)**— i ho explica amb mapes, visualitzacions i una capa d'IA que **sempre cita la font, la data i la fórmula**. Publica fins i tot els resultats negatius.

**Principis:** right-sizing (dada petita, gens de sobre-enginyeria), reproductibilitat, traçabilitat, disseny com a producte, honestedat (inclosos els resultats negatius), privacitat i accessibilitat per disseny.

## ES · Qué es

datapoble integra datos públicos (catastro, Idescat, Registro de Turismo, residuos, energía, elecciones, movilidad) en una base analítica reproducible, calcula indicadores propios —como el **Índice de Exposición Turística-Residencial (IETR)**— y lo explica con mapas, visualizaciones y una capa de IA que **siempre cita la fuente, la fecha y la fórmula**. Publica incluso los resultados negativos.

---

## Estat / Estado

**F0 — naixement del repo.** Migrant el prototip (validat) a una arquitectura de producció. Veure `docs/architecture.md`.

## Estructura (monorepo)

```
packages/
  ingestion/      connectors a fonts obertes (Sondeig)
  transform/      dbt + DuckDB: raw → staging → marts (Sondeig)
  ai/             text→SQL traçable via OpenRouter (Brúixola)
  web/            SvelteKit + MapLibre, i18n ca/es (Mirador)
  design-system/  marca · tokens · cartografia (Llegenda)
semantic/         metrics.yml — contracte únic multilingüe
docs/             arquitectura, mètode, brief d'art, fonts
bitacora/         memòria del projecte (decisions datades)
data/             artefactes versionats (parquet/geo)
```

## Equip / Equipo

| Rol | Agent | Frente |
|---|---|---|
| Coordinació + investigació | **Talaia** | arquitectura, contractes, anàlisi, review |
| Dades / pipeline | **Sondeig** | `ingestion/` · `transform/` |
| IA / semàntica | **Brúixola** | `ai/` · `semantic/` |
| Frontend | **Mirador** | `web/` |
| Direcció d'art | **Llegenda** | `design-system/` |
| Direcció humana | **Bea** | producte, veto narratiu |

## Idiomes / Idiomas

Interfície: **ca + es** sempre (per defecte `ca`), **en + fr** ampliables. Documentació interna lliure ca/es; README i CONTRIBUTING bilingües.

## Llicència / Licencia

Codi: **MIT** (`LICENSE`). Contingut propi i indicadors: **CC BY 4.0**. Les dades derivades conserven la llicència de cada font (Catastro, ICGC, Idescat, Dades Obertes de Catalunya…), citada al catàleg.
