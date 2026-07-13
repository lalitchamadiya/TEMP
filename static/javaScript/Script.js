/* =========================================================
   HMS — Theme Toggle (Light / Dark / System Auto Detection)
   Calculates active settings and matches OS theme options
   ========================================================= */
(function () {
  var THEME_KEY = 'hms_theme';

  function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  window.applyThemeMode = function (theme) {
    var actualTheme = theme;
    if (theme === 'system') {
      actualTheme = getSystemTheme();
    }
    
    document.documentElement.setAttribute('data-theme', actualTheme);
    localStorage.setItem(THEME_KEY, theme);

    // Sync elements
    var icon = document.getElementById('themeIcon');
    if (icon) {
      if (theme === 'dark') {
        icon.className = 'bi bi-moon-fill text-primary';
      } else if (theme === 'light') {
        icon.className = 'bi bi-sun-fill text-warning';
      } else {
        icon.className = 'bi bi-laptop text-info';
      }
    }
    
    var label = document.getElementById('themeLabel');
    if (label) {
      label.textContent = theme.charAt(0).toUpperCase() + theme.slice(1);
    }
  };

  // Listen for system theme changes if set to 'system'
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
    if (localStorage.getItem(THEME_KEY) === 'system') {
      window.applyThemeMode('system');
    }
  });

  // Apply immediately on load (no flash)
  var savedTheme = localStorage.getItem(THEME_KEY) || 'dark';
  window.applyThemeMode(savedTheme);

  document.addEventListener('DOMContentLoaded', function () {
    // Re-sync after DOM elements are fully loaded
    window.applyThemeMode(localStorage.getItem(THEME_KEY) || 'dark');
  });
})();
