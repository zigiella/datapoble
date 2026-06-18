<script lang="ts">
	/**
	 * Layout arrel — chrome compartit segons la DA final (captures 01 i 07).
	 *
	 * Capçalera `.ds-top` (sticky): marca SVG (ocre) + wordmark rius·degent + sub-tagline
	 * mono, navegació (Resum/Mapa actius; la resta inerts en aquesta fase) i, a la dreta,
	 * commutador d'idioma (CA/ES) + de tema (sol/lluna).
	 * Peu `.ap-foot` dissenyat: 4 columnes (marca+missió+segell · Explora · El projecte ·
	 * controls idioma/tema) + barra inferior legal amb coordenades i data.
	 *
	 * Tot el CSS ve del design-system (app.css importa tokens + sistema + aplicacio); aquí
	 * només hi ha estructura i el cablejat d'i18n (m.*) i de navegació localitzada.
	 */
	import '../app.css';
	import LangSwitcher from '$lib/components/LangSwitcher.svelte';
	import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';
	import ContourField from '$lib/components/ContourField.svelte';
	import { localizeHref, deLocalizeUrl, currentLocale } from '$lib/i18n';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { m } from '$lib/paraglide/messages';

	let { children } = $props();

	// Estat del menú mòbil (hamburger). Es tanca amb Escape o en triar una destinació.
	let menuOpen = $state(false);

	// `isActive` compara contra rutes CANÒNIQUES (sense prefix de locale: /resum…), però
	// `page.url.pathname` el conserva a /es/* (el reroute de Paraglide des-localitza el routing
	// de fitxers, no la URL observable). Sense des-localitzar, cap ítem del nav s'activa a /es/*.
	// `deLocalizeUrl` clona la URL (no muta `page.url`) i treu el segment de locale:
	// /es/resum/ → /resum · /resum/ (ca) intacte → tots dos casen amb isActive.
	const path = $derived(deLocalizeUrl(page.url).pathname);
	function isActive(p: string): boolean {
		return path === p || path.startsWith(p + '/');
	}

	// SEO: canonical + hreflang + Open Graph a partir de la URL localitzada actual.
	// `path` és la ruta canònica (sense prefix); localizeHref hi torna a posar /ca|/es.
	const SITE = 'https://riusdegent.cat';
	const canonicalUrl = $derived(SITE + page.url.pathname);
	const altCa = $derived(SITE + localizeHref(path, { locale: 'ca' }));
	const altEs = $derived(SITE + localizeHref(path, { locale: 'es' }));
	const ogLocale = $derived(currentLocale() === 'es' ? 'es_ES' : 'ca_ES');
	const ogLocaleAlt = $derived(currentLocale() === 'es' ? 'ca_ES' : 'es_ES');

	// Corbes del peu (cims + divisòria + etiquetes de dada real), com al target.
	const footSummits = [
		{ cx: 250, cy: 120, r0: 16, step: 24, rings: 8, sq: 0.95, seed: 0.6, lt: 0.02 },
		{ cx: 980, cy: 90, r0: 14, step: 22, rings: 8, sq: 1.05, seed: 2.3, lt: 0.04 }
	];
	const footDivis = { cx: 600, cy: 110, r: 150, sq: 1.0, seed: 1.4 };
	const footLabels = ['1.245 m', '42°16′N', '31', '1°53′E', '593'];
</script>

<svelte:head>
	<link rel="canonical" href={canonicalUrl} />
	<link rel="alternate" hreflang="ca" href={altCa} />
	<link rel="alternate" hreflang="es" href={altEs} />
	<link rel="alternate" hreflang="x-default" href={altCa} />
	<meta property="og:type" content="website" />
	<meta property="og:site_name" content={m.app_name()} />
	<meta property="og:title" content={`${m.app_name()} · ${m.app_tagline()}`} />
	<meta property="og:description" content={m.brand_sub()} />
	<meta property="og:url" content={canonicalUrl} />
	<meta property="og:locale" content={ogLocale} />
	<meta property="og:locale:alternate" content={ogLocaleAlt} />
</svelte:head>

<svelte:window onkeydown={(e) => { if (e.key === 'Escape') menuOpen = false; }} />

<a class="skip-link" href="#main">{m.skip_to_content()}</a>

