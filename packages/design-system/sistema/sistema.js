/* riusdegent · sistema — comportament compartit */
(function(){
  'use strict';

  /* ---- tema clar/fosc persistent ---- */
  var KEY = 'rdg-theme';
  function applyTheme(t){
    document.documentElement.setAttribute('data-theme', t);
    document.querySelectorAll('.themer button').forEach(function(b){
      b.classList.toggle('on', b.dataset.theme === t);
    });
    try{ localStorage.setItem(KEY, t); }catch(e){}
  }
  var saved;
  try{ saved = localStorage.getItem(KEY); }catch(e){}
  applyTheme(saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  document.addEventListener('click', function(e){
    var b = e.target.closest('.themer button'); if(!b) return;
    applyTheme(b.dataset.theme);
  });

  /* ---- corbes de nivell (full topogràfic) en qualsevol svg .ds-hero__field o [data-contours] ---- */
  function ring(cx,cy,r,squash,seed){
    var P=46, s='';
    for(var a=0;a<=P;a++){
      var ang=a/P*Math.PI*2;
      var n=1 + 0.10*Math.sin(seed+ang*3) + 0.06*Math.cos(seed*1.7+ang*5);
      var x=cx+Math.cos(ang)*r*n, y=cy+Math.sin(ang)*r*squash*n;
      s+=(a?'L':'M')+x.toFixed(1)+' '+y.toFixed(1);
    }
    return s+'Z';
  }
  function drawContours(svg){
    var cs = getComputedStyle(document.documentElement);
    var c  = cs.getPropertyValue('--contour').trim()   || '#C2C7BC';
    var ci = cs.getPropertyValue('--contour-i').trim() || '#9aa093';
    var summits=[{cx:250,cy:250,sq:0.92,seed:0.6},{cx:760,cy:300,sq:1.04,seed:2.3}], out='';
    summits.forEach(function(su){
      for(var i=1;i<=11;i++){
        var r=18+i*23, idx=(i%4===0);
        out+='<path d="'+ring(su.cx,su.cy,r,su.sq,su.seed+i*0.3)+'" fill="none" stroke="'+(idx?ci:c)
            +'" stroke-width="'+(idx?1.4:0.9)+'" vector-effect="non-scaling-stroke" opacity="0.7"/>';
      }
    });
    // corba índex divisòria (terracota puntejada)
    out+='<path d="'+ring(505,275,150,1.25,1.4)+'" fill="none" stroke="#C75D34" stroke-width="1.6" '
       +'vector-effect="non-scaling-stroke" stroke-dasharray="0.1 7" stroke-linecap="round" opacity="0.8"/>';
    svg.innerHTML = out;
  }
  function redrawAll(){
    document.querySelectorAll('.ds-hero__field,[data-contours]').forEach(drawContours);
  }
  redrawAll();
  // redibuixa en canviar de tema (els colors de corba canvien)
  new MutationObserver(redrawAll).observe(document.documentElement, {attributes:true, attributeFilter:['data-theme']});

  /* ---- tabs / segmented (delegació) ---- */
  document.addEventListener('click', function(e){
    var t = e.target.closest('.tabs button, .seg button:not(.themer button)');
    if(!t || t.closest('.themer')) return;
    var group = t.parentElement;
    group.querySelectorAll('button').forEach(function(b){ b.classList.toggle('on', b===t); });
  });

  /* ---- ordena taula demo (per la columna numèrica) ---- */
  document.addEventListener('click', function(e){
    var th = e.target.closest('table.tbl thead th[data-sort]'); if(!th) return;
    var table = th.closest('table'), tb = table.tBodies[0];
    var idx = Array.prototype.indexOf.call(th.parentElement.children, th);
    var dir = th.dataset.dir === 'asc' ? 'desc' : 'asc'; th.dataset.dir = dir;
    var rows = Array.prototype.slice.call(tb.rows);
    rows.sort(function(a,b){
      var x=parseFloat(a.cells[idx].dataset.v||a.cells[idx].textContent.replace(',','.'));
      var y=parseFloat(b.cells[idx].dataset.v||b.cells[idx].textContent.replace(',','.'));
      return dir==='asc' ? x-y : y-x;
    });
    rows.forEach(function(r){ tb.appendChild(r); });
    table.querySelectorAll('th[data-sort] .ar').forEach(function(a){ a.textContent=''; });
    var ar = th.querySelector('.ar'); if(ar) ar.textContent = dir==='asc' ? ' ↑' : ' ↓';
  });
})();
