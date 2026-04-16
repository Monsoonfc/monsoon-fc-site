// Monsoon FC — main.js

// Menu mobile
const toggle = document.getElementById('menuToggle');
const nav = document.getElementById('navLinks');
if (toggle && nav) {
  toggle.addEventListener('click', () => nav.classList.toggle('open'));
  document.addEventListener('click', (e) => {
    if (!toggle.contains(e.target) && !nav.contains(e.target)) {
      nav.classList.remove('open');
    }
  });
}

// Filtros (funciona para feed, noticias e posts)
const filterBtns = document.querySelectorAll('.filter-btn');
const grid = document.getElementById('postsGrid') || document.getElementById('articlesGrid');

function applyFilter(filter) {
  if (!grid) return;
  filterBtns.forEach(b => b.classList.remove('active'));
  const activeBtn = document.querySelector(`.filter-btn[data-filter="${filter}"]`);
  if (activeBtn) activeBtn.classList.add('active');
  else if (document.querySelector('.filter-btn[data-filter="all"]')) {
    document.querySelector('.filter-btn[data-filter="all"]').classList.add('active');
  }
  const items = grid.querySelectorAll('[data-type]');
  items.forEach(item => {
    if (!filter || filter === 'all' || item.dataset.type === filter) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
    }
  });
}

if (filterBtns.length && grid) {
  // Ler filtro da URL hash (ex: feed/index.html#noticia)
  const hashFilter = window.location.hash.replace('#', '');
  if (hashFilter) {
    applyFilter(hashFilter);
    // Rolar até o grid
    setTimeout(() => grid.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300);
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;
      history.replaceState(null, '', filter === 'all' ? '#' : '#' + filter);
      applyFilter(filter);
    });
  });
}

// Lazy load fallback
document.querySelectorAll('img[loading="lazy"]').forEach(img => {
  img.addEventListener('error', () => {
    img.style.display = 'none';
  });
});
