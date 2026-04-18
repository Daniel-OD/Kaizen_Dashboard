(function(){
  const API_BASE = '/api';

  // ---------------------------------------------------------------------------
  // In-memory dashboard state — the single source of truth for the API payload.
  // The HTML table (#tPlan) is a *rendering target*, NOT a data source.
  // ---------------------------------------------------------------------------
  const _state = { params: null, groups: [] };

  function num(x){
    if(!x) return 0;
    const t = String(x).replace(/[^0-9.,-]/g,'').replace(',','.');
    return parseFloat(t)||0;
  }

  /** Read global parameters from the exposed dashboard state, falling back to input fields. */
  function readParams(){
    if(window.__dashboardState && window.__dashboardState.params){
      return Object.assign({}, window.__dashboardState.params);
    }
    return {
      vMin: num(document.getElementById('vMin')?.value),
      vMax: num(document.getElementById('vMax')?.value),
      oreSapt: num(document.getElementById('oreSapt')?.value),
      saptAn: num(document.getElementById('saptAn')?.value),
      tDif: num(document.getElementById('tDif')?.value),
      tPM: num(document.getElementById('tPM')?.value),
      pctFOL: num(document.getElementById('pctFOL')?.value),
      factorCDif: num(document.getElementById('factorCDif')?.value) || 1,
      factorCPM: num(document.getElementById('factorCPM')?.value) || 1
    };
  }

  /** Read groups from the exposed dashboard state, falling back to the rendered table. */
  function readGroups(){
    if(window.__dashboardState && Array.isArray(window.__dashboardState.groups) && window.__dashboardState.groups.length){
      return window.__dashboardState.groups;
    }
    // Fallback: scrape table (only used before first fullUpdate runs)
    const rows = document.querySelectorAll('#tPlan tbody tr');
    const groups = [];
    rows.forEach(r=>{
      if(r.classList.contains('tot')) return;
      const tds = r.querySelectorAll('td');
      if(tds.length < 11) return;
      groups.push({
        name: tds[0].textContent.trim(),
        difKm: num(tds[6].textContent),
        pmKm: num(tds[10].textContent),
        comp: {
          gis: num(tds[1].textContent),
          rasr: num(tds[2].textContent),
          fol: num(tds[3].textContent)
        }
      });
    });
    return groups;
  }

  /**
   * Build the API payload from the stable dashboard state.
   * Prefers window.__dashboardState (set by fullUpdate in index.html).
   * Falls back to DOM scraping only before first fullUpdate.
   */
  function snapshot(){
    _state.params = readParams();
    _state.groups = readGroups();
    return { params: _state.params, groups: _state.groups };
  }

  // Expose state for debugging / future integration
  window.__bridgeState = _state;

  // ---------------------------------------------------------------------------
  // API communication with robust error handling
  // ---------------------------------------------------------------------------

  async function callAPI(){
    let res;
    try{
      res = await fetch(API_BASE + '/calculate',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(snapshot())
      });
    }catch(networkErr){
      console.error('[bridge] Network error calling /api/calculate:', networkErr);
      return { _error: 'Network error — API unreachable' };
    }

    if(!res.ok){
      const text = await res.text().catch(()=>'(no body)');
      console.error(`[bridge] /api/calculate returned HTTP ${res.status}:`, text);
      return { _error: `HTTP ${res.status} — ${text.slice(0,120)}` };
    }

    try{
      return await res.json();
    }catch(jsonErr){
      console.error('[bridge] Invalid JSON from /api/calculate:', jsonErr);
      return { _error: 'Invalid JSON response from API' };
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

  /** Format an ETA value — handles the blocked sentinel (-1). */
  function fmtEta(v){
    if(v === -1 || v === null || v === undefined) return '∞';
    return v.toFixed(1);
  }

  function render(data){
    const el = ensurePanel().querySelector('#pyContent');

    if(!data){
      el.innerHTML = '<span style="color:var(--red)">⚠ API unavailable</span>';
      return;
    }

    if(data._error){
      el.innerHTML = '<span style="color:var(--red)">⚠ Python API error</span>' +
        '<div style="font-size:9px;color:var(--muted);margin-top:2px">' + data._error + '</div>';
      return;
    }

    const rows = (data.groups||[]).map(r=>{
      const blocked = r.luni_dif === -1 || r.luni_pm === -1;
      const color = blocked ? 'var(--muted)' : (r.ok_dif ? 'var(--green)' : 'var(--red)');
      const icon = blocked ? '⏸' : (r.ok_dif ? '✓' : '✗');
      return `<div style="display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid var(--border)">
        <span>${r.name}</span>
        <span style="color:${color}">${icon} ${fmtEta(r.luni_dif)} luni dif · ${fmtEta(r.luni_pm)} luni PM</span>
      </div>`;
    }).join('');

    const scenarios = (data.scenarios||[]).map(s=>{
      const dM = s.max_eta_dif_years === -1 ? '∞' : (s.max_eta_dif_years*12).toFixed(1);
      const pM = s.max_eta_pm_years === -1 ? '∞' : (s.max_eta_pm_years*12).toFixed(1);
      return `<span style="margin-right:12px">${s.rate} km/h → dif ${dM}l · PM ${pM}l</span>`;
    }).join('');

    // Summary line (if available from backend)
    const sum = data.summary;
    const sumLine = sum ? `<div style="font-size:9px;color:var(--muted)">Sumar: ${sum.total_groups} grupuri · ${sum.groups_ok_dif} ok dif · ${sum.blocked_groups} blocate · factorDif=${sum.factor_c_dif} · factorPM=${sum.factor_c_pm}</div>` : '';

    el.innerHTML = rows +
      `<div style="margin-top:6px;font-size:9px;color:var(--muted)">Scenarii: ${scenarios}</div>` +
      `<div style="font-size:9px;color:var(--muted)">Rată medie: ${data.rata_medie} km/h</div>` +
      sumLine;
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
