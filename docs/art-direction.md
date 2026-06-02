# datapoble · Brief de Dirección de Arte

**Codename propuesto:** **Llegenda** (la leyenda de un mapa: la clave visual que hace legible el territorio — exactamente su función).
**Autora del brief:** Talaia (coordinación) · **Voto narrativo final:** Bea
**Estado:** brief inicial para revisión

---

## 0. Su remit en una frase

Llegenda es dueña de **todo lo que el público ve**: identidad de marca, lenguaje cartográfico, sistema de dataviz, capa editorial, accesibilidad y la coherencia visual entre idiomas. No "pinta al final": define el sistema desde el día 1 y lo entrega como **contratos** (tokens, estilos, componentes) que el frontend (Mirador) consume.

**Cómo trabaja:**
- Contra contratos, no contra código ajeno (jurisdicción del kit): entrega *design tokens* y *estilos*; Mirador los implementa. Si discrepan, se escala a Talaia; lo narrativo, a Bea.
- Empareja con **Mirador** (frontend) y con **Talaia** en la frontera diseño↔dato (paletas, clasificación de mapas).
- Trabaja contra **datos mock** desde F1 (no espera a que el pipeline esté listo).
- Fuente de verdad de diseño: **Figma**. Fuente de verdad de implementación: los **tokens exportados**.

---

## 1. Workstreams y entregables

### A · Identidad de marca
- Nombre público del observatorio (puede diferir de "datapoble", que es el repo), wordmark, favicon, atributos de marca, *moodboard*, tono.
- Registro: serio pero legible por un alcalde **y** por un vecino. Rigor + calidez. Territorio de montaña, no corporativo frío.
- **Entregable:** `design-system/brand/` — **2-3 rutas de identidad** para que Bea elija → identidad elegida, logo en SVG, favicon, guía de marca (1 página). *DoD:* Bea aprueba una ruta.

### B · Design tokens (única fuente de verdad visual)
- Color (incl. paletas de datos), tipografía (sistema con **buenas diacríticas catalanas y cifras tabulares** para dato), espaciado, radios, sombras, breakpoints, movimiento.
- **Entregable:** Figma tokens → `design-system/tokens/` exportados con Style Dictionary (JSON → variables CSS / tema). *Es el contrato que consume Mirador.* *DoD:* tokens compilando a CSS, consumidos por un componente de prueba.

### C · Lenguaje cartográfico  *(el corazón del proyecto)*
- **Basemap MapLibre custom**: apagado/desaturado para que el dato resalte; relieve apropiado de montaña; etiquetas en catalán.
- **Escalas coropléticas**: secuencial de "exposición/presión" **perceptualmente uniforme + segura para daltonismo**; diverging donde aplique; leyendas; método de clasificación (cuantiles vs Jenks) **coordinado con Talaia/dato**.
- Interacción del mapa: hover, selección, tooltip, y el patrón "dos extremos" (Castellar↔Berga resaltados).
- **Entregable:** `design-system/cartography/` — estilo MapLibre (JSON), spec de paletas, componentes de leyenda. *DoD:* el mapa del prototipo re-renderizado con el estilo nuevo.

### D · Sistema de dataviz
- Lenguaje de gráfico consistente sobre **Observable Plot / D3**: ejes, anotación, y los patrones-historia (ranking, scatter de validación, estacionalidad, distribución-con-resalte).
- Formato numérico y de fecha **por locale** (ca/es), unidades.
- **Entregable:** componentes de gráfico en `design-system/` + **Storybook** + guía de dataviz. *DoD:* las 4 visualizaciones del prototipo portadas al sistema.

### E · Capa editorial / scrollytelling
- El aspecto narrativo: cómo se presenta una "historia" (day-tripper, el índice, la irrupción de extrema derecha). Tipografía de lectura larga, pies de figura, y —clave para nuestra trazabilidad— **el tratamiento visual de "esto es dato / esto es inferencia / esto es un resultado negativo"** y de la **cita de fuente** (fuente·fecha·fórmula visibles).
- **Entregable:** plantillas editoriales + **una historia de referencia diseñada** (la del day-tripper) como patrón. *DoD:* la historia de referencia navegable.

### F · Accesibilidad y rendimiento  *(co-propiedad con Mirador)*
- **WCAG AA**: contraste, foco, **tabla-alternativa para cada gráfico** (lectores de pantalla), `prefers-reduced-motion`, patrones ARIA.
- **Presupuesto de rendimiento** acordado con Mirador (lazy-load de mapas, presupuesto de assets).
- **Entregable:** checklist a11y + doc de perf budget + baseline de **regresión visual** (Storybook/Chromatic en CI). *DoD:* checklist verde en la home y una historia.

### G · i18n visual  (ca/es siempre; en/fr ampliable)
- El diseño debe **respirar expansión de texto** (catalán y francés corren más largos que el castellano), un **selector de idioma** limpio, y formatos numéricos/fecha locale-aware.
- **Entregable:** componente selector de idioma + guías de i18n visual (longitudes, line-height, no romper layouts). *DoD:* la home no se rompe al alternar ca↔es.

---

## 2. Fases (se solapan con el resto del equipo)

| Fase | Llegenda entrega | Desbloquea |
|---|---|---|
| **F1** | Identidad (rutas→elegida) + **tokens** | Mirador arranca UI contra mock |
| **F2** | Cartografía custom + sistema dataviz | Mirador implementa mapa y charts reales |
| **F3** | Editorial/scrollytelling + a11y/perf + i18n visual | Lanzamiento público |

---

## 3. Contratos que respeta / produce

- **Produce:** tokens, estilo MapLibre, componentes (Storybook), guías. *Son contrato:* Mirador construye contra ellos.
- **Respeta:** las **etiquetas de las métricas las define el catálogo semántico** (Talaia/IA); Llegenda las **estiliza**, no las inventa. El **presupuesto de perf** y el **estándar a11y AA** son límites duros. La **autoridad narrativa final es de Bea** (marca, copy, qué se publica).
- **No toca:** `ingestion/`, `transform/`, `ai/` (lógica), `semantic/` (definiciones). Si necesita un cambio ahí, lo pide vía issue/handoff a Talaia.

---

## 4. Lo que NO es su trabajo (frontera explícita)
- No define indicadores ni métricas (eso es dato/semántica).
- No decide clasificación estadística de mapas en solitario (la acuerda con Talaia: el color comunica método).
- No implementa el frontend (eso es Mirador); entrega el sistema que Mirador implementa.
- No publica copy/marca sin el visto bueno de Bea.

---

*Primer encargo concreto cuando entre: las **2-3 rutas de identidad** + el set inicial de **tokens de color y tipografía**, contra los datos del prototipo actual. Con eso, Mirador ya puede empezar.*
