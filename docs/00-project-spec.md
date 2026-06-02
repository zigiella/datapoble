# Spec de proyecto

## Nombre provisional

**Observatorio de vivienda, turismo y presión territorial en Berga y Castellar de n’Hug**

## Versión

**V0.1**

## Propósito del proyecto

Diseñar y construir un sistema de inteligencia territorial que permita analizar, visualizar y explicar la relación entre vivienda, turismo, estructura urbana, patrimonio, actividad económica y presión sobre el territorio en dos municipios del Berguedà: Berga y Castellar de n’Hug.

El proyecto nace como piloto replicable. Berga y Castellar de n’Hug funcionan como dos casos complementarios:

**Berga** representa un municipio cabecera, con tejido urbano, centralidad comarcal, patrimonio cultural, servicios, comercio y dinámicas residenciales más complejas.

**Castellar de n’Hug** representa un municipio pequeño de montaña, con fuerte atractivo turístico, alta sensibilidad territorial, presión estacional y una escala urbana mucho más vulnerable.

La ambición no es crear únicamente un dashboard, sino una herramienta para detectar patrones, formular hipótesis y apoyar decisiones municipales o estratégicas.

## Tesis de trabajo

Los municipios pequeños y medianos están tomando decisiones sobre vivienda, turismo y territorio con datos fragmentados, desactualizados o poco conectados entre sí.

El proyecto propone integrar datos públicos, catastrales, turísticos, sociodemográficos y territoriales para responder una pregunta central:

**¿Cuánta presión soporta cada municipio, dónde se concentra y qué señales tempranas permiten anticipar problemas antes de que sean irreversibles?**

## Objetivos

### Objetivo general

Crear un piloto funcional que permita analizar la presión territorial vinculada a vivienda y turismo en Berga y Castellar de n’Hug, mediante una combinación de datos abiertos, análisis geoespacial, indicadores propios, dashboard e inteligencia artificial aplicada a la generación de informes.

### Objetivos específicos

1. Integrar datos municipales dispersos en una base analítica común.

2. Construir una radiografía comparada de vivienda, turismo y territorio para ambos municipios.

3. Diseñar un índice inicial de presión turística-residencial.

4. Visualizar los datos mediante mapas, gráficos y fichas municipales.

5. Generar informes narrativos asistidos por IA, revisados editorialmente.

6. Validar si el modelo puede escalarse a otros municipios del Berguedà.

## Usuarios objetivo

### Usuarios institucionales

* Ayuntamientos.
* Consell Comarcal.
* Diputació.
* Áreas de urbanismo, turismo, vivienda, promoción económica y desarrollo local.
* Técnicos municipales.
* Equipos de gobierno.

### Usuarios estratégicos

* Consultoras territoriales.
* Agencias de desarrollo local.
* Oficinas de turismo.
* Asociaciones empresariales.
* Entidades vinculadas a vivienda, patrimonio o sostenibilidad territorial.

### Usuarios futuros

* Investigadores.
* Periodistas de datos.
* Plataformas ciudadanas.
* Empresas interesadas en análisis territorial de pequeños municipios.

## Alcance del piloto

### Municipios incluidos

* Berga.
* Castellar de n’Hug.

### Sectores incluidos

* Vivienda.
* Turismo.
* Estructura urbana.
* Actividad inmobiliaria.
* Patrimonio y atractivos turísticos.
* Presión estacional.
* Capacidad territorial.
* Rehabilitación y parque construido.

### Nivel de análisis

* Municipio.
* Núcleo urbano.
* Sección o zona agregada cuando sea posible.
* Parcela o edificio cuando la fuente lo permita.
* Punto geolocalizado para alojamientos, equipamientos y atractivos.

## Fuera de alcance en la primera versión

La primera versión no incluirá:

* Datos personales.
* Titularidad individualizada de inmuebles.
* Predicción inmobiliaria avanzada con modelos de precio.
* Sensorización física.
* Datos móviles de operadoras.
* Integración con expedientes administrativos internos.
* Portal público definitivo.
* Sistema transaccional.
* Automatización completa sin revisión humana.

Estos elementos pueden considerarse en fases posteriores si existe interés institucional, viabilidad jurídica y presupuesto.

## Preguntas que debe responder el sistema

### Vivienda

* ¿Cómo se distribuye el parque de vivienda por antigüedad, superficie y uso?
* ¿Qué zonas presentan mayor envejecimiento del parque construido?
* ¿Dónde puede haber mayor oportunidad de rehabilitación?
* ¿Qué peso tiene la vivienda principal frente a la vivienda secundaria?
* ¿Qué áreas podrían estar sometidas a tensión residencial?