<!-- ============================ CAPÇALERA ============================ -->
<header class="ds-top">
	<a class="ds-top__brand" href={localizeHref('/')} aria-label={m.app_name()}>
		<img src="{base}/brand/riusdegent-mark.svg" width="30" height="30" alt="" />
		<span class="txt">
			<span class="wm">rius<b>degent</b></span>
			<span class="sub">{m.brand_sub()}</span>
		</span>
	</a>
	<nav class="ds-nav" aria-label="Primary">
		<a href={localizeHref('/')} class:on={isActive('/')} aria-current={isActive('/') ? 'page' : undefined}>
			<span>{m.nav_inici()}</span>
		</a>
		<a href={localizeHref('/resum')} class:on={isActive('/resum')} aria-current={isActive('/resum') ? 'page' : undefined}>
			<span>{m.nav_resum()}</span>
		</a>
		<a href={localizeHref('/mapa')} class:on={isActive('/mapa')} aria-current={isActive('/mapa') ? 'page' : undefined}>
			<span>{m.nav_mapa()}</span>
		</a>
		<!-- Licitacions FORA de la nav principal (decisió Bea): «en construcció», només al peu.
		     Metodologia i Glossari tampoc van a la capçalera: viuen al peu (secció Explora). -->
		<a href={localizeHref('/pregunta-li')} class:on={isActive('/pregunta-li')} aria-current={isActive('/pregunta-li') ? 'page' : undefined}>
			<span>{m.nav_preguntale()}</span>
		</a>
		<span class="nav-inert" aria-disabled="true">{m.nav_index()}</span>
		<span class="nav-inert" aria-disabled="true">{m.nav_daytripper()}</span>
		<span class="nav-inert" aria-disabled="true">{m.nav_politica()}</span>
	</nav>
	<div class="ds-top__right">
		<LangSwitcher />
		<ThemeSwitcher />
	</div>
	<button
		class="ds-burger"
		aria-label={m.nav_menu()}
		aria-expanded={menuOpen}
		aria-controls="ds-drawer"
		onclick={() => (menuOpen = !menuOpen)}
	>
		{#if menuOpen}
			<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
		{:else}
			<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" /></svg>
		{/if}
	</button>
	{#if menuOpen}
		<div id="ds-drawer" class="ds-drawer">
			<a href={localizeHref('/')} class:on={isActive('/')} onclick={() => (menuOpen = false)}>{m.nav_inici()}</a>
			<a href={localizeHref('/resum')} class:on={isActive('/resum')} onclick={() => (menuOpen = false)}>{m.nav_resum()}</a>
			<a href={localizeHref('/mapa')} class:on={isActive('/mapa')} onclick={() => (menuOpen = false)}>{m.nav_mapa()}</a>			<a href={localizeHref('/pregunta-li')} class:on={isActive('/pregunta-li')} onclick={() => (menuOpen = false)}>{m.nav_preguntale()}</a>
			<a href={localizeHref('/metodologia')} class:on={isActive('/metodologia')} onclick={() => (menuOpen = false)}>{m.foot_link_method_to()}</a>
			<a href={localizeHref('/glossari')} class:on={isActive('/glossari')} onclick={() => (menuOpen = false)}>{m.foot_link_glossary()}</a>
			<div class="ds-drawer__ctl"><LangSwitcher /><ThemeSwitcher /></div>
		</div>
	{/if}
</header>

<main id="main" tabindex="-1">
	{@render children?.()}
</main>

<!-- ============================ PEU ============================ -->
<footer class="ap-foot">
	<ContourField
		class="ap-foot__field"
		viewBox="0 0 1200 300"
		summits={footSummits}
		divis={footDivis}
		labels={footLabels}
	/>
	<div class="ap-foot__in">
		<div>
			<div class="ap-foot__brand">
				<img src="{base}/brand/riusdegent-mark.svg" width="30" height="30" alt="" />
				<span class="wm">rius<b>degent</b></span>
			</div>
			<p class="ap-foot__mission">{m.foot_mission()}</p>
			<span class="ap-foot__pledge"><span class="spot"></span><span>{m.foot_pledge()}</span></span>
		</div>
		<div>
			<h4>{m.foot_explore()}</h4>
			<ul>
				<li><a href={localizeHref('/resum')}>{m.nav_resum()}</a></li>
				<li><a href={localizeHref('/mapa')}>{m.nav_mapa()}</a></li>
				<li><a href={localizeHref('/licitacions')}>{m.nav_licitacions()}</a></li>
				<li><a href={localizeHref('/metodologia')}>{m.foot_link_method_to()}</a></li>
				<li><a href={localizeHref('/glossari')}>{m.foot_link_glossary()}</a></li>
			</ul>
		</div>
		<div>
			<h4>{m.foot_about()}</h4>
			<ul>
				<li><span class="foot-inert" aria-disabled="true">{m.foot_about_who()}</span></li>
				<li><span class="foot-inert" aria-disabled="true">{m.foot_about_politica()}</span></li>
				<li><span class="foot-inert" aria-disabled="true">{m.foot_link_contract()}</span></li>
				<li><a href={localizeHref('/pregunta-li')}>{m.foot_about_ask()}</a></li>
			</ul>
		</div>
		<div class="ap-foot__ctl">
			<div>
				<h4>{m.foot_lang()}</h4>
				<LangSwitcher />
			</div>
			<div>
				<h4>{m.foot_theme()}</h4>
				<ThemeSwitcher />
			</div>
		</div>
	</div>
	<div class="ap-foot__bottom">
		<span>{m.foot_legal()} · <a href="https://zigiella.com/legal/">{m.foot_legal_notice()}</a> · <a href="https://zigiella.com/privacidad/">{m.foot_privacy()}</a></span>
		<span class="coord"><span>42°17′N · 2°01′E</span><span>{m.foot_update()}</span></span>
	</div>
</footer>

<style>
	/* L'estructura i la pell vénen del design-system (.ds-top, .ap-foot, .ds-nav…).
	   Aquí només forcem que <main> ocupi l'alçada disponible perquè el peu quedi avall. */
	main {
		display: block;
		outline: none;
		min-height: 60vh;
	}

	/* Ítems de nav inerts (pàgines no construïdes en aquesta fase): es renderitzen com a
	   <span> (no són enllaços navegables → sense href), però amb el mateix encaix visual
	   que .ds-nav a, atenuats. */
	.nav-inert {
		font-size: 0.9rem;
		font-weight: 500;
		color: var(--dp-text-muted);
		padding: 8px 13px;
		border-radius: var(--dp-radius-sm);
		line-height: 1;
		opacity: 0.5;
		cursor: not-allowed;
		user-select: none;
	}

	/* Enllaços inerts del peu: <span> atenuat amb la mateixa pell que .ap-foot ul a. */
	.foot-inert {
		font-size: 0.86rem;
		color: var(--dp-text-muted);
		opacity: 0.55;
		cursor: not-allowed;
		user-select: none;
	}

	/* ——— Navegació MÒBIL: hamburger + drawer (≤760px). A escriptori, ocult. ——— */
	.ds-burger {
		display: none;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border: 1px solid var(--dp-border);
		border-radius: var(--dp-radius-sm);
		background: transparent;
		color: var(--dp-text);
		cursor: pointer;
	}
	.ds-burger:hover {
		background: var(--dp-accent-weak);
	}
	.ds-drawer {
		display: none;
	}
	@media (max-width: 760px) {
		.ds-nav {
			display: none;
		}
		.ds-top__right {
			display: none;
		}
		.ds-burger {
			display: inline-flex;
			margin-left: auto;
		}
		.ds-drawer {
			display: flex;
			flex-direction: column;
			gap: 2px;
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			background: var(--dp-bg);
			border-bottom: 1px solid var(--dp-border);
			padding: 8px 16px 16px;
			box-shadow: 0 10px 24px rgb(0 0 0 / 12%);
			z-index: 50;
		}
		.ds-drawer a {
			padding: 11px 8px;
			border-radius: var(--dp-radius-sm);
			color: var(--dp-text-muted);
			text-decoration: none;
			font-weight: 500;
		}
		.ds-drawer a.on {
			color: var(--dp-forest);
			background: var(--dp-accent-weak);
			font-weight: 700;
		}
		.ds-drawer__ctl {
			display: flex;
			gap: 14px;
			margin-top: 8px;
			padding-top: 12px;
			border-top: 1px solid var(--dp-border);
		}
	}
</style>
