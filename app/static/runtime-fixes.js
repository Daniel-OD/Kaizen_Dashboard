(function(){
  // Fix typography issues in CSS variables (en-dash vs double hyphen) — safety net
  // Primary fix is now in index.html source; this catches any remaining edge cases.
  document.querySelectorAll('style').forEach(s=>{
    s.textContent = s.textContent
      .replace(/var\(\u2013/g,'var(--')
      .replace(/\u2013/g,'-')
      .replace(/\u2014/g,'-');
  });

  // Ensure login logo uses static asset (safety net)
  const logo = document.querySelector('.kzLogo img');
  if(logo && !logo.src.includes('/static/')){
    logo.src = '/static/logo-delgaz.svg';
    logo.alt = 'Delgaz Grid';
  }
})();
