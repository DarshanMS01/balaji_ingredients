/**
 * Balaji Ingredients — main.js
 * Level 1: Navbar scroll, hamburger menu, scroll reveal animations.
 */

'use strict';

/* ============================================================
   1. NAVBAR — Transparent over hero, scrolled state
   ============================================================ */
(function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  const SCROLL_THRESHOLD = 60;

  function updateNavbar() {
    if (window.scrollY > SCROLL_THRESHOLD) {
      navbar.classList.add('scrolled');
      navbar.classList.remove('transparent');
    } else {
      navbar.classList.remove('scrolled');
      navbar.classList.add('transparent');
    }
  }

  // Initialise
  updateNavbar();

  // Add scroll listener (throttled with requestAnimationFrame)
  let ticking = false;
  window.addEventListener('scroll', function () {
    if (!ticking) {
      window.requestAnimationFrame(function () {
        updateNavbar();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
})();


/* ============================================================
   2. HAMBURGER MENU
   ============================================================ */
(function initHamburger() {
  const hamburger  = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  const navbar     = document.getElementById('navbar');

  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', function () {
    const isOpen = mobileMenu.classList.toggle('open');
    hamburger.classList.toggle('open', isOpen);
    hamburger.setAttribute('aria-expanded', isOpen.toString());
    // Prevent scrolling while menu is open
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // Close mobile menu on link click
  mobileMenu.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      mobileMenu.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  // Close mobile menu on outside click
  document.addEventListener('click', function (e) {
    if (
      !navbar.contains(e.target) &&
      mobileMenu.classList.contains('open')
    ) {
      mobileMenu.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
})();


/* ============================================================
   3. SCROLL REVEAL — IntersectionObserver
   ============================================================ */
(function initScrollReveal() {
  const revealElements = document.querySelectorAll(
    '.reveal-up, .reveal-left, .reveal-right'
  );

  if (!revealElements.length) return;

  // If IntersectionObserver is not supported, just show everything
  if (!('IntersectionObserver' in window)) {
    revealElements.forEach(function (el) {
      el.classList.add('revealed');
    });
    return;
  }

  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target); // only animate once
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px'
    }
  );

  revealElements.forEach(function (el) {
    observer.observe(el);
  });
})();


/* ============================================================
   4. SMOOTH SCROLL for anchor links
   ============================================================ */
(function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();
      const offset = 80; // navbar height
      const targetY = target.getBoundingClientRect().top + window.pageYOffset - offset;

      window.scrollTo({ top: targetY, behavior: 'smooth' });
    });
  });
})();


/* ============================================================
   5. ACTIVE NAV LINK based on current URL path
   ============================================================ */
(function initActiveNav() {
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(function (link) {
    const href = link.getAttribute('href');
    if (!href) return;
    // Extract path from href (strips query/hash)
    try {
      const url = new URL(href, window.location.origin);
      if (url.pathname !== '/' && currentPath.startsWith(url.pathname)) {
        link.classList.add('active');
      } else if (url.pathname === '/' && currentPath === '/') {
        link.classList.add('active');
      }
    } catch (e) { /* ignore */ }
  });
})();


/* ============================================================
   6. AUTO-DISMISS MESSAGES after 5 seconds
   ============================================================ */
(function initMessages() {
  document.querySelectorAll('.message').forEach(function (msg) {
    setTimeout(function () {
      msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(20px)';
      setTimeout(function () { msg.remove(); }, 500);
    }, 5000);
  });
})();
