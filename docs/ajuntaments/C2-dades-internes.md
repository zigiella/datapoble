# C2 · Contracte de dades internes municipals — contracte de disseny (abans del connector)

**De:** Talaia (owner) · **Implementa:** Sondeig (tasca D3) · **Data:** 2026-07-16
**Origen:** `docs/spec-ajuntaments-v1.md` §3 (C2), esmenat per §10 **E1** (que hi mana) i E4.
**Ordre:** aquest contracte es fusiona **abans** de cap línia del connector `municipal_csv`. Les decisions d'aquí són tancades: el connector les implementa, no les reinterpreta.

> El perill d'aquest contracte no és tècnic, és de confiança: un ajuntament ens dona un número que cap font pública té. Si aquell número apareix on no toca, no hi ha segona oportunitat. Per això la regla de visibilitat va primer i mana sobre tota la resta.

## 1. Política mare (citada, no reinventada)

La convenció de capes és la de **`docs/data-sources.md` §0 (Convención de visibilidad)**: etiquetes que s'hereten a indicadors, taules i sortides, i la regla del join — **creuament de capa interna × capa pública = resultat intern**. C2 no crea cap mecanisme paral·lel: `publicable: false` **és** capa interna en aquella convenció, i n'hereta totes les conseqüències.

**E1, la regla de ferro:** aquest repo és PÚBLIC; un fitxer `publicable: false` committejat seria públic de facto. Per tant:

1. **Al repo només entra dada `publicable: true`.** Sense excepcions, tampoc «temporals».
2. Els indicadors interns **mai toquen el repo públic**: ni fitxers, ni fixtures amb valors reals, ni logs de CI, ni artefactes de workflow públics, ni missatges de commit.
3. Al web només hi arriben **agregats publicables**. En v1, l'única sortida dels indicadors interns és el **correu**; qualsevol «mode intern» autenticat al web queda fora d'abast.

## 2. Esquema del CSV (tancat)

