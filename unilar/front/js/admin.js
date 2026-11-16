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

  // Fotos do imóvel: cada seleção soma às anteriores, dá para tirar uma foto antes de salvar
  // e as imagens são reduzidas no navegador (a Vercel recusa envios acima de 4,5 MB).
  const inputFotos = document.querySelector('.upload-field input[type="file"]');
  const preview = document.querySelector('#photoPreview');
  if (inputFotos && preview && window.DataTransfer) {
    const LADO_MAXIMO = 1600;
    const LIMITE_ENVIO = 4 * 1024 * 1024;
    const formFotos = inputFotos.form;
    const aviso = document.createElement('small');
    aviso.className = 'field-error';
    aviso.hidden = true;
    preview.after(aviso);
    let selecionadas = [];

    const sincronizar = () => {
      const lista = new DataTransfer();
      selecionadas.forEach((arquivo) => lista.items.add(arquivo));
      inputFotos.files = lista.files;
    };

    const desenhar = () => {
      preview.replaceChildren();
      selecionadas.forEach((arquivo, indice) => {
        const item = document.createElement('figure');
        item.className = 'photo-preview-item';
        const imagem = document.createElement('img');
        imagem.src = URL.createObjectURL(arquivo);
        imagem.alt = `Prévia: ${arquivo.name}`;
        imagem.onload = () => URL.revokeObjectURL(imagem.src);
        const remover = document.createElement('button');
        remover.type = 'button';
        remover.className = 'photo-preview-remove';
        remover.setAttribute('aria-label', `Tirar ${arquivo.name}`);
        remover.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
        remover.addEventListener('click', () => {
          selecionadas.splice(indice, 1);
          sincronizar();
          desenhar();
        });
        item.append(imagem, remover);
        preview.append(item);
      });
      if (selecionadas.length) {
        const total = document.createElement('p');
        total.className = 'photo-preview-count';
        total.textContent = `${selecionadas.length} foto${selecionadas.length > 1 ? 's' : ''} para enviar. Clique no campo acima para adicionar mais.`;
        preview.append(total);
      }
    };

    const reduzir = (arquivo) => new Promise((resolve) => {
      if (!arquivo.type.startsWith('image/') || arquivo.type === 'image/gif') { resolve(arquivo); return; }
      const imagem = new Image();
      const url = URL.createObjectURL(arquivo);
      imagem.onload = () => {
        URL.revokeObjectURL(url);
        const escala = Math.min(1, LADO_MAXIMO / Math.max(imagem.naturalWidth, imagem.naturalHeight));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(imagem.naturalWidth * escala);
        canvas.height = Math.round(imagem.naturalHeight * escala);
        canvas.getContext('2d').drawImage(imagem, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (!blob || blob.size >= arquivo.size) { resolve(arquivo); return; }
          const nome = arquivo.name.replace(/\.[^.]+$/, '') + '.jpg';
          resolve(new File([blob], nome, { type: 'image/jpeg' }));
        }, 'image/jpeg', 0.82);
      };
      imagem.onerror = () => { URL.revokeObjectURL(url); resolve(arquivo); };
      imagem.src = url;
    });

    inputFotos.addEventListener('change', async () => {
      const novas = Array.from(inputFotos.files).filter((arquivo) => arquivo.type.startsWith('image/'));
      aviso.hidden = true;
      inputFotos.disabled = true;
      const reduzidas = await Promise.all(novas.map(reduzir));
      inputFotos.disabled = false;
      selecionadas = selecionadas.concat(reduzidas);
      sincronizar();
      desenhar();
    });

    formFotos?.addEventListener('submit', (evento) => {
      const tamanho = selecionadas.reduce((soma, arquivo) => soma + arquivo.size, 0);
      if (tamanho > LIMITE_ENVIO) {
        evento.preventDefault();
        aviso.textContent = 'As fotos selecionadas passam do limite de envio. Salve com menos fotos e adicione o restante editando o imóvel em seguida.';
        aviso.hidden = false;
        aviso.scrollIntoView({ block: 'center' });
      }
    });
  }
});
