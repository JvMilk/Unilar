function mostrarSecaoPainel() {
    const secoes = [...document.querySelectorAll('.painel-secao')];
    const alvo = secoes.find(secao => '#' + secao.id === location.hash) || secoes[0];
    secoes.forEach(secao => { secao.hidden = secao !== alvo; });
    document.querySelectorAll('.painel-sidebar nav a').forEach(link => {
        const ativo = link.hash === '#' + alvo.id;
        link.classList.toggle('ativo', ativo);
        if (ativo) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
    });
}
window.addEventListener('hashchange', mostrarSecaoPainel);
mostrarSecaoPainel();

// Foto de perfil: mostra a imagem escolhida antes de salvar e confere o tamanho.
(function () {
    const entrada = document.getElementById('fotoArquivo');
    if (!entrada) return;
    const preview = document.getElementById('fotoPreview');
    const nome = document.getElementById('fotoNome');
    const salvar = document.getElementById('fotoSalvar');
    const erro = document.getElementById('fotoErro');
    entrada.addEventListener('change', function () {
        const arquivo = entrada.files[0];
        erro.hidden = true;
        salvar.disabled = true;
        if (!arquivo) { nome.textContent = 'Escolher foto'; return; }
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(arquivo.type)) {
            erro.textContent = 'Envie uma imagem JPG, PNG ou WEBP.';
            erro.hidden = false;
            entrada.value = '';
            return;
        }
        if (arquivo.size > 4 * 1024 * 1024) {
            erro.textContent = 'A imagem deve ter no máximo 4 MB.';
            erro.hidden = false;
            entrada.value = '';
            return;
        }
        nome.textContent = arquivo.name;
        const imagem = document.createElement('img');
        imagem.alt = 'Prévia da foto de perfil';
        imagem.src = URL.createObjectURL(arquivo);
        preview.replaceChildren(imagem);
        salvar.disabled = false;
    });
})();
