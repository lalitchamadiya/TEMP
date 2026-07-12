/* =========================================================
   HMS — Theme Toggle (Dark / Light)
   Runs immediately; DOMContentLoaded hooks up the button.
   ========================================================= */
(function () {
  var THEME_KEY = 'hms_theme';

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    var icon = document.getElementById('themeIcon');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }
    var label = document.getElementById('themeLabel');
    if (label) {
      label.textContent = theme === 'dark' ? 'Light' : 'Dark';
    }
  }

  // Apply saved theme immediately (no flash)
  var savedTheme = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(savedTheme);

  document.addEventListener('DOMContentLoaded', function () {
    // Re-sync icon after DOM is ready
    applyTheme(localStorage.getItem(THEME_KEY) || 'dark');

    var btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
      });
    }
  });
})();
