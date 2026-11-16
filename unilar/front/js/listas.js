// Listas (<select>) no visual do site.
// O <select> original continua na página (aparência fechada, valor, envio e validação do formulário);
// só a lista de opções que abre ao clicar é trocada por um painel desenhado no estilo do UniLar.
// Para manter a lista nativa em algum campo, use <select data-nativo>.
(function () {
    'use strict';

    let atual = null;          // { select, painel, itens, ativo }
    let busca = '';
    let buscaTempo = 0;
    const MARGEM = 6;

    function deveEstilizar(select) {
        return select instanceof HTMLSelectElement
            && !select.multiple
            && select.size <= 1
            && !select.hasAttribute('data-nativo')
            && !select.classList.contains('visually-hidden')
            && !select.closest('.seletor');
    }

    function opcoesVisiveis(select) {
        return [...select.options].filter(function (opcao) { return !opcao.hidden; });
    }

    function montar(select) {
        const painel = document.createElement('div');
        painel.className = 'lista-suspensa';
        if (select.closest('.admin-page')) painel.classList.add('lista-suspensa-admin');
        const lista = document.createElement('ul');
        lista.setAttribute('role', 'listbox');
        lista.id = 'lista-suspensa-opcoes';
        const rotulo = select.getAttribute('aria-label') || (select.labels && select.labels[0] ? select.labels[0].textContent.trim() : '');
        if (rotulo) lista.setAttribute('aria-label', rotulo);
        painel.append(lista);

        const itens = [];
        let grupoAtual = null;
        opcoesVisiveis(select).forEach(function (opcao) {
            const grupo = opcao.parentElement instanceof HTMLOptGroupElement ? opcao.parentElement : null;
            if (grupo && grupo !== grupoAtual) {
                const titulo = document.createElement('li');
                titulo.className = 'lista-suspensa-grupo';
                titulo.setAttribute('role', 'presentation');
                titulo.textContent = grupo.label;
                lista.append(titulo);
            }
            grupoAtual = grupo;
            const li = document.createElement('li');
            li.setAttribute('role', 'option');
            li.id = 'lista-suspensa-opcao-' + itens.length;
            li.textContent = opcao.textContent;
            li.dataset.indice = String(opcao.index);
            const selecionada = opcao.index === select.selectedIndex;
            li.setAttribute('aria-selected', String(selecionada));
            if (selecionada) li.insertAdjacentHTML('beforeend', '<i class="bi bi-check2" aria-hidden="true"></i>');
            if (opcao.disabled || (grupo && grupo.disabled)) li.setAttribute('aria-disabled', 'true');
            lista.append(li);
            itens.push(li);
        });
        return { painel: painel, lista: lista, itens: itens };
    }

    function posicionar() {
        if (!atual) return;
        const caixa = atual.select.getBoundingClientRect();
        const painel = atual.painel;
        if (caixa.bottom < 0 || caixa.top > window.innerHeight) { fechar(false); return; }
        painel.style.minWidth = caixa.width + 'px';
        painel.style.maxWidth = Math.max(caixa.width, Math.min(420, window.innerWidth - 16)) + 'px';
        const altura = painel.offsetHeight;
        const abaixo = window.innerHeight - caixa.bottom - MARGEM - 8;
        const acima = caixa.top - MARGEM - 8;
        const paraCima = altura > abaixo && acima > abaixo;
        painel.classList.toggle('para-cima', paraCima);
        painel.style.maxHeight = Math.max(160, Math.min(320, paraCima ? acima : abaixo)) + 'px';
        const alturaFinal = painel.offsetHeight;
        painel.style.top = (paraCima ? caixa.top - MARGEM - alturaFinal : caixa.bottom + MARGEM) + 'px';
        const largura = painel.offsetWidth;
        painel.style.left = Math.max(8, Math.min(caixa.left, window.innerWidth - largura - 8)) + 'px';
    }

    function marcar(posicao, rolar) {
        if (!atual || !atual.itens.length) return;
        const total = atual.itens.length;
        let destino = Math.max(0, Math.min(posicao, total - 1));
        atual.ativo = destino;
        atual.itens.forEach(function (li, i) { li.classList.toggle('ativo', i === destino); });
        atual.select.setAttribute('aria-activedescendant', atual.itens[destino].id);
        if (rolar !== false) atual.itens[destino].scrollIntoView({ block: 'nearest' });
    }

    function mover(passo) {
        if (!atual) return;
        let i = atual.ativo;
        for (let tentativas = 0; tentativas < atual.itens.length; tentativas++) {
            i += passo;
            if (i < 0 || i >= atual.itens.length) return;
            if (atual.itens[i].getAttribute('aria-disabled') !== 'true') { marcar(i); return; }
        }
    }

    function abrir(select) {
        if (select.disabled) return;
        if (atual && atual.select === select) return;
        fechar(false);
        const montado = montar(select);
        atual = { select: select, painel: montado.painel, itens: montado.itens, ativo: -1 };
        document.body.append(montado.painel);
        select.setAttribute('aria-expanded', 'true');
        select.setAttribute('aria-controls', montado.lista.id);
        select.classList.add('lista-aberta');
        posicionar();
        const escolhida = montado.itens.findIndex(function (li) { return Number(li.dataset.indice) === select.selectedIndex; });
        marcar(escolhida >= 0 ? escolhida : 0);

        montado.painel.addEventListener('pointerdown', function (e) { e.preventDefault(); });
        montado.painel.addEventListener('pointermove', function (e) {
            const li = e.target.closest('li[role="option"]');
            if (li && li.getAttribute('aria-disabled') !== 'true') marcar(atual.itens.indexOf(li), false);
        });
        montado.painel.addEventListener('click', function (e) {
            const li = e.target.closest('li[role="option"]');
            if (!li || li.getAttribute('aria-disabled') === 'true') return;
            escolher(Number(li.dataset.indice));
        });
    }

    function fechar(focar) {
        if (!atual) return;
        const select = atual.select;
        atual.painel.remove();
        select.setAttribute('aria-expanded', 'false');
        select.removeAttribute('aria-activedescendant');
        select.removeAttribute('aria-controls');
        select.classList.remove('lista-aberta');
        atual = null;
        if (focar) select.focus({ preventScroll: true });
    }

    function escolher(indice) {
        if (!atual) return;
        const select = atual.select;
        const mudou = select.selectedIndex !== indice;
        select.selectedIndex = indice;
        fechar(true);
        if (mudou) {
            select.dispatchEvent(new Event('input', { bubbles: true }));
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function buscarPorLetra(tecla) {
        clearTimeout(buscaTempo);
        busca += tecla.toLocaleLowerCase('pt-BR');
        buscaTempo = setTimeout(function () { busca = ''; }, 600);
        const normal = function (t) { return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('pt-BR'); };
        const termo = normal(busca);
        const inicio = busca.length === 1 ? atual.ativo + 1 : atual.ativo;
        const ordem = atual.itens.slice(inicio).concat(atual.itens.slice(0, inicio));
        const achado = ordem.find(function (li) {
            return li.getAttribute('aria-disabled') !== 'true' && normal(li.textContent).startsWith(termo);
        });
        if (achado) marcar(atual.itens.indexOf(achado));
    }

    // ---- eventos (delegados, valem também para listas criadas depois) ----
    document.addEventListener('pointerdown', function (e) {
        const select = e.target instanceof Element ? e.target.closest('select') : null;
        if (select && deveEstilizar(select) && e.button === 0) {
            e.preventDefault();               // impede a lista nativa
            if (atual && atual.select === select) { fechar(true); return; }
            select.focus({ preventScroll: true });
            abrir(select);
            return;
        }
        if (atual && !atual.painel.contains(e.target)) fechar(false);
    }, true);

    // No iPhone/iPad a lista nativa abre no toque: cancelar o toque mantém só a nossa.
    document.addEventListener('touchend', function (e) {
        const select = e.target instanceof Element ? e.target.closest('select') : null;
        if (select && deveEstilizar(select)) e.preventDefault();
    }, { capture: true, passive: false });

    // Clique "sintético" (ex.: leitor de tela ou label) abre a nossa lista.
    document.addEventListener('click', function (e) {
        const select = e.target instanceof Element ? e.target.closest('select') : null;
        if (select && deveEstilizar(select) && e.detail === 0 && !atual) abrir(select);
    }, true);

    document.addEventListener('keydown', function (e) {
        const select = e.target;
        if (!(select instanceof HTMLSelectElement) || !deveEstilizar(select)) return;
        const aberta = atual && atual.select === select;
        if (!aberta) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'F4') {
                e.preventDefault();
                abrir(select);
            }
            return;
        }
        switch (e.key) {
            case 'ArrowDown': e.preventDefault(); mover(1); break;
            case 'ArrowUp': e.preventDefault(); mover(-1); break;
            case 'Home': e.preventDefault(); marcar(0); break;
            case 'End': e.preventDefault(); marcar(atual.itens.length - 1); break;
            case 'PageDown': e.preventDefault(); marcar(atual.ativo + 8); break;
            case 'PageUp': e.preventDefault(); marcar(atual.ativo - 8); break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (atual.ativo >= 0 && atual.itens[atual.ativo].getAttribute('aria-disabled') !== 'true') {
                    escolher(Number(atual.itens[atual.ativo].dataset.indice));
                }
                break;
            case 'Escape': e.preventDefault(); fechar(true); break;
            case 'Tab': fechar(false); break;
            default:
                if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    e.preventDefault();
                    buscarPorLetra(e.key);
                }
        }
    }, true);

    document.addEventListener('focusout', function (e) {
        if (atual && e.target === atual.select) {
            setTimeout(function () {
                if (atual && document.activeElement !== atual.select) fechar(false);
            }, 0);
        }
    });

    window.addEventListener('resize', function () { fechar(false); });
    window.addEventListener('scroll', function (e) {
        if (atual && !atual.painel.contains(e.target)) posicionar();
    }, true);

    // Marca as listas para tecnologias assistivas.
    function preparar(raiz) {
        (raiz.querySelectorAll ? raiz.querySelectorAll('select') : []).forEach(function (select) {
            if (deveEstilizar(select)) select.setAttribute('aria-expanded', 'false');
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { preparar(document); });
    } else {
        preparar(document);
    }
})();