### Turismo

* ¿Cuántos alojamientos turísticos registrados hay en cada municipio?
* ¿Dónde se concentran?
* ¿Qué peso tienen sobre el conjunto del parque residencial?
* ¿Qué relación existe entre alojamiento turístico, atractivos, accesos y centralidad urbana?
* ¿Qué zonas pueden estar soportando una presión excesiva en determinados momentos del año?

### Territorio

* ¿Qué partes del municipio acumulan más presión?
* ¿Qué zonas combinan atractivo turístico, fragilidad residencial y limitaciones de acceso?
* ¿Qué diferencias aparecen entre Berga y Castellar de n’Hug?
* ¿Qué patrones podrían replicarse en otros municipios del Berguedà?

### Gestión pública

* ¿Qué decisiones municipales podrían apoyarse en estos datos?
* ¿Dónde convendría priorizar rehabilitación, regulación, movilidad o diversificación turística?
* ¿Qué indicadores deberían monitorizarse de forma periódica?
* ¿Cómo puede explicarse la situación del municipio de manera clara ante vecinos, técnicos y responsables políticos?

## Fuentes de datos iniciales

### Catastro

Uso previsto:

* Parcelas.
* Edificios.
* Direcciones.
* Superficie construida.
* Usos.
* Antigüedad.
* Tipologías.
* Geometría de edificios y parcelas.

Valor para el proyecto:

Permite construir la base física del municipio: qué existe, dónde está, qué características tiene y cómo se organiza el parque construido.

### Idescat

Uso previsto:

* Población.
* Hogares.
* Viviendas.
* Indicadores municipales.
* Comparativa con comarca y Cataluña.
* Evolución demográfica.
* Datos del censo de población y viviendas.

Valor para el proyecto:

Permite situar cada municipio en contexto y construir indicadores relativos, evitando lecturas engañosas basadas solo en magnitudes absolutas.

### Registre de Turisme de Catalunya

Uso previsto:

* Establecimientos turísticos inscritos.
* Categoría.
* Dirección.
* Municipio.
* Tipología de alojamiento.
* Posible geolocalización derivada.

Valor para el proyecto:

Permite construir la capa oficial de alojamiento turístico regulado y compararla con vivienda, población, atractivos y estructura urbana.

### Datos municipales y turísticos públicos

Uso previsto:

* Equipamientos.
* Puntos de interés.
* Aparcamientos.
* Rutas.
* Patrimonio.
* Agenda de eventos.
* Recursos turísticos.
* Oficinas de turismo.
* Servicios públicos.

Valor para el proyecto:

Ayuda a interpretar la presión turística desde la experiencia real del municipio: por dónde entra la gente, dónde se concentra, qué consume y qué zonas quedan invisibles.

### Scraping público

Uso previsto:

* Oferta turística visible.
* Precios publicados.
* Presencia en plataformas.
* Reseñas.
* Actividad comercial.
* Eventos.
* Señales de demanda.
* Contenido turístico indexado.

Valor para el proyecto:

Permite detectar capas de realidad que no siempre aparecen en los registros oficiales. Debe aplicarse con prudencia, trazabilidad y respeto normativo.

### Datos geográficos abiertos

Uso previsto:

* Cartografía base.
* Límites administrativos.
* Red viaria.
* Hidrografía.
* Espacios naturales.
* Pendientes.
* Altitud.
* Usos del suelo si están disponibles.

Valor para el proyecto:

Permite incorporar el territorio físico al análisis, especialmente importante en municipios de montaña.

## Modelo de datos conceptual

### Entidades principales

**Municipio**
Unidad administrativa principal.

**Zona**
Agrupación territorial interna: núcleo, barrio, área de análisis o sección.

**Parcela**
Unidad catastral territorial.

**Edificio**
Construcción asociada a una parcela.

**Vivienda**
Unidad residencial cuando pueda inferirse o agregarse.

**Alojamiento turístico**
Establecimiento inscrito o detectado en fuentes públicas.

**Atractivo turístico**
Recurso natural, cultural, patrimonial o comercial.

**Evento**
Actividad temporal con potencial impacto en movilidad, alojamiento o consumo.

**Indicador**
Métrica calculada para comparar zonas, municipios o evolución temporal.

**Informe**
Documento narrativo generado a partir de datos, visualizaciones y análisis.

## Indicadores iniciales

### Indicadores de vivienda

* Número estimado de viviendas.
* Superficie media construida.
* Antigüedad media de edificios.
* Distribución por tipología.
* Peso de vivienda principal.
* Peso de vivienda secundaria.
* Zonas con parque construido envejecido.
* Potencial de rehabilitación.

