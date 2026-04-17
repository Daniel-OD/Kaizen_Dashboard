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
      if(r.classList.contains('total')) return;
      const tds = r.querySelectorAll('td');
      if(tds.length < 11) return;

      const name = tds[0].textContent.trim();
      const compTxt = tds[3].textContent;
      const [gis,rasr,fol] = compTxt.split('/').map(x=>num(x));

      groups.push({
        name,
        difKm: num(tds[6].textContent),
        pmKm: num(tds[10].textContent),
        comp: {gis,rasr,fol}
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
    el.style.margin = '12px 0';
    el.style.padding = '10px';
    el.style.border = '1px solid #444';
    el.style.borderRadius = '8px';
    el.innerHTML = '<b>Python Engine</b><div id="pyContent">loading...</div>';

    const anchor = document.querySelector('.kpi-bar') || document.body;
    anchor.parentNode.insertBefore(el, anchor.nextSibling);
    return el;
  }

  function render(data){
    const el = ensurePanel().querySelector('#pyContent');
    if(!data){ el.innerHTML = '⚠️ API unavailable'; return; }

    const rows = (data.results||[]).slice(0,6).map(r=>
      `<div>${r.name}: ${r.etaYears?.toFixed(2)||'-'} yrs</div>`
    ).join('');

    el.innerHTML = rows || 'no data';
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
