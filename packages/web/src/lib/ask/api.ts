/**
 * Client de l'API de Brúixola (la IA traçable) per a la pàgina «Pregunta-li».
 *
 * És la ÚNICA frontera entre el web estàtic (adapter-static, sense servidor) i el
 * servei de preguntes (FastAPI a Render). La crida és CLIENT-SIDE (fetch des del
 * navegador) cap a una URL pública configurable per entorn (`PUBLIC_API_BASE`):
 * el build estàtic ha de funcionar SENSE l'API viva, i la pàgina degrada amablement
 * si no respon (vegeu `AskOutcome` amb `kind: 'unreachable'`).
 *
 * El CONTRACTE (forma exacta de `/ask`, NO inventada) viu aquí com a tipus, perquè
 * el component de pàgina només consumeixi dades ja tipades. Camps i valors segueixen
 * l'especificació de Brúixola: kind answer|refusal, backend offline|openrouter,
 * provenance amb la query SQL (la signatura de confiança del projecte) i refusal_reason
 * d'un conjunt tancat.
 */

import { PUBLIC_API_BASE } from '$env/static/public';
import type { Locale } from '$lib/contract/types';

/** Resultat de la consulta: resposta humana o refús honest. */
export type AskKind = 'answer' | 'refusal';

/** Qui ha resolt la pregunta: motor determinista offline o un model via OpenRouter. */
export type AskBackend = 'offline' | 'openrouter';

/**
 * Motiu del refús (conjunt TANCAT del contracte). Cada valor té un missatge amable
 * propi a la UI: el refús és una FEATURE d'honestedat, no un error a amagar.
 */
export type RefusalReason =
	| 'out_of_catalog'
	| 'metric_planned'
	| 'unknown_municipality'
	| 'unsupported_question'
	| 'guardrail_violation'
	| 'budget_exceeded'
	| 'rate_limited';

/**
 * Procedència de la resposta: la traça que fa la xifra creïble. `query` és la SQL
 * exacta executada (es mostra en mono, prominent). `is_fixture` marca dada de prova.
 */
export interface AskProvenance {
	metric: string | null;
	metric_label: string | null;
	source: string | null;
	source_key: string | null;
	date: string | null;
	formula: string | null;
	query: string | null;
	params: Record<string, unknown> | null;
	license: string | null;
	note: string | null;
	is_fixture: boolean;
}

/** Una fila de les dades crues darrere la resposta (forma lliure: clau → valor). */
export type AskRow = Record<string, unknown>;

/** Cos JSON exacte que retorna `POST {API_BASE}/ask`. */
export interface AskResponse {
	kind: AskKind;
	text: string;
	backend: AskBackend;
	data: AskRow[];
	provenance: AskProvenance | null;
	refusal_reason: RefusalReason | null;
	metric_key: string | null;
}

/**
 * Resultat normalitzat per a la UI. A diferència de `AskResponse`, distingeix també
 * els estats de XARXA que no formen part del cos JSON però que la pàgina ha de tractar
 * amablement: `unreachable` (l'API no respon: Render dormint, CORS, sense connexió) i
 * `rate_limited` quan arriba com a HTTP 429 (amb `retryAfter` de la capçalera Retry-After).
 */
export type AskOutcome =
	| { kind: 'ok'; response: AskResponse }
	| { kind: 'rate_limited'; retryAfter: number | null }
	| { kind: 'unreachable' };

/**
 * Base de l'API, configurable via env pública de SvelteKit (`PUBLIC_API_BASE`).
 * Es llegeix amb `$env/static/public` (s'INCRUSTA al build), perquè el web és estàtic
 * (adapter-static, sense servidor) i `$env/dynamic/public` quedaria BUIT al navegador.
 * El default que evita trencar el build quan la variable no hi és viu a
 * `packages/web/.env` (`PUBLIC_API_BASE=""`); el deploy l'injecta amb la URL real.
 * Default de dev a `http://localhost:8000`. Buida o no definida → sense API: la
 * pàgina ho tracta com a `unreachable` i mostra l'avís amable.
 */
export function apiBase(): string {
	const raw = (PUBLIC_API_BASE ?? '').trim();
	if (raw) return raw.replace(/\/+$/, ''); // sense barra final
	// Default només útil en desenvolupament local; en estàtic pur queda buit.
	if (import.meta.env.DEV) return 'http://localhost:8000';
	return '';
}

/** True si hi ha una base d'API configurada (si no, ni intentem la crida). */
export function hasApi(): boolean {
	return apiBase().length > 0;
}

/** Llegeix `Retry-After` (segons) si hi és i és un enter vàlid; si no, null. */
function parseRetryAfter(res: Response): number | null {
	const h = res.headers.get('Retry-After');
	if (!h) return null;
	const secs = Number.parseInt(h, 10);
	return Number.isFinite(secs) && secs >= 0 ? secs : null;
}

/**
 * Fa la pregunta a l'API i retorna un `AskOutcome` normalitzat (mai llança per
 * condicions esperades: xarxa caiguda, 429, JSON dolent → es tradueixen a estats).
 *
 * @param question  text de la pregunta de l'usuari
 * @param locale    locale actiu (ca|es) — l'API retorna el `text` ja en aquest idioma
 * @param signal    AbortSignal opcional (cancel·lar la petició anterior)
 */
export async function ask(
	question: string,
	locale: Locale,
	signal?: AbortSignal
): Promise<AskOutcome> {
	const base = apiBase();
	if (!base) return { kind: 'unreachable' };

	let res: Response;
	try {
		res = await fetch(`${base}/ask`, {
			method: 'POST',
			headers: { 'content-type': 'application/json', accept: 'application/json' },
			body: JSON.stringify({ question, locale }),
			signal
		});
	} catch {
		// Fetch ha fallat (DNS, CORS, offline, servei dormint): degradació amable.
		return { kind: 'unreachable' };
	}

	// 429 → refús rate_limited amb Retry-After (capçalera). El cos pot venir buit.
	if (res.status === 429) {
		return { kind: 'rate_limited', retryAfter: parseRetryAfter(res) };
	}

	if (!res.ok) {
		// Qualsevol altre error HTTP no contemplat pel contracte: tracta'l com a
		// servei no disponible (millor un avís amable que una pantalla trencada).
		return { kind: 'unreachable' };
	}

	let body: AskResponse;
	try {
		body = (await res.json()) as AskResponse;
	} catch {
		return { kind: 'unreachable' };
	}

	return { kind: 'ok', response: body };
}
