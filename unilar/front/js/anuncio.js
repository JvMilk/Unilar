// Página de detalhes do imóvel: compartilhar, "Mostrar mais" e galeria de fotos.
(function () {
    const compartilhar = document.getElementById('compartilhar');
    if (compartilhar) {
        const rotulo = compartilhar.querySelector('span');
        compartilhar.addEventListener('click', async function () {
            const dados = { title: compartilhar.dataset.titulo, url: window.location.href };
            try {
                if (navigator.share) {
                    await navigator.share(dados);
                    return;
                }
                await navigator.clipboard.writeText(dados.url);
                rotulo.textContent = 'Link copiado!';
            } catch (erro) {
                if (erro && erro.name === 'AbortError') return;
                rotulo.textContent = 'Copie o endereço da barra';
            }
            setTimeout(function () { rotulo.textContent = 'Compartilhar'; }, 2500);
        });
    }

    const mostrarMais = document.getElementById('mostrarMais');
    const texto = document.getElementById('descricaoTexto');
    if (mostrarMais && texto) {
        mostrarMais.addEventListener('click', function () {
            const aberto = texto.classList.toggle('recolhido') === false;
            mostrarMais.setAttribute('aria-expanded', String(aberto));
            mostrarMais.innerHTML = aberto
                ? 'Mostrar menos <i class="bi bi-chevron-up" aria-hidden="true"></i>'
                : 'Mostrar mais <i class="bi bi-chevron-down" aria-hidden="true"></i>';
        });
    }

    // Ao abrir a galeria pela foto clicada, rola até ela.
    const modalFotos = document.getElementById('modalFotos');
    if (modalFotos) {
        modalFotos.addEventListener('shown.bs.modal', function (evento) {
            const indice = evento.relatedTarget ? evento.relatedTarget.dataset.foto : '0';
            const foto = document.getElementById('foto-' + indice);
            if (foto && indice !== '0') foto.scrollIntoView({ block: 'start' });
        });
    }
})();
