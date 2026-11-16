document.addEventListener('DOMContentLoaded', () => {
  const page = document.querySelector('.admin-page');
  const menuToggle = document.querySelector('.admin-menu-toggle');

  menuToggle?.addEventListener('click', () => {
    const aberto = page.classList.toggle('menu-open');
    menuToggle.setAttribute('aria-expanded', String(aberto));
  });

  page.addEventListener('click', (event) => {
    if (event.target instanceof Element && event.target.closest('.admin-nav a')) {
      page.classList.remove('menu-open');
      menuToggle?.setAttribute('aria-expanded', 'false');
    }

    if (event.target instanceof Element && !event.target.closest('.topbar-popover')) {
      document.querySelectorAll('.topbar-popover[open]').forEach((popover) => {
        popover.removeAttribute('open');
      });
    }

    if (event.target instanceof Element && !event.target.closest('.recent-property-menu')) {
      document.querySelectorAll('.recent-property-menu[open]').forEach((menu) => {
        menu.removeAttribute('open');
      });
    }

    if (
      page.classList.contains('menu-open')
      && event.target instanceof Element
      && !event.target.closest('.admin-sidebar')
      && !event.target.closest('.admin-menu-toggle')
    ) {
      page.classList.remove('menu-open');
      menuToggle?.setAttribute('aria-expanded', 'false');
    }
  });

  document.querySelectorAll('[data-auto-submit]').forEach((control) => {
    control.addEventListener('change', () => control.form.requestSubmit());
  });
  page.classList.add('js-enabled');

  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});
