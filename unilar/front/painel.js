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
