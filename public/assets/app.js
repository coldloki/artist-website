/* ===========================================================
   Santhiago Collection — gallery interactivity
   - Theme toggle (light/dark, persisted)
   - Hamburger nav toggle on small screens
   - Lightbox for grid tiles
   =========================================================== */

(function () {
  'use strict';

  // ------- Theme -------
  const STORAGE_KEY = 'antonia-theme';
  const root = document.documentElement;

  function getPreferredTheme() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'light' || stored === 'dark') return stored;
    } catch (e) { /* private mode */ }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    const btn = document.querySelector('.theme-toggle');
    if (btn) {
      btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
      btn.setAttribute('aria-pressed', theme === 'dark');
    }
  }

  applyTheme(getPreferredTheme());

  document.addEventListener('DOMContentLoaded', () => {
    // Always-solid header for now — backdrop blur alone is too unreliable
    // on dark backgrounds. Set the .has-solid class immediately so CSS picks it up.
    const header = document.querySelector('.site-header');
    if (header) header.classList.add('has-solid');

    // Theme toggle wiring
    const themeBtn = document.querySelector('.theme-toggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => {
        const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        try { localStorage.setItem(STORAGE_KEY, next); } catch (e) { /* private mode */ }
      });
    }

    // Hamburger nav wiring
    const navToggle = document.querySelector('.nav-toggle');
    const navClose = document.querySelector('.nav-close');
    const nav = document.querySelector('.nav');
    if (navToggle && nav) {
      const setOpen = (open) => {
        nav.classList.toggle('is-open', open);
        navToggle.classList.toggle('is-open', open);
        navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
        document.body.classList.toggle('nav-open', open);
        document.body.style.overflow = open ? 'hidden' : '';
      };
      navToggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
      // The big "Close" button inside the overlay
      if (navClose) {
        navClose.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen(false);
        });
      }
      // Close the menu when a nav link is tapped (so the page transition feels clean)
      nav.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => setOpen(false));
      });
      // Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && nav.classList.contains('is-open')) setOpen(false);
      });
      // Close when tapping the overlay background (but not when tapping a link or button)
      nav.addEventListener('click', (e) => {
        if (e.target === nav) setOpen(false);
      });
    }

    // Lightbox wiring
    const lb = document.querySelector('.lightbox');
    const lbImg = lb ? lb.querySelector('img') : null;
    if (lb && lbImg) {
      document.querySelectorAll('[data-lightbox]').forEach(el => {
        el.addEventListener('click', (e) => {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
          e.preventDefault();
          const src = el.getAttribute('data-lightbox');
          // Prefer the WebP full-size variant for the lightbox if it exists.
          // The lightbox always shows the largest available image, so the JPEG
          // fallback inside the <picture> only matters if WebP generation failed.
          const webpSrc = src.replace(/\.(jpe?g|png)$/i, '.webp');
          lbImg.src = webpSrc;
          lbImg.alt = el.getAttribute('data-lightbox-title') || '';
          lb.classList.add('is-open');
          lb.setAttribute('aria-hidden', 'false');
          document.body.style.overflow = 'hidden';
        });
      });

      function close() {
        lb.classList.remove('is-open');
        lb.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        setTimeout(() => { lbImg.src = ''; }, 200);
      }

      lb.addEventListener('click', (e) => {
        if (e.target === lb || e.target.classList.contains('lightbox__close')) close();
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lb.classList.contains('is-open')) close();
      });
    }
  });
})();