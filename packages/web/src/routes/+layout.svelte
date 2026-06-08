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
	import { localizeHref } from '$lib/i18n';
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { m } from '$lib/paraglide/messages';

	let { children } = $props();

	// Rutes canòniques (sense prefix de locale); reroute/localize fan la traducció.
	const path = $derived(page.url.pathname);
	function isActive(p: string): boolean {
		return path === p || path.startsWith(p + '/');
	}

	// Corbes del peu (cims + divisòria + etiquetes de dada real), com al target.
	const footSummits = [
		{ cx: 250, cy: 120, r0: 16, step: 24, rings: 8, sq: 0.95, seed: 0.6, lt: 0.02 },
		{ cx: 980, cy: 90, r0: 14, step: 22, rings: 8, sq: 1.05, seed: 2.3, lt: 0.04 }
	];
	const footDivis = { cx: 600, cy: 110, r: 150, sq: 1.0, seed: 1.4 };
	const footLabels = ['1.245 m', '42°16′N', '31', '1°53′E', '593'];
</script>

<a class="skip-link" href="#main">{m.skip_to_content()}</a>

<!-- ============================ CAPÇALERA ============================ -->
<header class="ds-top">
	<a class="ds-top__brand" href={localizeHref('/resum')} aria-label={m.app_name()}>
		<img src="{base}/brand/riusdegent-mark.svg" width="30" height="30" alt="" />
		<span class="txt">
			<span class="wm">rius<b>degent</b></span>
			<span class="sub">{m.brand_sub()}</span>
		</span>
	</a>
	<nav class="ds-nav" aria-label="Primary">
		<a href={localizeHref('/resum')} class:on={isActive('/resum')} aria-current={isActive('/resum') ? 'page' : undefined}>
			<span>{m.nav_resum()}</span>
		</a>
		<a href={localizeHref('/mapa')} class:on={isActive('/mapa')} aria-current={isActive('/mapa') ? 'page' : undefined}>
			<span>{m.nav_mapa()}</span>
		</a>
		<!-- Metodologia i Glossari NO van a la capçalera (decisió de Bea): viuen al peu (secció Explora). -->
		<a href={localizeHref('/preguntale')} class:on={isActive('/preguntale')} aria-current={isActive('/preguntale') ? 'page' : undefined}>
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
				<li><a href={localizeHref('/preguntale')}>{m.foot_about_ask()}</a></li>
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
		<span>{m.foot_legal()}</span>
		<span class="coord"><span>42°16′N · 1°53′E</span><span>{m.foot_update()}</span></span>
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
</style>
