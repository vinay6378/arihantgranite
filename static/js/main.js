document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('mobile-nav-toggle');
  var nav = document.getElementById('mobile-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('hidden');
    });
  }

  // Header scroll effect
  const header = document.querySelector('.modern-header');
  if (header) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    });
  }

  // Smooth scroll for anchor links (native)
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#' && href !== '') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // Intersection Observer for scroll animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
      }
    });
  }, observerOptions);

  // Observe all reveal elements
  document.querySelectorAll('.reveal').forEach(el => {
    observer.observe(el);
  });

  // Removed heavy parallax on scroll for performance

  // Add smooth transitions to modal
  const modals = document.querySelectorAll('[id$="-modal"], #lightbox');
  modals.forEach(modal => {
    if (modal) {
      modal.addEventListener('click', function(e) {
        if (e.target === this) {
          const content = this.querySelector('.modal-content');
          if (content) {
            content.style.transform = 'scale(0.95)';
            setTimeout(() => {
              this.classList.add('hidden');
              document.body.style.overflow = 'auto';
            }, 200);
          }
        }
      });
    }
  });
});

console.log('Arihant Granite\'s site loaded with modern animations');
