# datapoble — Registro de fuentes verificadas (Experimento 0)

**Qué es:** resultado del *Experimento 0* del laboratorio — la verificación, contra fuente primaria y consultando APIs **en vivo**, de qué datos existen de verdad para **Berga** y **Castellar de n'Hug** (Berguedà). Sustituye a las suposiciones de la spec V0.1 por hechos comprobados.
**Fecha de verificación:** 2026-06-01.
**Método:** consulta directa a portales oficiales y endpoints SODA/Socrata (con conteos de filas y filas concretas de ambos municipios donde fue posible). Lo no comprobado en vivo se marca como tal.
**Doble de:** el entregable "Registro de fuentes" + semilla del "Diccionario de datos" de la spec.

---

## 0. Convención de visibilidad (etiquetas de capa)

Cada fuente lleva una etiqueta que se hereda a indicadores, tablas y salidas:

- 🟢 **VISIBLE** — puede entrar en el producto turístico-territorial que se enseña.
- 🔴 **PRIVADA** — capa interna de investigación (ideología/voto). **Nunca se exporta** al producto. Se reporta solo agregada (comarcal o clústeres), nunca nominando municipios diminutos, nunca cruzada con datos personales/parcela.

Regla de diseño: toda tabla del modelo lleva columna `visibilidad`; cualquier *join* entre 🔴 y 🟢 produce un resultado 🔴.

---

## 1. Trampas operativas críticas (leer antes de tocar nada)

1. **Trampa de códigos.** Castellar de n'Hug = **08052** en INE/Idescat pero **08051** en Catastro/DGC. Berga = **08022** en ambos. Usa el correcto según la fuente o el *join* falla en silencio.
2. **La referencia catastral es la espina dorsal.** El RTC (turismo) **no trae coordenadas**; ICAEN sí. Ambos traen `referencia_cadastral` → es la clave para unir alojamiento ↔ edificio físico (Catastro INSPIRE) ↔ eficiencia energética (ICAEN) en el mismo punto.
3. **Castellar = una sola sección censal = nivel municipal.** No existe granularidad sub-municipal administrativa (166 hab. = 1 sección = 1 mesa electoral). Berga sí baja a sección (4 distritos, 14 secciones, 23 mesas).
4. **Secreto estadístico (Censo INE).** Para Castellar, cualquier cruce multivariable se **bloquea** por umbral de precisión y los valores llegan **redondeados a múltiplos de 3**. Excepción: las **tablas predefinidas** dan valores exactos (úsalas para el split principal/secundaria/vacía).
5. **SoQL (Socrata):** la columna sección se llama `secci_` (no `seccio`); `id_eleccio` = letra(tipo)+año (`A20241` = Parlament 2024; sufijo `1/2` para repeticiones).
6. **La escala correcta es comarcal (≈31 municipios del Berguedà).** Los ratios sobre denominadores diminutos (Castellar) son inestables; el índice solo tiene sentido normalizado contra la distribución comarcal. Casi todas las fuentes clave son comarcales y consultables sin autenticación, así que esto es viable.

---

## 2. Capa FÍSICA / territorio 🟢

| Fuente | Viab. | Granularidad | Acceso | Gotcha |
|---|---|---|---|---|
| **Catastro INSPIRE** (BU/CP/AD) | ✅ | Edificio / parcela / dirección | ATOM ZIP por municipio, GML, sin login. `…/INSPIRE/Buildings/08/08022-BERGA/A.ES.SDGC.BU.08022.zip` (Castellar usa **08051**) | `currentUse` solo 6 categorías; nº plantas solo en `BuildingPart`, no en `Building` |
| **Catastro CAT** (alfanumérico masivo) | ⚠️ | Inmueble | Sede Electrónica, requiere **certificado/Cl@ve**; texto ancho fijo | Uso/tipología/calidad/antigüedad mucho más detallados que INSPIRE. Sin titular ni valor (protegidos) |
| **ICGC — MUC** (urbanismo) | ✅ | Municipal/parcela | territori.gencat.cat → MUC (SHP/GML/WMS) | Lo hace Territori, no ICGC; **posible cláusula no-comercial — verificar** |
| **ICGC — MDT/pendientes** | ✅ | Ráster 2/5/15 m | visors.icgc.cat/appdownloads (GeoTIFF, WCS/WMS) | CC BY 4.0 |
| **ICGC — Cobertes del sòl** (usos) | ✅ | Ráster 1 m, 41 clases | MCSC2024 (GeoTIFF/GPKG) | No confundir con MCSC del CREAF ni con usos DARP |
| **ICGC — Ortofoto / límites** | ✅ | Ráster / vector | appdownloads + WMS | CC BY 4.0 |