### Indicadores turísticos

* Alojamientos turísticos registrados.
* Alojamientos por 100 viviendas.
* Alojamientos por 1.000 habitantes.
* Concentración espacial de alojamientos.
* Distancia media a atractivos turísticos.
* Tipología dominante de alojamiento.
* Peso turístico relativo por zona.

### Indicadores de presión territorial

* Índice de presión turística-residencial.
* Índice de concentración turística.
* Índice de vulnerabilidad residencial.
* Índice de dependencia estacional.
* Índice de fragilidad de acceso.
* Índice de oportunidad de rehabilitación.

### Indicadores comparativos

* Berga frente a Castellar de n’Hug.
* Municipio frente a comarca.
* Municipio frente a Cataluña.
* Núcleo urbano frente a entorno municipal.
* Turismo registrado frente a parque residencial.

## Índice de presión turística-residencial

### Definición inicial

Indicador compuesto que estima la intensidad de la presión turística sobre la estructura residencial del municipio.

### Variables candidatas

* Alojamientos turísticos por 100 viviendas.
* Alojamientos turísticos por 1.000 habitantes.
* Concentración espacial de alojamientos.
* Peso de vivienda secundaria.
* Antigüedad del parque construido.
* Proximidad a atractivos turísticos.
* Limitaciones de acceso o aparcamiento.
* Estacionalidad detectada.
* Densidad comercial orientada al visitante.

### Interpretación

El índice no debe presentarse como una verdad cerrada, sino como una herramienta de lectura comparativa.

Sirve para detectar zonas donde conviene mirar mejor, no para emitir sentencias automáticas.

### Escala propuesta (orientativa)

* 0-20: presión baja.
* 21-40: presión moderada.
* 41-60: presión relevante.
* 61-80: presión alta.
* 81-100: presión muy alta.

## Arquitectura funcional (orientativa)

### Capa 1: Ingesta de datos

* Descarga de datasets abiertos.
* Extracción de ficheros catastrales.
* Integración de datos turísticos.
* Scraping público controlado.
* Normalización de formatos.
* Registro de fuente, fecha y licencia.

### Capa 2: Limpieza y transformación

* Homogeneización de nombres de municipio.
* Normalización de direcciones.
* Geocodificación.
* Eliminación de duplicados.
* Validación de campos.
* Conversión geoespacial.
* Agregación por zonas.

### Capa 3: Base analítica

* Modelo relacional para entidades.
* Modelo geoespacial para capas.
* Tablas de indicadores.
* Histórico de actualizaciones.
* Diccionario de datos.
* Catálogo semántico.

### Capa 4: Motor de análisis

* Cálculo de indicadores.
* Comparativas municipales.
* Detección de concentración espacial.
* Segmentación territorial.
* Construcción del índice de presión.
* Identificación de zonas prioritarias.

### Capa 5: Visualización

* Dashboard interactivo.
* Mapas.
* Fichas municipales.
* Gráficos comparativos.
* Tablas descargables.
* Panel ejecutivo.

### Capa 6: Inteligencia artificial

* Generación asistida de informes.
* Explicación de indicadores.
* Consultas en lenguaje natural.
* Resumen ejecutivo automático.
* Detección de hipótesis.
* Asistente para preguntas territoriales.

## Dashboard mínimo viable (pantallas orientativas)

### Pantalla 1: Visión general

Contenido:

* Resumen de Berga.
* Resumen de Castellar de n’Hug.
* Comparativa rápida.
* Indicadores principales.
* Alertas o zonas de interés.

### Pantalla 2: Mapa territorial

Contenido:

* Parcelas.
* Edificios.
* Alojamientos turísticos.
* Atractivos.
* Equipamientos.
* Capas activables.
* Filtros por municipio y zona.

### Pantalla 3: Vivienda

Contenido:

* Antigüedad del parque construido.
* Superficie construida.
* Tipologías.
* Vivienda principal y secundaria si está disponible.
* Potencial de rehabilitación.
* Comparativa entre municipios.

### Pantalla 4: Turismo

Contenido:

* Alojamientos registrados.
* Tipologías.
* Concentración.
* Proximidad a puntos de interés.
* Ratio turismo-vivienda.
* Posibles señales de estacionalidad.

### Pantalla 5: Presión territorial

Contenido:

* Índice de presión turística-residencial.
* Mapa de calor.
* Ranking de zonas.
* Variables explicativas.
* Recomendaciones iniciales.
* Exportación de ficha o informe.

### Pantalla 6: Consulta con IA

Contenido:

