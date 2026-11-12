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

    // Mapa: troca entre o imóvel e os pontos de referência ao redor.
    const painel = document.querySelector('.anuncio-mapa-painel');
    if (painel) {
        const mapa = document.getElementById('mapaImovel');
        const legenda = document.getElementById('mapaLegenda');
        const abrir = document.getElementById('mapaAbrir');
        const endereco = painel.dataset.endereco;
        const chave = painel.dataset.chave;
        painel.querySelectorAll('.anuncio-mapa-filtro').forEach(function (botao) {
            botao.addEventListener('click', function () {
                const busca = botao.dataset.busca;
                const consulta = busca ? busca + ' perto de ' + endereco : endereco;
                const q = encodeURIComponent(consulta);
                if (chave) {
                    mapa.src = 'https://www.google.com/maps/embed/v1/' + (busca ? 'search' : 'place') + '?key=' + encodeURIComponent(chave) + '&q=' + q;
                } else {
                    mapa.src = 'https://maps.google.com/maps?q=' + q + '&z=' + (busca ? '15' : '16') + '&output=embed';
                }
                abrir.href = 'https://www.google.com/maps/search/?api=1&query=' + q;
                legenda.textContent = busca ? 'Mostrando: ' + botao.textContent.trim().toLowerCase() + ' perto do imóvel' : 'Mostrando: localização do imóvel';
                painel.querySelectorAll('.anuncio-mapa-filtro').forEach(function (outro) {
                    outro.setAttribute('aria-pressed', String(outro === botao));
                });
            });
        });
    }
})();
