(function(){
  // Fix typography issues in CSS variables (– vs --)
  document.querySelectorAll('style').forEach(s=>{
    s.textContent = s.textContent
      .replace(/var\(–/g,'var(--')
      .replace(/–/g,'-')
      .replace(/—/g,'-');
  });

  // Replace base64 logo with static asset
  const logo = document.querySelector('.kzLogo img');
  if(logo){
    logo.src = '/static/logo-delgaz.svg';
    logo.alt = 'Delgaz Grid';
  }

  // Patch factorC consistency in runtime calculations (safe override)
  window.__applyFactorC = function(val, factor){
    return val * (factor || 1.0);
  };
})();
