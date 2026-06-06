/* ============================================================================
   riusdegent · APLICACIÓ REAL — comportament de pàgina
   1 · corbes de nivell ETIQUETADES amb dades (guinyo a «dades i números»)
   2 · i18n CA/ES (commutador d'idioma persistent)
   3 · navegació entre vistes (Resum / Mapa)
   4 · mapa coroplètic: selector d'indicador (rampa + llegenda) + fitxa
   El tema (clar/fosc) el porta ../sistema/sistema.js.
   ============================================================================ */
(function(){
  'use strict';
  var root = document.documentElement;

  /* ========================================================================
     1 · CORBES DE NIVELL AMB ETIQUETES DE DADA
     Full topogràfic on les corbes índex porten una xifra real de la pàgina,
     escrita com una cota (la línia es trenca per deixar passar el número).
     ===================================================================== */
  function ringPts(cx,cy,r,sq,seed){
    var P=54, pts=[];
    for(var a=0;a<=P;a++){
      var ang=a/P*Math.PI*2;
      var n=1 + 0.10*Math.sin(seed+ang*3) + 0.055*Math.cos(seed*1.7+ang*5);
      pts.push([cx+Math.cos(ang)*r*n, cy+Math.sin(ang)*r*sq*n]);
    }
    return pts;
  }
  function path(pts){ var s=''; for(var i=0;i<pts.length;i++){ s+=(i?'L':'M')+pts[i][0].toFixed(1)+' '+pts[i][1].toFixed(1); } return s+'Z'; }

  function drawField(svg){
    if(!svg) return;
    var dark = root.getAttribute('data-theme')==='dark';
    var cs   = getComputedStyle(root);
    var c    = (cs.getPropertyValue('--contour')||'').trim()   || '#C2C7BC';
    var ci   = (cs.getPropertyValue('--contour-i')||'').trim() || '#9aa093';
    var lcol = dark ? '#C79A63' : '#A07A4C';           /* etiqueta de dada · ocre apagat */
    var plate= svg.getAttribute('data-plate')==='map'
                 ? (dark ? '#0C1014' : '#F2F1EC')
                 : (cs.getPropertyValue('--paper')||'#F2F1EC').trim();
    var labels = (svg.getAttribute('data-labels')||'').split('|').filter(Boolean);
    var summits = JSON.parse(svg.getAttribute('data-summits') || '[]');
    var li = 0, out = '';

    summits.forEach(function(su){
      for(var i=1;i<=su.rings;i++){
        var r = su.r0 + i*su.step, idx = (i % 3 === 0);
        var pts = ringPts(su.cx, su.cy, r, su.sq, su.seed + i*0.3);
        out += '<path d="'+path(pts)+'" fill="none" stroke="'+(idx?ci:c)+'" stroke-width="'+(idx?1.5:0.9)
             + '" vector-effect="non-scaling-stroke" opacity="'+(idx?0.95:0.7)+'"/>';
        /* etiqueta de dada sobre la corba índex */
        if(idx && li < labels.length && i >= 3){
          var t  = Math.floor(pts.length*su.lt) % pts.length;
          var p  = pts[t], q = pts[(t+2)%pts.length];
          var ang= Math.atan2(q[1]-p[1], q[0]-p[0]) * 180/Math.PI;
          if(ang>90) ang-=180; if(ang<-90) ang+=180;
          var txt= labels[li++], w = txt.length*6.3 + 6;
          out += '<g transform="translate('+p[0].toFixed(1)+' '+p[1].toFixed(1)+') rotate('+ang.toFixed(1)+')">'
               +   '<rect x="'+(-w/2)+'" y="-7.5" width="'+w+'" height="15" fill="'+plate+'"/>'
               +   '<text x="0" y="3.4" text-anchor="middle" font-family="IBM Plex Mono, monospace" '
               +     'font-size="11" font-weight="500" fill="'+lcol+'">'+txt+'</text>'
               + '</g>';
        }
      }
    });
    /* divisòria · corba índex terracota puntejada (motiu de marca) */
    var dv = JSON.parse(svg.getAttribute('data-divis') || 'null');
    if(dv){
      out += '<path d="'+path(ringPts(dv.cx,dv.cy,dv.r,dv.sq,dv.seed))+'" fill="none" stroke="#C75D34" '
           + 'stroke-width="1.7" vector-effect="non-scaling-stroke" stroke-dasharray="0.1 7" stroke-linecap="round" opacity="0.85"/>';
    }
    svg.innerHTML = out;
  }
  function drawAllFields(){ document.querySelectorAll('[data-field]').forEach(drawField); }
  drawAllFields();
  new MutationObserver(drawAllFields).observe(root, {attributes:true, attributeFilter:['data-theme']});

  /* ========================================================================
     2 · i18n CA / ES
     ===================================================================== */
  var I18N = {
    ca:{
      'brand.sub':'Dades per entendre com s’habita el territori',
      'nav.resum':'Resum','nav.mapa':'Mapa','nav.index':'Índex IETR',
      'nav.day':'Excursionista de dia','nav.pol':'Política','nav.ask':'Pregunta-li',
      /* Resum */
      'r.eye':'Observatori del territori','r.eye2':'Berguedà · 31 municipis',
      'r.h1a':'Resum','r.h1b':'comarcal',
      'r.lede':"Indicadors clau del Berguedà (31 municipis) i la comparativa entre els <b class=\"warm\">dos extrems</b> de la pressió turística-residencial: Castellar de n'Hug i Berga.",
      'r.kpiTitle':'Indicadors comarcals',
      'kpi.pop':'Població','kpi.est':'Establiments turístics','kpi.ratio':'Establiments / 1000 hab',
      'kpi.nop':'% habitatge no principal','kpi.res':'Residus kg/hab/any',
      'kpi.pop.src':'Idescat — El municipi en xifres (EMEX) / Cens 2021 · 2025',
      'kpi.est.src':'Generalitat — Registre de Turisme de Catalunya · 2026',
      'kpi.ratio.src':'datapoble (calculat) — indicadors derivats / IETR',
      'kpi.nop.src':'datapoble (calculat) · Idescat · 2021',
      'kpi.res.src':'Agència de Residus de Catalunya (ARC) · 2024',
      'r.extTitle':'Dos extrems del Berguedà',
      'r.extLede':"Castellar de n'Hug (166 hab.) i Berga (17.539 hab.) marquen els dos pols de la pressió turística-residencial. El mateix riu que creix en un vessant s'asseca a l'altre.",
      'axis.lo':'IETR 0 · menys exposició','axis.hi':'100 · més exposició',
      'ex.rank1':'Rànquing IETR','ex.of':'de 31',
      'i.ietr':"Índex d'Exposició T-R",'i.pop':'Població','i.hab':'Habitatges (total)',
      'i.nop':'Habitatges no principals','i.pnop':'% habitatge no principal','i.hph':'Habitatges per habitant',
      'i.est':'Establiments turístics','i.hut':"HUT (habitatges d'ús turístic)",'i.ratio':'Establiments / 1000 hab',
      'i.res':'Residus kg/hab/any','i.vot':'% vot independentista',
      'cav.1':'És exposició estructural (stock), no pressió realitzada. Robust a normalització (Spearman > 0,97) i a pesos.',
      'cav.2':'Lectura ECOLÒGICA (no individual; falàcia ecològica). Volàtil en micromunicipis (N petit).',
      'r.src':'Cap xifra sense procedència. Lectura a escala comarcal. Dades reals dels 31 municipis del Berguedà, amb la forma del contracte semàntic (font: marts de riusdegent).',
      /* Mapa */
      'm.eye':'Cartografia','m.eye2':'31 municipis · geometria INE/IGN',
      'm.h1a':'Mapa','m.h1b':'coroplètic',
      'm.lede':"Per defecte, la <b class=\"warm\">bretxa</b> entre població real estimada i padró: <b class=\"warm\">càlid</b> = població que el padró no veu; <b class=\"cool\">teal</b> = menys gent que el registre. El color comunica el mètode; els municipis amb estimació feble o sense dada porten trama.",
      'm.indicator':'Indicador',
      'ind.gap':'Gap població (%)','ind.real':'Població real estimada','ind.ietr':"Índex d'Exposició T-R (IETR)",
      'ind.nop':'% habitatge no principal','ind.ratio':'Establiments / 1000 hab','ind.res':'Residus kg/hab/any',
      'm.legTitle':'Gap població (%)','m.legSub':'estimació · divergent (centrat en 0) · 5 classes',
      'm.legSeqSub':'seqüencial · Jenks · 5 classes',
      'm.lc':'confiança baixa (estimació feble: tramada)','m.nd':'sense dada / secret estadístic',
      'm.near':'≈ mitjana comarcal (neutre)',
      'm.liveT':'Mapa coroplètic en viu','m.liveS':'MapLibre · geometria oficial INE/IGN','m.liveS2':'Aquí es renderitza el mapa real de riusdegent.cat/mapa. El selector d\u2019indicador hi aplica la paleta especificada a sota.',
      'm.read.gap':'<b>Porpra</b> = població que el padró no veu (inferència). <b>Teal</b> = menys gent que el registre. El to neutre marca \u2248 la mitjana comarcal.',
      'm.read.seq':'Escala de terra ordenada: <b>clar</b> = valor baix, <b>fosc</b> = valor alt. La magnitud creix amb la intensitat del to.',
      'ps.title':'Paletes per visualització','m.readH':'Com es llegeix el color','ps.lede':'Cada tipus de dada té la seva paleta. El color comunica el mètode: mai es barreja magnitud amb desviació. La que utilitza l\u2019indicador actiu queda destacada.',
      'ps.div.t':'Divergent · «gap» (desviació)','ps.div.use':'Valors amb un centre significatiu (0 = mitjana): gap de població, saldo, desviació vs comarca.','ps.div.cvd':'teal \u2194 porpra · CVD-safe (no toca el vermell-verd) · porpra = inferència',
      'ps.seq.t':'Seqüencial · «terra» (magnitud)','ps.seq.use':'Magnituds ordenades de baix a alt: IETR, % habitatge no principal, establiments/1000, residus.','ps.seq.cvd':'família terra (YlOrBr) · lluminositat estrictament creixent · CVD-safe',
      'ps.cat.t':'Qualitativa · Okabe-Ito','ps.cat.use':'Categories sense ordre intrínsec. Mai per a color polític partidista sense acord.','ps.cat.cvd':'8 tons dissenyats per a daltonisme',
      'ps.map.t':'Quin indicador fa servir quina paleta','ps.pdiv':'divergent','ps.pseq':'seqüencial','ps.active':'actiu',
      'ps.note':'Sense dada \u2192 tramat gris (mai farciment pla). Confiança baixa \u2192 es manté el color de la rampa, velat amb un puntejat (el «llit sec» de la marca).',
      'pk.measured':'dada oficial directa','pk.derived':'inferència / índex (datapoble)','pk.nd':'sense dada / secret',
      'd.sel':'Seleccionat','d.gap':'Gap de població','d.ietr':'IETR','d.read.pos':'població que el padró <b>no veu</b>','d.read.neg':'<b>menys</b> gent que el registre',
      'd.click':'Clica un municipi al mapa per veure\u2019n la fitxa.',
      'mcav.1':'Estimació, no cens: presència real inferida dels residus (ARC) vs padró. Positiu = població que el padró no veu. La xifra exacta depèn de la base i es llegeix com un rang.',
      'mcav.2':'Els talls poden canviar si entren més municipis (escala Catalunya). Geometria oficial (INE/IGN). Cada xifra porta font i data.',
      'm.src':'Font: datapoble (calculat) — indicadors derivats i índex IETR · Agència de Residus de Catalunya (ARC) · 2024/2025. Cap xifra sense procedència.',
      /* peu */
      'f.mission':'Cada municipi té una xifra; cada xifra té una font. Un observatori del territori que separa el que es mesura del que s\u2019infereix.',
      'f.pledge':'Cap xifra sense procedència',
      'f.explore':'Explora','f.about':'El projecte','f.sources':'Fonts',
      'fl.method':'Metodologia IETR','fl.contract':'Contracte semàntic','fl.opendata':'Codi i dades obertes','fl.glossary':'Glossari',
      'fa.who':'Qui hi ha al darrere','fa.politica':'Política de dades','fa.contact':'Contacte','fa.ask':'Pregunta-li a les dades',
      'f.theme':'Tema','f.lang':'Idioma',
      'f.legal':'riusdegent · dades per entendre com s’habita el territori · dades obertes',
      'f.update':'Darrera actualització · juny 2026'
    },
    es:{
      'brand.sub':'Datos para entender cómo se habita el territorio',
      'nav.resum':'Resumen','nav.mapa':'Mapa','nav.index':'Índice IETR',
      'nav.day':'Excursionista de día','nav.pol':'Política','nav.ask':'Pregúntale',
      'r.eye':'Observatorio del territorio','r.eye2':'Berguedà · 31 municipios',
      'r.h1a':'Resumen','r.h1b':'comarcal',
      'r.lede':"Indicadores clave del Berguedà (31 municipios) y la comparativa entre los <b class=\"warm\">dos extremos</b> de la presión turístico-residencial: Castellar de n'Hug y Berga.",
      'r.kpiTitle':'Indicadores comarcales',
      'kpi.pop':'Población','kpi.est':'Establecimientos turísticos','kpi.ratio':'Establecimientos / 1000 hab',
      'kpi.nop':'% vivienda no principal','kpi.res':'Residuos kg/hab/año',
      'kpi.pop.src':'Idescat — El municipio en cifras (EMEX) / Censo 2021 · 2025',
      'kpi.est.src':'Generalitat — Registro de Turismo de Cataluña · 2026',
      'kpi.ratio.src':'datapoble (calculado) — indicadores derivados / IETR',
      'kpi.nop.src':'datapoble (calculado) · Idescat · 2021',
      'kpi.res.src':'Agencia de Residuos de Cataluña (ARC) · 2024',
      'r.extTitle':'Dos extremos del Berguedà',
      'r.extLede':"Castellar de n'Hug (166 hab.) y Berga (17.539 hab.) marcan los dos polos de la presión turístico-residencial. El mismo río que crece en una vertiente se seca en la otra.",
      'axis.lo':'IETR 0 · menos exposición','axis.hi':'100 · más exposición',
      'ex.rank1':'Ranking IETR','ex.of':'de 31',
      'i.ietr':'Índice de Exposición T-R','i.pop':'Población','i.hab':'Viviendas (total)',
      'i.nop':'Viviendas no principales','i.pnop':'% vivienda no principal','i.hph':'Viviendas por habitante',
      'i.est':'Establecimientos turísticos','i.hut':'VUT (viviendas de uso turístico)','i.ratio':'Establecimientos / 1000 hab',
      'i.res':'Residuos kg/hab/año','i.vot':'% voto independentista',
      'cav.1':'Es exposición estructural (stock), no presión realizada. Robusto a normalización (Spearman > 0,97) y a pesos.',
      'cav.2':'Lectura ECOLÓGICA (no individual; falacia ecológica). Volátil en micromunicipios (N pequeño).',
      'r.src':'Ninguna cifra sin procedencia. Lectura a escala comarcal. Datos reales de los 31 municipios del Berguedà, con la forma del contrato semántico (fuente: marts de riusdegent).',
      'm.eye':'Cartografía','m.eye2':'31 municipios · geometría INE/IGN',
      'm.h1a':'Mapa','m.h1b':'coroplético',
      'm.lede':"Por defecto, la <b class=\"warm\">brecha</b> entre población real estimada y padrón: <b class=\"warm\">cálido</b> = población que el padrón no ve; <b class=\"cool\">teal</b> = menos gente que el registro. El color comunica el método; los municipios con estimación débil o sin dato llevan trama.",
      'm.indicator':'Indicador',
      'ind.gap':'Gap población (%)','ind.real':'Población real estimada','ind.ietr':'Índice de Exposición T-R (IETR)',
      'ind.nop':'% vivienda no principal','ind.ratio':'Establecimientos / 1000 hab','ind.res':'Residuos kg/hab/año',
      'm.legTitle':'Gap población (%)','m.legSub':'estimación · divergente (centrado en 0) · 5 clases',
      'm.legSeqSub':'secuencial · Jenks · 5 clases',
      'm.lc':'confianza baja (estimación débil: tramada)','m.nd':'sin dato / secreto estadístico',
      'm.near':'≈ media comarcal (neutro)',
      'm.liveT':'Mapa coroplético en vivo','m.liveS':'MapLibre · geometría oficial INE/IGN','m.liveS2':'Aquí se renderiza el mapa real de riusdegent.cat/mapa. El selector de indicador le aplica la paleta especificada debajo.',
      'm.read.gap':'<b>Púrpura</b> = población que el padrón no ve (inferencia). <b>Teal</b> = menos gente que el registro. El tono neutro marca \u2248 la media comarcal.',
      'm.read.seq':'Escala de tierra ordenada: <b>claro</b> = valor bajo, <b>oscuro</b> = valor alto. La magnitud crece con la intensidad del tono.',
      'ps.title':'Paletas por visualización','m.readH':'Cómo se lee el color','ps.lede':'Cada tipo de dato tiene su paleta. El color comunica el método: nunca se mezcla magnitud con desviación. La del indicador activo queda destacada.',
      'ps.div.t':'Divergente · «gap» (desviación)','ps.div.use':'Valores con un centro significativo (0 = media): gap de población, saldo, desviación vs comarca.','ps.div.cvd':'teal \u2194 púrpura · CVD-safe (no toca el rojo-verde) · púrpura = inferencia',
      'ps.seq.t':'Secuencial · «tierra» (magnitud)','ps.seq.use':'Magnitudes ordenadas de bajo a alto: IETR, % vivienda no principal, establecimientos/1000, residuos.','ps.seq.cvd':'familia tierra (YlOrBr) · luminosidad estrictamente creciente · CVD-safe',
      'ps.cat.t':'Cualitativa · Okabe-Ito','ps.cat.use':'Categorías sin orden intrínseco. Nunca para color político partidista sin acuerdo.','ps.cat.cvd':'8 tonos diseñados para daltonismo',
      'ps.map.t':'Qué indicador usa qué paleta','ps.pdiv':'divergente','ps.pseq':'secuencial','ps.active':'activo',
      'ps.note':'Sin dato \u2192 trama gris (nunca relleno plano). Confianza baja \u2192 se mantiene el color de la rampa, velado con un punteado (el «lecho seco» de la marca).',
      'pk.measured':'dato oficial directo','pk.derived':'inferencia / índice (datapoble)','pk.nd':'sin dato / secreto',
      'd.sel':'Seleccionado','d.gap':'Gap de población','d.ietr':'IETR','d.read.pos':'población que el padrón <b>no ve</b>','d.read.neg':'<b>menos</b> gente que el registro',
      'd.click':'Haz clic en un municipio del mapa para ver su ficha.',
      'mcav.1':'Estimación, no censo: presencia real inferida de los residuos (ARC) vs padrón. Positivo = población que el padrón no ve. La cifra exacta depende de la base y se lee como rango.',
      'mcav.2':'Los cortes pueden cambiar si entran más municipios (escala Cataluña). Geometría oficial (INE/IGN). Cada cifra lleva fuente y fecha.',
      'm.src':'Fuente: datapoble (calculado) — indicadores derivados e índice IETR · Agencia de Residuos de Cataluña (ARC) · 2024/2025. Ninguna cifra sin procedencia.',
      'f.mission':'Cada municipio tiene una cifra; cada cifra tiene una fuente. Un observatorio del territorio que separa lo que se mide de lo que se infiere.',
      'f.pledge':'Ninguna cifra sin procedencia',
      'f.explore':'Explora','f.about':'El proyecto','f.sources':'Fuentes',
      'fl.method':'Metodología IETR','fl.contract':'Contrato semántico','fl.opendata':'Código y datos abiertos','fl.glossary':'Glosario',
      'fa.who':'Quién está detrás','fa.politica':'Política de datos','fa.contact':'Contacto','fa.ask':'Pregúntale a los datos',
      'f.theme':'Tema','f.lang':'Idioma',
      'f.legal':'riusdegent · datos para entender cómo se habita el territorio · datos abiertos',
      'f.update':'Última actualización · junio 2026'
    }
  };

  function applyLang(lang){
    var d = I18N[lang] || I18N.ca;
    root.setAttribute('data-lang', lang);
    root.setAttribute('lang', lang==='es' ? 'es' : 'ca');
    document.querySelectorAll('[data-i18n]').forEach(function(el){
      var k = el.getAttribute('data-i18n'); if(d[k]!=null) el.textContent = d[k];
    });
    document.querySelectorAll('[data-i18n-html]').forEach(function(el){
      var k = el.getAttribute('data-i18n-html'); if(d[k]!=null) el.innerHTML = d[k];
    });
    document.querySelectorAll('.langer button').forEach(function(b){ b.classList.toggle('on', b.dataset.lang===lang); });
    try{ localStorage.setItem('rdg-lang', lang); }catch(e){}
    renderDossier();
    if(typeof paint==='function') paint();
  }
  var savedLang; try{ savedLang = localStorage.getItem('rdg-lang'); }catch(e){}
  document.addEventListener('click', function(e){
    var b = e.target.closest('.langer button'); if(!b) return;
    applyLang(b.dataset.lang);
  });

  /* ========================================================================
     3 · NAVEGACIÓ ENTRE VISTES
     ===================================================================== */
  function showView(v){
    document.querySelectorAll('[data-view]').forEach(function(s){ s.classList.toggle('on', s.dataset.view===v); });
    document.querySelectorAll('.ds-nav a[data-go]').forEach(function(a){ a.classList.toggle('on', a.dataset.go===v); });
    window.scrollTo(0,0);
    drawAllFields();
  }
  document.addEventListener('click', function(e){
    var a = e.target.closest('[data-go]'); if(!a) return;
    e.preventDefault(); showView(a.dataset.go);
  });

  /* ========================================================================
     4 · MAPA COROPLÈTIC
     ===================================================================== */
  var DIV = ['--dp-div2-0','--dp-div2-1','--dp-div2-2','--dp-div2-3','--dp-div2-4','--dp-div2-5','--dp-div2-6'];
  var EXP = ['--dp-exposure-0','--dp-exposure-1','--dp-exposure-2','--dp-exposure-3','--dp-exposure-4','--dp-exposure-5'];
  /* gi = índex rampa divergent (0-6) · si = índex seqüencial (0-5) · gap = % bretxa */
  var M = [
    {n:'Berga',ine:'08022',gap:-2,gi:2,si:1},{n:'Avià',ine:'08009',gap:8,gi:3,si:2},{n:'Olvan',ine:'08145',gap:14,gi:3,si:2},{n:'Gironella',ine:'08092',gap:4,gi:3,si:1},{n:'Casserres',ine:'08047',gap:46,gi:4,si:3},{n:'Puig-reig',ine:'08175',gap:-6,gi:2,si:1},{n:'Montmajor',ine:'08130',gap:52,gi:4,si:3},
    {n:'Cercs',ine:'08066',gap:18,gi:3,si:2},{n:'Vilada',ine:'08294',gap:58,gi:4,si:3},{n:'Borredà',ine:'08024',gap:74,gi:5,si:4},{n:'la Quar',ine:'08172',gap:96,gi:5,si:3,lc:true},{n:'Sagàs',ine:'08185',gap:22,gi:3,si:2},{n:"l'Espunyola",ine:'08077',gap:50,gi:4,si:3},{n:'Capolat',ine:'08038',gap:118,gi:5,si:4,lc:true},
    {n:'Vallcebre',ine:'08293',gap:88,gi:5,si:4},{n:'Fígols',ine:'08081',gap:62,gi:4,si:3,lc:true},{n:'Saldes',ine:'08187',gap:112,gi:5,si:4},{n:'Gósol',ine:'08099',gap:142,gi:6,si:4},{n:"Castellar de n'Hug",ine:'08052',gap:176,gi:6,si:5,lc:true,sel:true},{n:'la Pobla de Lillet',ine:'08168',gap:84,gi:5,si:3},{n:'Guardiola de B.',ine:'08100',gap:54,gi:4,si:3},
    {n:'Bagà',ine:'08013',gap:24,gi:3,si:2},{n:'Gisclareny',ine:'08093',gap:0,gi:3,si:0,nd:true},{n:'Sant Julià de C.',ine:'08218',gap:20,gi:3,si:2},{n:'Sant Jaume de F.',ine:'08207',gap:40,gi:4,si:3},{n:'la Nou de B.',ine:'08143',gap:80,gi:5,si:3},{n:"Castell de l'Areny",ine:'08051',gap:104,gi:5,si:4,lc:true},{n:'Vilada de Dalt',ine:'08294',gap:48,gi:4,si:3}
  ];
  var IND_DIV = 'gap';
  var choro = document.getElementById('choro');
  var indicator = 'gap';
  var selIdx = M.findIndex(function(d){ return d.sel; }); if(selIdx<0) selIdx=0;

  function paint(){
    var divMode = (indicator===IND_DIV);
    if(choro){
      choro.querySelectorAll('.cell').forEach(function(c){
        var d = M[+c.dataset.i];
        c.classList.remove('nodata','lowconf','sel'); c.style.background='';
        if(d.nd){ c.classList.add('nodata'); return; }
        c.style.background = 'var(' + (divMode ? DIV[d.gi] : EXP[d.si]) + ')';
        if(d.lc) c.classList.add('lowconf');
        if(+c.dataset.i===selIdx) c.classList.add('sel');
      });
    }
    /* llegenda: divergent vs seqüencial */
    document.querySelectorAll('[data-leg]').forEach(function(el){
      el.style.display = el.dataset.leg===(divMode?'div':'seq') ? '' : 'none';
    });
    var st = document.getElementById('legSeqTitle'), sel = document.getElementById('indicator');
    if(st && sel){ st.textContent = sel.options[sel.selectedIndex].textContent; }
    /* nota «com es llegeix el color» */
    var note = document.getElementById('readnote');
    if(note){ var d = I18N[root.getAttribute('data-lang')||'ca']; note.innerHTML = divMode ? d['m.read.gap'] : d['m.read.seq']; }
    /* paleta activa destacada a l'especificació */
    document.querySelectorAll('[data-pal]').forEach(function(el){ el.classList.toggle('on', el.dataset.pal===(divMode?'div':'seq')); });
  }
  function fmtGap(g){ return (g>0?'+':(g<0?'\u2212':'')) + Math.abs(g) + ' %'; }
  function renderDossier(){
    var host = document.getElementById('dossier'); if(!host) return;
    var lang = root.getAttribute('data-lang')||'ca'; var d = I18N[lang];
    var m = M[selIdx];
    var posneg = m.gap>=0 ? d['d.read.pos'] : d['d.read.neg'];
    host.innerHTML =
      '<div class="map-dossier__hd"><div>'
      + '<h3>'+m.n+'</h3>'
      + '<p class="comarca">BERGUEDÀ · INE '+m.ine+(m.lc?' · '+d['m.lc'].split('(')[0].trim():'')+'</p>'
      + '</div></div>'
      + '<div class="big"><span class="v">'+fmtGap(m.gap)+'</span><span class="u">'+d['d.gap']+'</span></div>'
      + '<p class="read">'+(m.nd?d['m.nd']:posneg)+'.</p>';
  }
  // build cells
  if(choro){
    M.forEach(function(d,i){
      var c=document.createElement('div'); c.className='cell'; c.dataset.i=i;
      c.title=d.n;
      if(d.sel){ c.innerHTML='<span class="pin"><svg width="16" height="16" viewBox="0 0 96 96" aria-hidden="true"><line x1="48" y1="22" x2="48" y2="74" stroke-width="5" stroke-linecap="round"/></svg></span>'; }
      choro.appendChild(c);
    });
    paint();
    choro.addEventListener('click', function(e){
      var c=e.target.closest('.cell'); if(!c) return; var d=M[+c.dataset.i]; if(d.nd) return;
      selIdx=+c.dataset.i;
      choro.querySelectorAll('.cell .pin').forEach(function(p){ p.remove(); });
      c.innerHTML='<span class="pin"><svg width="16" height="16" viewBox="0 0 96 96" aria-hidden="true"><line x1="48" y1="22" x2="48" y2="74" stroke-width="5" stroke-linecap="round"/></svg></span>';
      paint(); renderDossier();
    });
  }
  // indicator selector
  var indSel = document.getElementById('indicator');
  if(indSel){ indSel.addEventListener('change', function(){ indicator=indSel.value; paint(); }); }

  /* ---- arrencada ---- */
  applyLang(savedLang || (root.getAttribute('lang')==='es' ? 'es' : 'ca'));
})();
