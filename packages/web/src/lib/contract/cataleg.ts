/**
 * Catàleg de municipis de Catalunya — forma de `data/municipis-cataleg.json`.
 *
 * El genera el prebuild (`scripts/copy-data.mjs` · `buildCataleg`) des de la geometria oficial
 * `static/geo/catalunya-municipis.geojson`. És la columna vertebral de «tota Catalunya»: el cens
 * de noms+codis de TOTS els municipis (~947), perquè el cercador hi cerqui i la fitxa hi resolgui
 * qualsevol slug → ine5 + nom. NO és cap dada de població ni xifra; el slug es deriva del nom en
 * runtime amb `toSlug` (la lògica viu només a `$lib/contract/slug`).
 */

export interface MuniCataleg {
	/** Codi INE de 5 dígits (clau interna, join key del contracte). */
	ine5: string;
	/** Nom oficial del municipi (per a cerca i pantalla). */
	nom: string;
}

export type CatalegData = MuniCataleg[];
