/**
 * MedAI Diagnostics — Frontend JS
 * Handles animations, bar growth, active nav state
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Animate probability bars on load ────────────────────────
  document.querySelectorAll('.prob-bar, .expl-bar').forEach(bar => {
    const target = bar.style.width;
    bar.style.width = '0';
    requestAnimationFrame(() => {
      setTimeout(() => {
        bar.style.transition = 'width 0.9s cubic-bezier(0.4,0,0.2,1)';
        bar.style.width = target;
      }, 100);
    });
  });

  // ── Flash message auto-dismiss ───────────────────────────────
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // ── Range input sync (fallback) ──────────────────────────────
  document.querySelectorAll('input[type="range"]').forEach(input => {
    const display = document.getElementById(input.id.replace('-range', '-val'));
    if (display) {
      display.textContent = input.value;
      input.addEventListener('input', () => display.textContent = input.value);
    }
  });

  // ── Print styles ─────────────────────────────────────────────
  window.matchMedia('print').addListener(() => {
    document.querySelectorAll('.prob-bar, .expl-bar').forEach(bar => {
      bar.style.transition = 'none';
    });
  });

  // ── Theme persistence ────────────────────────────────────────
  const savedTheme = localStorage.getItem('medai-theme');
  if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
  }
  updateToggleLabel();

});

function toggleMode() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('medai-theme', isLight ? 'light' : 'dark');
  updateToggleLabel();
}

function updateToggleLabel() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  const isLight = document.body.classList.contains('light-mode');
  btn.innerHTML = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
}

