# riusdegent — Visión v3 (documento constitucional)

**riusdegent · Dades per entendre com s'habita el territori**

> Persones que arriben, marxen, tornen, pernocten, lloguen, compren, hereten, visiten, treballen, voten, ocupen places, omplen segones residències o desapareixen del padró real de la vida quotidiana.

**Estado:** constitución v3 — **supersede** la spec V0.1 (`docs/00-project-spec.md`, preservada como evidencia histórica, no se borra).
**Autora:** Talaia · **Decide la narrativa:** Bea.

---

## 0. El giro
De *"observatorio de presión turística-residencial"* a **observatorio de cómo se habita el territorio**. No es cosmético: pasa del foco en la *presión* (alarmista, parcial) a la *habitança* (humana, completa — presencia **y** ausencia, flujo **y** stock, los que vienen y los que desaparecen). El nombre lo dice: **rius de gent**, el caudal humano que atraviesa y llena (o vacía) cada municipio. El IETR deja de ser *el punto* para ser *un indicador* dentro de un observatorio más ancho.

## 1. La tesis / el norte
**El gap entre el padrón oficial y la habitança real.** Hacer visible la **población invisible**: los que **no constan pero llenan** el territorio (excursionistas, segunda residencia, estacionales) y los que **constan pero ya no viven** la vida cotidiana (despoblación, padrón fantasma). Ese gap es el relato que nadie más tiene — y ya tenemos los proxies para medirlo.

## 2. Los dos pilares

### Pilar 1 — Capas de habitança (datos estructurados: stock + flujo)
*La forma del río.* Marts reproducibles por municipio: vivienda (vacío/segunda residencia), turismo (flujo reglado y observado), exposición (IETR, validado r=0,87), política (quién vota), edad (quién envejece / quién es joven y se va).
- **Indicador estrella: "población real estimada" vs padrón** (proxies: residuos = fantasmas, IMD, tren, museo). Un número y un mapa propios.
- **"Rius de gent": el pulso estacional** — quién entra y sale de cada municipio a lo largo del año.

### Pilar 2 — El cabal (inteligencia territorial desde los rastros)
*El caudal del río:* la corriente de actividad en tiempo real, medida por los **rastros** que el territorio deja cuando un fenómeno no tiene dataset limpio. *(El principio de los kg de residuos, generalizado: leer el "tubo de escape" administrativo y digital.)*
- **Motor: tabla de eventos + convergencia.** Todo (un pliego, un corte de tráfico, una noticia, un decreto de sequía) → evento *tipado, fechado, geolocalizado* (`ine5`). La inteligencia es la **convergencia**: señales independientes que coinciden en municipio+ventana = confianza (el mismo principio que validó el IETR contra los residuos).
- **Oro: licitaciones y presupuestos como indicador *adelantado*.** Lo que un ayuntamiento contrata revela lo que espera. Semi-estructurado, fechado, geolocalizable.
- **Ciclo de vida del fenómeno:** anticipación (licitaciones) → realización (agendas, cortes, refuerzos) → reacción (ordenanzas, tasas, noticias de quejas).
- **Catálogo de proxies** (recetario: *fenómeno → rastro → fuente → caveat*).
- **Extracción con LLM anclada** (vía OpenRouter): de texto messy a evento tipado, **citando siempre el fragmento fuente**; si no puede, rechaza. **Dato vs inferencia** explícito.
- **Fuentes, por orden de señal/ruido:** contratación pública + BOPB/DOGC (incl. sequía) primero; agendas, webs y noticias después.
- **Right-sizing:** 2-3 fuentes de alta señal sobre los 2 pilotos + comarca; *luego* ensanchar. Legal: boletines y contratación son reutilizables por diseño; webs/noticias → robots/ToS, hecho+enlace (no copia), sin datos personales.

## 3. Principios (reafirmados)
Right-sizing · reproducibilidad · **trazabilidad** (ningún número sin fuente·fecha·fórmula; dato vs inferencia) · diseño como producto · **honestidad incluidos los "no"** · privacidad (lectura ecológica, no individual) · accesibilidad · abierto.

## 4. Qué ya tenemos (balance)
Repo vivo + equipo de 4 agentes. **F0 y F1 integrados** (7 PRs): sistema de diseño, pipeline reproducible con IETR validado + mart electoral, IA texto→SQL trazable, frontend SvelteKit i18n ca/es. Investigación: el auge de la extrema derecha en Catalunya mapeado (951 munis) + **tres "no" honestos** (ni edad municipal, ni inmigración, ni tamaño lo explican → es geográfico, el fenómeno Aliança) + el ángulo del **voto joven** (capa de encuesta, CEO).

## 5. Arquitectura
Los dos pilares sobre el mismo stack.
- **Pilar 1:** connectors → dbt + DuckDB → marts (clave `ine5`).
- **Pilar 2:** harvest → esquema de evento → **extracción LLM (OpenRouter)** → **events table (clave `ine5`)**.
- La events table hace **join** con los marts: el mismo municipio visto como *forma* (stock) y como *cabal* (señales).
- Salidas: artefactos estáticos + API IA. Frontend: SvelteKit + MapLibre, scrollytelling, i18n ca/es (en/fr).

## 6. Equipo
Talaia (coord + investigación) · Sondeig (datos) · **Cabal** *(nueva: señales/rastros)* · Brúixola (IA) · Mirador (frontend) · Llegenda (arte + identidad `riusdegent`). Bea: voto narrativo.

## 7. Roadmap a lanzamiento
- **F2 · Identidad + datos reales:** identidad `riusdegent` (Llegenda) · Mirador con tokens + marts reales · escala Catalunya (Sondeig).
- **F3 · Cabal (pilar 2):** primer experimento (licitaciones como anticipación, 2 pilotos) → events table → convergencia.
- **F4 · Indicador estrella:** "población real vs padrón" + el pulso estacional.
- **F5 · IA en vivo** (OpenRouter) + scrollytelling.
- **F6 · Lanzamiento público** (Cloudflare + dominio `riusdegent.cat`).

## 8. Primeros encargos
1. **Llegenda:** identidad `riusdegent` (logo, favicon, guía) sobre los tokens ya definidos.
2. **Cabal (nueva) / Sondeig:** experimento *"licitaciones como anticipación"* — contratación pública de Castellar/Berga + Berguedà, clasificada por tema (neteja, aigua, aparcament, turisme, residus, seguretat), buscando la *huella de gasto* estacional. El "kg de residuos" del pilar 2.
3. **Talaia:** el indicador *"población real vs padrón"* con los proxies que ya tenemos.

---
*Supersede `docs/00-project-spec.md` (V0.1). Este documento es el contrato del que cuelgan los encargos. Cambios → bitácora + PR.*