**Campos clave Catastro INSPIRE (edificio):** `dateOfConstruction` (año), `currentUse`, `officialArea` (m² construidos), `numberOfDwellings`, `numberOfBuildingUnits`, `conditionOfConstruction`, `footprint`. Atributo de unión: referencia catastral (`nationalCadastralReference`).

---

## 3. Capa SOCIODEMOGRÁFICA / vivienda 🟢

| Fuente | Viab. | Granularidad | Acceso | Gotcha |
|---|---|---|---|---|
| **Idescat EMEX + API** | ✅ | Municipio (+comarca/Cat) | `api.idescat.cat/emex/v1/dades.json?id=080522` (Castellar) / `?id=080229` (Berga). Sin clave | Da principal/**no** principal, no el split de 3 tipos |
| **Padró continu** | ✅ | Municipio y sección | Idescat `pub/?id=pmh`; serie anual desde 1998 | — |
| **INE Censo 2021** | ⚠️ | Municipio (Castellar) / sección (Berga) | SDC-2021 `ine.es/censos2021/`; Idescat `pub/?id=censph` | Split principal/secundaria/vacía: usar **tablas predefinidas** (exactas). Cruces finos bloqueados en Castellar |

**Códigos API Idescat (6 díg.):** Berga `080229`, Castellar `080522`.

---

## 4. Capa TURISMO — oferta / stock 🟢

| Fuente | Viab. | Qué da | Acceso | Gotcha |
|---|---|---|---|---|
| **RTC — `t2h3-cgys`** | ✅ | Alojamiento reglado (HUT/hotel/rural/càmping) por municipio | `analisi.transparenciacatalunya.cat/resource/t2h3-cgys.json`, mensual | **Sin coordenadas** → geocodificar o unir por `referencia_cadastral`. Trae datos personales del titular (RGPD) |
| **eOMET** (oferta municipal) | ✅ | Plazas/establecimientos por municipio | Dept. Empresa | Es capacidad, no flujo |
| **POIs — DIBA patrimoni** | ✅ | Patrimonio con lat/lon | `dadesobertes.diba.cat` (API REST, `comarques=6`), semanal | Cobertura municipal desigual (depende del Mapa de Patrimoni) |
| **POIs — OSM** | ✅ | Atracciones, equipamientos | Overpass API (`tourism=*`, `historic=*`) | Respaldo; cubre Fonts del Llobregat, Museu del Ciment, Jardins Artigas |

**Inside Airbnb / listings scrapeados:** ❌ **no cubre el Berguedà** (solo Barcelona y Girona ciudad). El lado "observado" se inventaría a mano (universos de decenas).

---

## 5. Capa TURISMO — FLUJO 🟢 (el núcleo del producto visible)

Tres tipos: **D** = excursionista/día · **P** = pernoctación · **I** = demanda/interés.

| Fuente | Tipo | Viab. | Granularidad útil | Acceso / dato verificado |
|---|---|---|---|---|
| **IMD carreteres — `xsvx-ym46`** | D | ✅ | Estación de aforo | C-16 Berga PK96.1 (**permanent**, IMD 8.872→17.812); B-402 PK2 = corredor a Castellar (IMD 1.527→2.029); BV-4031 (399→615). Serie abierta **2017-2022** |
| **Tren del Ciment** (FGC/Turistren) | D | ✅ | ≈ Castellar | Viajeros/temporada: **2023: 19.427 · 2024: 29.019 (+49%)**. Notes de premsa |
| **Museu del Ciment** (mNACTEC) | D | ✅ | Municipal de facto | Visitantes/año: 2021: 11.164 · 2023: 15.165 · **2024: 20.846** · 2025: >25.000 (prelim) |
| **Residus municipals — `69zu-w48s`** | D | ✅ | Municipio × año | kg/hab/any hasta 2024. Proxy de "población fantasma" (carga real vs empadronados) |
| **IEET / taxa turística** | P | ⚠️ | **Solo comarca** | `q4sr-68c3` (municipal) **excluye Berga y Castellar** (caen en "Resta"). Usar `2nmt-74sj` (comarca, semestral) |
| **INE movilidad** (móvil agregado) | D/P | ⚠️ | Celdas ≥5.000 hab | Castellar **no aislable** (diluido). Berga quizá celda propia. Gratuito |
| **EOH / ACT / LABturisme** | P | ⚠️ | Marca "Pirineus" / comarca | Sin dato municipal para ninguno de los dos |
| **Gasto tarjeta** (CaixaBank) | I | ❌ | Solo >35.000 hab | Ambos excluidos |
| **La Patum** (Berga, UNESCO) | D | ⚠️ | Evento | Pico ~6.000; Ajuntament instaló **comptadors de persones (2026)** — institucional, no open data |
| **Google Trends** | I | ✅ | Término de búsqueda | Gratis/legal (manual). **Mejor proxy de estacionalidad** (forma de curva). Relativo, no absoluto. pytrends archivado 2025 |
| **Wikipedia pageviews** | I | ✅ | Artículo | API oficial, **conteo absoluto**, gratis, legal. *Infravalorado — usar* |
| **Review velocity** (Google/TripAdvisor) | D | ⚠️ | POI | Débil a esta escala (~49 reseñas Museu). Solo tendencia interanual/ranking. Anonimizar (RGPD) |
| **Google Popular Times** | D | ⚠️ | POI, intradía | De pago (SerpApi/Outscraper) o libs muertas. Verificar que el Museu tenga datos antes de invertir. Fonts: casi seguro sin dato |
| **Instagram / Wikiloc / AllTrails** | D | ❌ | — | APIs cerradas/hostiles + ToS. Descartar como pipeline; solo conteo manual estático puntual |

**Honestidad de flujo:** ningún proxy da excursionistas/día absolutos. Anclar las curvas de Trends/Wikipedia contra un dato duro (Tren del Ciment, Museu) para fijar escala.

---

## 6. Capa ENERGÍA / rehabilitación 🟢

| Fuente | Viab. | Granularidad | Acceso | Dato verificado |
|---|---|---|---|---|
| **ICAEN certificados — `j6ii-t3w2`** | ✅ | Inmueble (con coords + ref. catastral) | `analisi.transparenciacatalunya.cat/resource/j6ii-t3w2.json` | **Berga 2.550 / Castellar 58** certificados. Calificación A–G, superficie, uso, normativa |
| **Idescat habitatges/edificis + Censo** | ✅ | Municipio | `idescat.cat/tema/habit` | Antigüedad del parque (lo que ICAEN no da) |
| **Ayudas rehabilitación (AHC)** | ⚠️ | Municipio (en visor) | habitatge.gencat.cat/visor | Sin CSV/API confirmado; extracción manual |

**Gotcha ICAEN:** no da año exacto (solo normativa de referencia); cubre solo el parque *certificado* (sesgo: certifica quien vende/alquila/pide ayuda).

---

## 7. Capa POLÍTICA / ideología 🔴 PRIVADA — nunca se exporta

| Fuente | Viab. | Granularidad | Acceso |
|---|---|---|---|
| **Eleccions — `ntc4-rnwr`** ("Processos electorals - Vots") | ✅ | **Hasta mesa** | `analisi.transparenciacatalunya.cat/resource/ntc4-rnwr.json`. 21,4M filas. Todas las convocatorias (Parlament 1980→, Congrés/Senat 1977→, Europees 1987→, Municipals 1979→) hasta **2024**. `TERRITORI_CODI` = INE 5 díg. |
| **Candidatos — `xnfg-weec`** | ✅ | Territorio | Mismo portal (sexo, electe/no) |
| **Idescat eleccions** | ✅ | Municipio | `pub/?id=elepc` (Parlament), `?id=elem` (municipals) — validación de agregados |
| **CEO Baròmetre — `gp4k-sxxn`** | ⚠️ | **Provincia** (no municipio) | Microdatos .sav/.csv, 2005-2025. Solo calibración provincial; NO imputar a municipio |

**Sin supresión:** los datos electorales son públicos por mesa (verificado: Castellar publica su mesa única con el voto de cada partido).

**Método (dos ejes, ambos calculables desde `VOTS`):**
- Eje **independentista–constitucionalista** y eje **izquierda–derecha** (clasificar candidaturas por `CANDIDATURA_SIGLES`; documentar el tratamiento de híbridos: CiU pre-2015, Comuns "ni-ni").
- Métricas: % bloque indep., % izquierda, participación/abstención, fragmentación (nº efectivo de partidos, Laakso-Taagepera), volatilidad (Pedersen, con tabla de equivalencias de siglas en el tiempo).
- No existe índice municipal académico reutilizable → **replicarlo** (anclar posiciones con CEO o Chapel Hill Expert Survey).

**Guardarraíles éticos (uso interno):**
- Falacia ecológica explícita (no atribuir el voto de la mesa a individuos).
- k-anonimato práctico: no difundir cruces para municipios < ~100–250 votantes; agregar los diminutos en clústeres, no nominarlos.
- No cruzar voto con datos personales/nominales ni a nivel parcela.

---

## 8. Hechos verificados clave (en vivo)

**Castellar de n'Hug (08052 / Catastro 08051) — perfil:**
- Población 2025: **166**. Hogares 2021: 72.
- Viviendas 2021: total **276** · principales **71 (25,7%)** · no principales **205 (74,3%)**. → **1,66 viviendas/habitante**.
- Alojamiento reglado (RTC): **30** (mayoría HUT) → ≈181/1.000 hab.
- Solo ~30 de las 205 no principales están regladas como turísticas → el grueso son **segundas residencias**, no negocio turístico.
- Flujo contado 2024: **29.019 (Tren del Ciment) + 20.846 (Museu)** ≈ **50.000 visitas/año** a un pueblo de 166 → la presión real es **excursionista de día**, invisible para el RTC.
- Certificados energéticos: 58.

**Berga (08022) — perfil:**
- Población ~17.160.
- Alojamiento reglado (RTC): **45** (36 HUT, 4 hotels, 4 turisme rural, 1 càmping) → ≈2,6/1.000 hab (**~69× menos intensidad que Castellar**).
- IMD acceso C-16: estación permanente, 8.872→17.812 veh/día.
- Pico anual: **La Patum** (UNESCO, Corpus).
- Certificados energéticos: 2.550. Estructura electoral: 4 distritos / 14 secciones / 23 mesas.

---

## 9. Pendiente / no verificado al 100%

- Fecha exacta del último corte INSPIRE y del último vuelo ortofoto/LiDAR para estos municipios.
- Literal de la licencia del MUC (¿no-comercial?).
- IMD Generalitat **posterior a 2022** en open data (existe en visor, no confirmada la descarga).
- Asignación exacta de la celda INE-movilidad que contiene a Berga.
- Dataset consolidado de **participació/cens a nivel mesa** (existen tablas legacy por convocatoria).
- Split del parque de Berga (1 llamada Idescat pendiente).
- Volcado fila-a-fila del bloc "Eleccions" del EMEX de Castellar (existencia confirmada).

---

## 10. Dataset IDs de referencia rápida

| ID Socrata | Contenido | Capa |
|---|---|---|
| `t2h3-cgys` | Alojamiento turístico RTC | 🟢 |
| `j6ii-t3w2` | Certificados energéticos ICAEN | 🟢 |
| `69zu-w48s` | Residus municipals | 🟢 |
| `xsvx-ym46` | IMD carreteres (Generalitat) | 🟢 |
| `q4sr-68c3` / `2nmt-74sj` / `rn32-up9n` | IEET (municipi / comarca / marca) | 🟢 |
| `ntc4-rnwr` / `xnfg-weec` | Resultados electorales / candidatos | 🔴 |
| `gp4k-sxxn` | CEO microdatos | 🔴 |

API Idescat EMEX: `api.idescat.cat/emex/v1/dades.json?id={080229|080522}`.