- **Un indicador per fitxer.** Nom de fitxer: `<indicador>.csv` en kebab-case (p. ex. `consum-aigua-m3.csv`).
- **Columnes:** `data,valor` amb capçalera obligatòria; tercera columna `nota` opcional (text lliure, curt).
- **`data`:** ISO `AAAA-MM-01` (freqüència **mensual**, una fila per mes, primer dia del mes). Dates duplicades = error de validació.
- **`valor`:** numèric, separador decimal **punt**, sense milers. **Només valors ≥ 0**: la v1 no admet indicadors que necessitin negatius (si en cal un, s'esmena aquest contracte primer).
- **Codificació:** UTF-8; separador coma.
- **NOMÉS agregats de municipi.** Mai persones, mai adreces, mai res reidentificable — tampoc a la columna `nota`. Això no és una validació tècnica sinó una condició d'entrada: un CSV que ho incompleixi es rebutja sencer i s'avisa l'ajuntament.
- Codi de municipi: `ine5` INE/Idescat (la Pobla de Lillet = **08166**; Castellar de n'Hug = **08052**). El connector porta el test de la trampa de codis (§2 de l'spec).

## 3. Mapa de camins: on viu cada capa

**Publicable (`publicable: true`) — al repo públic:**

- Dada: `data/municipal/<ine5>/<indicador>.csv`
- Manifest: `data/municipal/<ine5>/indicadors.yml` — un bloc per indicador amb `nom`, `descripcio`, `unitat`, `publicable: true`, `llindar_alerta` (opcional) i la referència a la decisió de l'ajuntament (§7). El manifest públic **només llista indicadors publicables**: el nom d'un indicador intern també és informació interna.
- Definició semàntica: entrada a `semantic/metrics.yml` amb el camp `visibilitat` que C1 introdueix (E4), etiquetada de capa visible (🟢 de §0).

**Intern (`publicable: false`) — mai al repo públic:**

- **Canal d'entrada (concret):** l'ajuntament envia el CSV a **Bea** (correu, canal manual — coherent amb la procedència §6). Bea el diposita al **magatzem privat**.
- **Magatzem privat (concret):** un **repo GitHub privat separat** (`datapoble-privat`), amb la mateixa estructura `municipal/<ine5>/…` i el seu propi `indicadors.yml` i fitxa semàntica (mateix esquema que C1, fitxer `metrics-intern.yml` al privat — la definició d'un indicador intern tampoc entra al `metrics.yml` públic).
- **Accés del workflow:** només via secret de workflow (deploy key, p. ex. `MUNICIPAL_PRIVAT_KEY`), mai al codi ni al CI de PR (principi «secrets només a workflows» del §1 de l'spec).
- **Aquest contracte mana:** cap pas del pipeline pot copiar, cachejar ni materialitzar dada del privat dins del repo públic ni dels seus artefactes. Un PR que ho faci es tanca sense fusionar i es neteja l'historial abans que res més.

## 4. Validació del connector (tancada)

En aquest ordre, i **el fitxer sencer o res** (mai publicació parcial de files):

1. **Esquema:** capçalera, tipus, format de data, codificació. Falla → rebuig amb motiu d'una línia.
2. **Monotonia de dates:** estrictament creixents, sense duplicats.
3. **No-negatius:** cap `valor < 0`.
4. **Salt anòmal:** `valor > 3 × anterior` o `valor < anterior / 3` (amb `anterior > 0`; si `anterior = 0` no s'aplica) → el fitxer va a **quarantena** + **avís per correu a Bea**. La quarantena no publica ni descarta: reté fins a revisió humana.
5. **La quarantena viu al mateix nivell de visibilitat que la dada:** quarantena d'un fitxer intern → al magatzem privat; d'un publicable → fora del web igualment (no entra al mart fins que un humà la validi).

## 5. `llindar_alerta` (opcional)

Per indicador, al manifest: `llindar_alerta: {operador: ">"|"<", valor: N}`. Quan es creua: **correu** (destinatari en v1: **Bea**; ampliable només per decisió de l'ajuntament titular, com al R4). **Mai publicació automàtica**, mai al web, mai cap acció fora del correu. Una alerta no canvia la visibilitat de res.

## 6. Procedència i visibilitat

Cada valor porta procedència **`municipal · <ajuntament> · manual`** (cap número sense font, data i fórmula — contracte C1). El camp `visibilitat` de C1 s'assigna així: `publicable: true` → capa visible; `publicable: false` → capa interna (§0). Qualsevol mart, agregat o resposta del xat que combini un indicador intern amb dada pública **hereta la capa interna** i, per tant, no surt al web.

## 7. La porta de `publicable` (única)

- **Per defecte, tot indicador nou neix `publicable: false`.** Privacitat per disseny: publicar és l'excepció que es demana, no l'estat que s'assumeix.
- **L'única porta cap a `true` és la decisió expressa de l'ajuntament titular** (un correu val), arxivada al magatzem privat i referenciada al manifest. Ni Bea, ni Talaia, ni cap front la pot substituir.
- **Honestedat sobre la irreversibilitat:** publicar al repo públic deixa historial git. Revocar el consentiment retira l'indicador del web i del repo cap endavant, però l'historial és de facto permanent. La decisió de l'ajuntament es demana **fent-li saber això** — mai es ven la revocació com a esborrat total.

## 8. Dins / fora d'aquest contracte

**Dins:** esquema CSV, camins públic/privat, canal d'entrada, validació i quarantena, llindar d'alerta, procedència, porta de publicable.
**Fora:** el contingut concret dels indicadors de la Pobla (D6, amb l'Ajuntament); el mode govern que els mostra (C6/D5); qualsevol sortida impresa (post-v1); indicadors amb valors negatius o freqüència no mensual (esmena prèvia obligatòria); qualsevol «mode intern» al web.

## 9. Llistó de verificació (per acceptar D3)

- CI verd **offline** amb fixtures **sintètiques etiquetades «demo»** — cap valor real, ni publicable, al fixture.
- Test de cada regla del §4 (esquema, monotonia, no-negatius, salt ×3 → quarantena) + test de la trampa de codis.
- Grep verificable: cap referència al magatzem privat fora de workflows amb secret; cap fitxer sota `data/municipal/` sense entrada `publicable: true` al manifest.
- L'alerta de llindar surt per correu en el workflow i **no existeix cap camí de codi** que la porti al web.
- Revisió adversarial de Talaia contra aquest contracte, punt per punt, abans de fusionar.