* Preguntas en lenguaje natural.
* Respuestas basadas en datos.
* Generación de resúmenes.
* Explicación de gráficos.
* Generación de borradores de informe.
* Trazabilidad de fuentes usadas.

## Informes generables

### Informe municipal individual

Un informe para Berga y otro para Castellar de n’Hug.

Estructura:

* Resumen ejecutivo.
* Contexto municipal.
* Vivienda.
* Turismo.
* Territorio.
* Presión detectada.
* Zonas prioritarias.
* Recomendaciones.
* Anexos de datos.

### Informe comparativo

Documento que contraste ambos municipios.

Estructura:

* Diferencias estructurales.
* Diferencias de escala.
* Diferencias de modelo turístico.
* Riesgos específicos.
* Indicadores relativos.
* Lecturas estratégicas.
* Posible escalado comarcal.

### Informe ejecutivo de venta

Documento breve para presentar a ayuntamientos o instituciones.

Estructura:

* Problema.
* Solución.
* Qué datos se usan.
* Qué preguntas responde.
* Qué entregables se obtienen.
* Cómo se implementa.
* Qué coste aproximado tendría una fase piloto.

## Inteligencia artificial

### Usos

* Resumir datos.
* Explicar indicadores.
* Redactar informes.
* Generar hipótesis.
* Traducir consultas de lenguaje natural a consultas estructuradas.
* Ayudar a explorar patrones.
* Crear fichas ejecutivas.

### Usos a testear

* Tomar decisiones automáticas.
* Emitir diagnósticos normativos definitivos.
* Sustituir criterio técnico municipal.
* Generar conclusiones sin fuente.
* Mezclar datos verificados con hipótesis sin distinguirlos.
* Presentar estimaciones como hechos.

### Principio de diseño

La IA debe ser una capa de interpretación y conversación sobre datos trazables.

Cada respuesta debe poder explicar:

* Qué fuente usa.
* Qué indicador consulta.
* Qué fecha tiene el dato.
* Qué limitaciones existen.
* Qué parte es dato y qué parte es inferencia.

## Piloto

### Dataset integrado

Contenido:

* Datos catastrales procesados.
* Datos turísticos integrados.
* Indicadores municipales.
* Capas geográficas.
* Diccionario de datos.
* Registro de fuentes.

Formato:

* CSV.
* GeoJSON.
* Parquet si procede.
* Base DuckDB o PostgreSQL.

### Entregable 2: Dashboard funcional

Contenido:

* Pantallas principales.
* Filtros.
* Mapas.
* Comparativas.
* Indicadores.
* Exportación básica.

Formato:

* Web app privada.
* Demo navegable.

### Entregable 3: Informe analítico

Contenido:

* Informe Berga.
* Informe Castellar de n’Hug.
* Comparativa.
* Índice de presión.
* Recomendaciones.
* Limitaciones.

Formato:

* PDF.
* Documento editable.

### Entregable 4: Ficha comercial

Contenido:

* Propuesta de valor.
* Problema que resuelve.
* Módulos disponibles.
* Fuentes de datos.
* Ejemplos de preguntas.
* Roadmap de escalado.

Formato:

* One pager.
* Presentación breve opcional.

### Entregable 5: Catálogo semántico inicial

Contenido:

* Definición de entidades.
* Definición de indicadores.
* Relaciones entre conceptos.
* Preguntas tipo.
* Glosario.

Formato:

* Documento técnico.
* Tabla estructurada.

## Métricas de éxito

### Técnicas

* Número de fuentes integradas.
* Porcentaje de registros geolocalizados.
* Número de indicadores calculados.
* Tiempo de actualización del dataset.
* Número de visualizaciones funcionales.
* Tasa de respuestas IA con fuente trazable.

### Estratégicas

* Claridad del diagnóstico.
* Utilidad percibida por usuarios municipales.
* Capacidad de detectar zonas prioritarias.
* Facilidad de explicación pública.
* Potencial de escalado.
* Interés comercial generado.

## Roadmap posterior

### V1

* Ampliar a más municipios del Berguedà.
* Incorporar más capas de movilidad.
* Añadir histórico de precios si se dispone de fuente fiable.
* Mejorar índice de presión.
* Crear alertas periódicas.
* Incorporar exportación automática de informes.

### V2

* Observatorio comarcal.
* Portal institucional.
* Comparador entre municipios.
* Módulo de escenarios.
* Módulo de políticas públicas.
* Integración con datos internos municipales.

### V3

* Producto replicable para municipios de montaña, patrimonio y turismo interior.
* Licencia SaaS para instituciones.
* Informes automáticos bajo demanda.
* Asistente territorial conversacional.
* Marketplace de análisis sectoriales.