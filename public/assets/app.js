/* ===========================================================
   Santhiago Collection — gallery interactivity
   - Theme toggle (light/dark, persisted)
   - Hamburger nav toggle on small screens
   - Lightbox for grid tiles (with focus trap)
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
        if (open) {
          // Move focus into the overlay for keyboard users
          const firstLink = nav.querySelector('a, button');
          if (firstLink) firstLink.focus();
        } else {
          // Return focus to the toggle button
          navToggle.focus();
        }
      };
      navToggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
      if (navClose) {
        navClose.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen(false);
        });
      }
      nav.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => setOpen(false));
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && nav.classList.contains('is-open')) setOpen(false);
      });
      nav.addEventListener('click', (e) => {
        if (e.target === nav) setOpen(false);
      });
    }

    // Lightbox wiring — with focus trap
    const lb = document.querySelector('.lightbox');
    const lbImg = lb ? lb.querySelector('img') : null;
    if (lb && lbImg) {
      // Remember which element opened the lightbox so we can return focus
      let lbPrevFocus = null;

      function openLb(src, title, opener) {
        const webpSrc = src.replace(/\.(jpe?g|png)$/i, '.webp');
        lbImg.src = webpSrc;
        lbImg.alt = title || '';
        lb.classList.add('is-open');
        lb.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        lbPrevFocus = opener || document.activeElement;
        // Focus the close button so screen reader users land somewhere sensible
        const closeBtn = lb.querySelector('.lightbox__close');
        if (closeBtn) closeBtn.focus();
      }

      function closeLb() {
        lb.classList.remove('is-open');
        lb.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        setTimeout(() => { lbImg.src = ''; }, 200);
        // Restore focus to the element that opened the lightbox
        if (lbPrevFocus && typeof lbPrevFocus.focus === 'function') {
          lbPrevFocus.focus();
        }
      }

      // Focus trap: when tabbing inside the lightbox, cycle between the image
      // and the close button (the only focusable elements).
      lb.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab' || !lb.classList.contains('is-open')) return;
        const focusable = lb.querySelectorAll('button, [tabindex]:not([tabindex="-1"])');
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      });

      document.querySelectorAll('[data-lightbox]').forEach(el => {
        el.addEventListener('click', (e) => {
          if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
          e.preventDefault();
          openLb(
            el.getAttribute('data-lightbox'),
            el.getAttribute('data-lightbox-title') || '',
            el
          );
        });
      });

      lb.addEventListener('click', (e) => {
        if (e.target === lb || e.target.classList.contains('lightbox__close')) closeLb();
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && lb.classList.contains('is-open')) closeLb();
      });
    }
  });
})();
