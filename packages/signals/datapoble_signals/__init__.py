"""datapoble · signals (el cabal) — pilar 2: intel·ligència territorial des dels
rastres administratius i digitals que el territori deixa.

La idea (el principi dels kg de residus, generalitzat): quan un fenomen no té un
dataset net, el seu *rastre* sí que existeix —algú ha hagut de contractar el
servei, publicar un edicte, declarar una restricció—. Aquesta capa normalitza
aquests rastres a una taula única d'**events** (una fila per senyal), amb
traçabilitat (cada event amb el seu ``font_url``) i la frontera dada/inferència
sempre explícita.

Scope d'aquest PR (primer): la taula ``events`` (el contracte de la capa) + UN
rastre — el **connector de contractació** (Socrata ``ybgg-dgi6``). Pilot: el
Berguedà (Castellar, Berga, la resta + el Consell Comarcal).

Fora d'aquest PR: el motor de **convergència** (repartir el senyal comarcal als
micromunicipis), el connector de **sequera** (DOGC/ACA), l'extracció **LLM** per a
fonts messy, i l'escala Catalunya.
"""

__version__ = "0.1.0"
