# Paquet de consultoria — datapoble (juny 2026)

Material per a una revisió externa del projecte **datapoble** (observatori territorial; *riusdegent*).
Moment de **parar, triar i orientar prioritats** abans de seguir construint.

## Què hi ha

| Fitxer | Què és |
|---|---|
| **`00-dossier.md`** | El document central: estat honest del projecte, **3 conceptes de web** possibles (amb justificació i recomanació), **auditoria d'indicadors** (defensa · crítica · veredicte), **metodologia** (defensa · qüestions obertes), brief de redisseny de la **fitxa de municipi**, i decisions de navegació/UI. |
| **`01-reconduccio.md`** | La **decisió de rumbo** (adoptada): resposta de la consultoria externa al dossier. Verificació de la peça clau (Idescat ja cobreix ≥1.000 hab; Barcelona ETCA positiva), target/propòsit/concepte (**«l'observatori que sap el que no sap»**), **contracte d'abast** i pla per **fases (0–5)**. Concilia la crítica externa amb el dossier. |
| **`municipis-catalunya.csv`** | La **base de dades** sencera: 947 municipis de Catalunya × 54 indicadors (ine5, codi6, nom, comarca, vegueria + tots els valors). Plana, llesta per a anàlisi. |
| **`diccionari-indicadors.csv`** | El **diccionari**: per a cada indicador, etiqueta (ca/es), dimensió, unitat, format, **font** (procedència) i **definició** canònica. |

## Com llegir-ho
1. Comença pel **dossier** (`00-dossier.md`) — §2 (concepte) i §3 (indicadors) van plantejar el debat.
2. Després la **reconducció** (`01-reconduccio.md`) — la **decisió** presa (concepte, abast, fases).
3. El **diccionari** dona el significat exacte de cada columna de la base de dades.
4. La **base de dades** permet verificar, reanalitzar o visualitzar pel vostre compte.

## Procedència
Tot surt del contracte semàntic i dels marts del projecte (cap número inventat; estimació ≠ cens).
Les dades es regeneren amb `tools/export_dossier.py`. El web públic: [datapoble] (en construcció).

## Què demanem
Validar/desafiar el **concepte**, ajudar a **prioritzar i tallar** indicadors, revisar el redisseny
de la **fitxa**, i donar criteri sobre **com explicar** cada mapa. (Detall a §8 del dossier.)
