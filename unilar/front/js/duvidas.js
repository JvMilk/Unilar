// Página Dúvidas: abre a caixa com o imóvel escolhido, filtra a lista e conta os caracteres.
(function () {
    const modal = document.getElementById('modalDuvida');
    if (!modal) return;
    const campoImovel = document.getElementById('modalDuvidaImovel');

    function preencher(botao) {
        if (!botao) return;
        document.getElementById('modalDuvidaTitulo').textContent = botao.dataset.titulo;
        document.getElementById('modalDuvidaLocal').textContent = botao.dataset.local;
        const imagem = document.getElementById('modalDuvidaImagem');
        imagem.src = botao.dataset.imagem;
        if (campoImovel && campoImovel.value !== botao.dataset.imovel) {
            campoImovel.value = botao.dataset.imovel;
        }
    }

    modal.addEventListener('show.bs.modal', function (evento) {
        const botao = evento.relatedTarget;
        if (botao && botao.classList.contains('resposta-nova')) {
            // Nova dúvida a partir de "Visualizar": começa com os campos em branco.
            const assunto = document.getElementById('duvidaAssunto');
            const texto = document.getElementById('duvidaMensagem');
            if (assunto) assunto.value = '';
            if (texto) { texto.value = ''; texto.dispatchEvent(new Event('input')); }
        }
        preencher(botao);
    });
    modal.addEventListener('shown.bs.modal', function () {
        const assunto = document.getElementById('duvidaAssunto');
        if (assunto) assunto.focus();
    });

    // Se o envio voltou com erro, reabre a caixa do mesmo imóvel com o texto digitado.
    if (modal.dataset.abrir) {
        const botao = document.querySelector('.duvida-imovel[data-imovel="' + CSS.escape(modal.dataset.abrir) + '"]');
        preencher(botao);
        bootstrap.Modal.getOrCreateInstance(modal).show();
    }

    const mensagem = document.getElementById('duvidaMensagem');
    const contador = document.getElementById('duvidaContador');
    if (mensagem && contador) {
        const atualizar = function () { contador.textContent = mensagem.value.length; };
        mensagem.addEventListener('input', atualizar);
        atualizar();
    }

    const busca = document.getElementById('buscaDuvidas');
    const vazio = document.getElementById('buscaVazia');
    const normalizar = function (texto) {
        return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    };
    if (busca) {
        busca.addEventListener('input', function () {
            const termo = normalizar(busca.value.trim());
            let visiveis = 0;
            document.querySelectorAll('#listaDuvidas .duvida-imovel').forEach(function (botao) {
                const texto = normalizar(botao.dataset.titulo + ' ' + botao.dataset.local);
                const mostrar = !termo || texto.includes(termo);
                botao.parentElement.hidden = !mostrar;
                if (mostrar) visiveis++;
            });
            vazio.hidden = visiveis > 0;
        });
    }
})();
