// Cycom ERP Marketing Website — main.js
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
    solo:       { monthly: 59,  annual: 47 },
    business:   { monthly: 149, annual: 119 },
    enterprise: { monthly: 399, annual: 319 },
  };

  const annualSavings = {
    solo:       { save: 144 },
    business:   { save: 360 },
    enterprise: { save: 960 },
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

  // ── Language Toggle (AR/EN Dictionary) ────────────────────────
  const langBtn = document.getElementById('lang-toggle');
  let isAr = false;
  
  const translations = {
    'hero-title-1': { en: 'Run Your Global', ar: 'أدر أعمالك العالمية' },
    'hero-title-2': { en: 'Enterprise.', ar: 'بذكاء.' },
    'hero-title-3': { en: 'One Platform.', ar: 'منصة واحدة.' },
    'hero-sub': { 
      en: 'The next-generation autonomous B2B ERP. Unifying Finance, CRM, MRP, Inventory, HR, and Carbon accounting in one secure multi-tenant cloud.', 
      ar: 'نظام ERP الذاتي للأعمال. يوحد الحسابات، المبيعات، التصنيع، المخازن، الموارد البشرية، وحسابات انبعاثات الكربون في سحابة أمنة.' 
    },
    'nav-features': { en: 'Features', ar: 'المميزات' },
    'nav-pricing':  { en: 'Pricing', ar: 'الأسعار' },
    'nav-contact':  { en: 'Contact', ar: 'تواصل معنا' },
    'btn-trial':    { en: 'Start Free Trial', ar: 'ابدأ تجربة مجانية' },
    'btn-demo':     { en: 'Book a B2B Demo', ar: 'احجز عرضاً للشركات' },
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

  // ── AOS (scroll reveal helper) ────────────────────────────────
  const aosEls = document.querySelectorAll('[data-aos]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('aos-animate');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  aosEls.forEach(el => observer.observe(el));

  // ── Stats Counter animation ───────────────────────────────────
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

  // ── Smooth scrolling ──────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Lead generation mock form ─────────────────────────────────
  const trialForm = document.getElementById('trial-form');
  trialForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = trialForm.querySelector('input[type=email]').value;
    if (!email) return;
    const btn = trialForm.querySelector('button');
    btn.textContent = '✓ Welcome Onboard!';
    btn.style.background = 'var(--success)';
    btn.disabled = true;
    setTimeout(() => { 
      btn.textContent = 'Get Started Now'; 
      btn.style.background = ''; 
      btn.disabled = false; 
      trialForm.reset(); 
    }, 4000);
  });
});
