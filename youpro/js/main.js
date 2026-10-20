document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });

    links.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => links.classList.remove('open'));
    });
  }

  const form = document.querySelector('#contact-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = form.querySelector('#name').value.trim();
      const email = form.querySelector('#email').value.trim();
      const profile = form.querySelector('#profile').value;
      const message = form.querySelector('#message').value.trim();
      const subject = encodeURIComponent(`Contato via site — ${name}`);
      const body = encodeURIComponent(`Nome: ${name}\nE-mail: ${email}\nPerfil: ${profile}\n\n${message}`);
      window.location.href = `mailto:contato@youpro.app?subject=${subject}&body=${body}`;
    });
  }
});
