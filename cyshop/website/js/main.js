// CyShop Marketing Website — main.js
// CYBERCOM REVOLUTION © 2026

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll effect ──────────────────────────────────────
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  // ── Mobile menu toggle ────────────────────────────────────────
  const mobileBtn = document.getElementById('mobile-menu-btn');
  const mobileNav = document.getElementById('mobile-nav');
  mobileBtn?.addEventListener('click', () => {
    const isOpen = mobileNav.style.display === 'flex';
    mobileNav.style.display = isOpen ? 'none' : 'flex';
  });
  mobileNav?.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => { mobileNav.style.display = 'none'; });
  });

  // ── Pricing Toggle ────────────────────────────────────────────
  let isAnnual = false;
  const toggle = document.getElementById('pricing-toggle');
  const monthLabel = document.getElementById('label-monthly');
  const annualLabel = document.getElementById('label-annual');

  const prices = {
    solo:         { monthly: 39,  annual: 31 },
    starter:      { monthly: 79,  annual: 63 },
    growth:       { monthly: 199, annual: 159 },
    professional: { monthly: 449, annual: 359 },
  };

  const annualSavings = {
    solo:         { monthly: 39,  annual: 31,  save: 96 },
    starter:      { monthly: 79,  annual: 63,  save: 192 },
    growth:       { monthly: 199, annual: 159, save: 480 },
    professional: { monthly: 449, annual: 359, save: 1080 },
  };

  function updatePricing() {
    Object.keys(prices).forEach(plan => {
      const amountEl = document.getElementById(`price-${plan}`);
      const savedEl  = document.getElementById(`saved-${plan}`);
      if (!amountEl) return;
      const p = prices[plan];
      amountEl.textContent = isAnnual ? p.annual : p.monthly;
      if (savedEl) {
        if (isAnnual) {
          savedEl.textContent = `Save $${annualSavings[plan].save}/year`;
          savedEl.className = 'plan-annual saved';
        } else {
          savedEl.textContent = `Billed monthly`;
          savedEl.className = 'plan-annual';
        }
      }
    });
    monthLabel.classList.toggle('active', !isAnnual);
    annualLabel.classList.toggle('active', isAnnual);
    toggle.classList.toggle('on', isAnnual);
  }

  toggle?.addEventListener('click', () => { isAnnual = !isAnnual; updatePricing(); });

  // ── Feature deep dive tabs ────────────────────────────────────
  const diveTabs = document.querySelectorAll('.dive-tab');
  const diveContents = document.querySelectorAll('.dive-panel');
  diveTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      diveTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      diveContents.forEach(panel => {
        panel.style.display = panel.id === `dive-${target}` ? 'grid' : 'none';
      });
    });
  });

  // ── Language Toggle ───────────────────────────────────────────
  const langBtn = document.getElementById('lang-toggle');
  let isAr = false;
  const translations = {
    'hero-title-1': { en: 'Run Your Entire', ar: 'أدر عملك بالكامل' },
    'hero-title-2': { en: 'Business.', ar: 'بالكامل.' },
    'hero-title-3': { en: 'One Platform.', ar: 'منصة واحدة.' },
    'hero-sub':     { en: 'The complete ERP for retail, restaurant, bakery, supermarket and multi-branch chains. Built for the Middle East and beyond.', ar: 'نظام ERP متكامل للمطاعم والسوبرماركت والمخابز وسلاسل الفروع المتعددة. مصمم للشرق الأوسط والعالم.' },
    'nav-features': { en: 'Features', ar: 'المميزات' },
    'nav-industries':{ en: 'Industries', ar: 'القطاعات' },
    'nav-pricing':  { en: 'Pricing', ar: 'الأسعار' },
    'nav-contact':  { en: 'Contact', ar: 'تواصل معنا' },
    'btn-trial':    { en: 'Start Free 14-Day Trial', ar: 'ابدأ تجربة مجانية ١٤ يوم' },
    'btn-demo':     { en: 'Book a Live Demo', ar: 'احجز عرضاً مباشراً' },
    'btn-nav-demo': { en: 'Live Demo', ar: 'عرض مباشر' },
    'btn-hero-demo': { en: '⚡ Launch Live Demo', ar: '⚡ تشغيل العرض المباشر' },
    'btn-mobile-demo': { en: 'Launch Live Demo →', ar: 'تشغيل العرض المباشر ←' },
  };
  langBtn?.addEventListener('click', () => {
    isAr = !isAr;
    langBtn.textContent = isAr ? 'EN' : 'AR';
    document.documentElement.dir = isAr ? 'rtl' : 'ltr';
    Object.entries(translations).forEach(([id, t]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = isAr ? t.ar : t.en;
    });
  });

  // ── AOS (scroll reveal) ───────────────────────────────────────
  const aosEls = document.querySelectorAll('[data-aos]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('aos-animate');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  aosEls.forEach(el => observer.observe(el));

  // ── Counter animation ─────────────────────────────────────────
  function animateCounter(el, target, suffix = '') {
    let start = 0;
    const step = target / 60;
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { start = target; clearInterval(timer); }
      el.textContent = Math.round(start).toLocaleString() + suffix;
    }, 20);
  }
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        animateCounter(el, parseInt(el.dataset.target), el.dataset.suffix || '');
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  document.querySelectorAll('[data-counter]').forEach(el => counterObserver.observe(el));

  // ── Smooth CTA scroll ─────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Trial form demo ───────────────────────────────────────────
  const trialForm = document.getElementById('trial-form');
  trialForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = trialForm.querySelector('input[type=email]').value;
    if (!email) return;
    const btn = trialForm.querySelector('button');
    btn.textContent = '✓ You\'re on the list!';
    btn.style.background = 'var(--success)';
    btn.disabled = true;
    setTimeout(() => { btn.textContent = 'Start Free Trial'; btn.style.background = ''; btn.disabled = false; trialForm.reset(); }, 4000);
  });
});
