(function(){
  const API_BASE = '/api';

  function num(x){
    if(!x) return 0;
    const t = String(x).replace(/[^0-9.,-]/g,'').replace(',','.');
    return parseFloat(t)||0;
  }

  function snapshot(){
    const params = {
      vMin: num(document.getElementById('vMin')?.value),
      vMax: num(document.getElementById('vMax')?.value),
      oreSapt: num(document.getElementById('oreSapt')?.value),
      saptAn: num(document.getElementById('saptAn')?.value),
      tDif: num(document.getElementById('tDif')?.value),
      tPM: num(document.getElementById('tPM')?.value),
      pctFOL: num(document.getElementById('pctFOL')?.value),
      factorC: num(document.getElementById('factorC')?.value) || 1
    };

    const rows = document.querySelectorAll('#tPlan tbody tr');
    const groups = [];

    rows.forEach(r=>{
      if(r.classList.contains('tot')) return;
      const tds = r.querySelectorAll('td');
      if(tds.length < 11) return;

      const name = tds[0].textContent.trim();
      const gis = num(tds[1].textContent);
      const rasr = num(tds[2].textContent);
      const fol = num(tds[3].textContent);

      groups.push({
        name,
        difKm: num(tds[6].textContent),
        pmKm: num(tds[10].textContent),
        comp: {gis: gis||1, rasr: rasr||1, fol: fol||0}
      });
    });

    return {params, groups};
  }

  async function callAPI(){
    try{
      const res = await fetch(API_BASE + '/calculate',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(snapshot())
      });
      return await res.json();
    }catch(e){
      return null;
    }
  }

  function ensurePanel(){
    let el = document.getElementById('pyPanel');
    if(el) return el;

    el = document.createElement('div');
    el.id = 'pyPanel';
    el.style.cssText = 'margin:12px 24px;padding:12px 16px;border:1px solid var(--border);border-radius:8px;background:#fff;font-size:11px;box-shadow:0 1px 3px rgba(0,0,0,.08)';
    el.innerHTML = '<div style="font-size:9px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:6px">🐍 PYTHON ENGINE VALIDATION</div><div id="pyContent" style="font-family:var(--mono)">loading...</div>';

    const anchor = document.querySelector('.kpi-bar') || document.body;
    anchor.parentNode.insertBefore(el, anchor.nextSibling);
    return el;
  }

  function render(data){
    const el = ensurePanel().querySelector('#pyContent');
    if(!data){ el.innerHTML = '<span style="color:var(--red)">⚠ API unavailable</span>'; return; }

    const rows = (data.groups||[]).map(r=>{
      const color = r.ok_dif ? 'var(--green)' : 'var(--red)';
      const icon = r.ok_dif ? '✓' : '✗';
      return `<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid var(--border)">
        <span>${r.name}</span>
        <span style="color:${color}">${icon} ${r.luni_dif?.toFixed(1)||'-'} luni dif · ${r.luni_pm?.toFixed(1)||'-'} luni PM</span>
      </div>`;
    }).join('');

    const scenarios = (data.scenarios||[]).map(s=>
      `<span style="margin-right:12px">${s.rate} km/h → dif ${(s.max_eta_dif_years*12).toFixed(1)}l · PM ${(s.max_eta_pm_years*12).toFixed(1)}l</span>`
    ).join('');

    el.innerHTML = rows +
      `<div style="margin-top:6px;font-size:9px;color:var(--muted)">Scenarii: ${scenarios}</div>` +
      `<div style="font-size:9px;color:var(--muted)">Rată medie: ${data.rata_medie} km/h</div>`;
  }

  let t;
  function schedule(){
    clearTimeout(t);
    t = setTimeout(async ()=>{
      const data = await callAPI();
      render(data);
    }, 600);
  }

  function init(){
    ensurePanel();
    document.addEventListener('input', schedule);

    const obs = new MutationObserver(schedule);
    const target = document.querySelector('#tPlan');
    if(target) obs.observe(target, {childList:true, subtree:true});

    schedule();
  }

  window.addEventListener('load', init);
})();
