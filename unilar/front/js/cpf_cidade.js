// Máscara de CPF (000.000.000-00) e lista de cidades por estado (API pública do IBGE).
(function () {
    function mascararCpf(valor) {
        const d = valor.replace(/\D/g, '').slice(0, 11);
        if (d.length > 9) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
        if (d.length > 6) return d.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
        if (d.length > 3) return d.replace(/(\d{3})(\d{1,3})/, '$1.$2');
        return d;
    }

    function cpfValido(valor) {
        const d = valor.replace(/\D/g, '');
        if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false;
        for (const tamanho of [9, 10]) {
            let soma = 0;
            for (let i = 0; i < tamanho; i++) soma += Number(d[i]) * (tamanho + 1 - i);
            if ((soma * 10 % 11) % 10 !== Number(d[tamanho])) return false;
        }
        return true;
    }

    document.querySelectorAll('input[name="cpf"]').forEach(function (input) {
        input.value = mascararCpf(input.value);
        input.addEventListener('input', function () {
            input.value = mascararCpf(input.value);
            input.setCustomValidity('');
        });
        input.addEventListener('blur', function () {
            const completo = input.value.replace(/\D/g, '').length === 11;
            input.setCustomValidity(completo && !cpfValido(input.value) ? 'CPF inválido. Confira os números digitados.' : '');
            if (completo) input.reportValidity();
        });
    });

    const uf = document.querySelector('select[name="uf"]');
    const cidade = document.querySelector('select[name="cidade"]');
    if (!uf || !cidade) return;

    function opcao(texto, valor) {
        const o = document.createElement('option');
        o.textContent = texto;
        o.value = valor;
        return o;
    }

    let listaLocal = null;

    // Usa a lista salva no projeto; se ela não existir, consulta a API do IBGE.
    async function nomesDasCidades(sigla) {
        if (listaLocal === null && cidade.dataset.municipios) {
            try {
                const resposta = await fetch(cidade.dataset.municipios);
                listaLocal = resposta.ok ? await resposta.json() : false;
            } catch (erro) { listaLocal = false; }
        }
        if (listaLocal && listaLocal[sigla]) return listaLocal[sigla];
        const resposta = await fetch('https://servicodados.ibge.gov.br/api/v1/localidades/estados/' + sigla + '/municipios?orderBy=nome');
        if (!resposta.ok) throw new Error();
        return (await resposta.json()).map(function (m) { return m.nome; });
    }

    async function carregarCidades(selecionada) {
        cidade.replaceChildren(opcao(uf.value ? 'Carregando cidades...' : 'Selecione o estado primeiro', ''));
        cidade.disabled = true;
        if (!uf.value) return;
        try {
            const nomes = await nomesDasCidades(uf.value);
            cidade.replaceChildren(opcao('Selecione a cidade', ''));
            nomes.forEach(function (nome) { cidade.append(opcao(nome, nome)); });
            if (selecionada) cidade.value = selecionada;
            cidade.disabled = false;
            cidade.dispatchEvent(new Event('change'));
        } catch (erro) {
            cidade.replaceChildren(opcao('Não foi possível carregar as cidades. Recarregue a página.', ''));
        }
    }

    uf.addEventListener('change', function () { carregarCidades(''); });
    carregarCidades(cidade.dataset.selecionada || '');

    // Lista estilizada com busca: o <select> original continua no formulário (envio e validação),
    // mas fica escondido e é controlado por um botão + painel com campo de busca.
    function normalizar(texto) {
        return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    }

    function estilizar(select, textoBusca) {
        const campo = select.closest('.cad-campo');
        campo.classList.add('seletor');
        select.classList.add('visually-hidden');
        select.tabIndex = -1;

        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'seletor-botao';
        botao.setAttribute('aria-haspopup', 'listbox');
        botao.setAttribute('aria-expanded', 'false');
        const rotulo = document.createElement('b');
        const seta = document.createElement('i');
        seta.className = 'bi bi-chevron-down';
        seta.setAttribute('aria-hidden', 'true');
        botao.append(rotulo, seta);
        select.after(botao);

        const painel = document.createElement('div');
        painel.className = 'seletor-painel';
        painel.hidden = true;
        const busca = document.createElement('input');
        busca.type = 'search';
        busca.className = 'seletor-busca';
        busca.placeholder = textoBusca;
        busca.autocomplete = 'off';
        const lista = document.createElement('ul');
        lista.className = 'seletor-lista';
        lista.setAttribute('role', 'listbox');
        painel.append(busca, lista);
        campo.append(painel);

        let ativo = -1;

        function atualizarBotao() {
            const escolhida = select.selectedOptions[0];
            const temValor = Boolean(select.value);
            rotulo.textContent = escolhida ? escolhida.textContent : '';
            botao.classList.toggle('vazio', !temValor);
            botao.disabled = select.disabled;
        }

        function itens() { return [...lista.querySelectorAll('li[role="option"]')]; }

        function marcarAtivo(indice) {
            const todos = itens();
            if (!todos.length) return;
            ativo = Math.max(0, Math.min(indice, todos.length - 1));
            todos.forEach(function (li, i) { li.classList.toggle('ativo', i === ativo); });
            todos[ativo].scrollIntoView({ block: 'nearest' });
        }

        function montarLista() {
            const termo = normalizar(busca.value);
            lista.replaceChildren();
            ativo = -1;
            [...select.options].forEach(function (opcaoOriginal) {
                if (!opcaoOriginal.value) return;
                if (termo && !normalizar(opcaoOriginal.textContent).includes(termo)) return;
                const li = document.createElement('li');
                li.setAttribute('role', 'option');
                li.dataset.valor = opcaoOriginal.value;
                li.textContent = opcaoOriginal.textContent;
                li.setAttribute('aria-selected', String(opcaoOriginal.value === select.value));
                lista.append(li);
            });
            if (!lista.children.length) {
                const vazio = document.createElement('li');
                vazio.className = 'seletor-vazio';
                vazio.textContent = 'Nenhum resultado encontrado';
                lista.append(vazio);
            }
        }

        function abrir() {
            if (select.disabled) return;
            document.querySelectorAll('.seletor-painel').forEach(function (p) {
                if (p !== painel && !p.hidden) p.dispatchEvent(new Event('fechar'));
            });
            busca.value = '';
            montarLista();
            painel.hidden = false;
            botao.setAttribute('aria-expanded', 'true');
            const selecionado = itens().findIndex(function (li) { return li.dataset.valor === select.value; });
            if (selecionado >= 0) marcarAtivo(selecionado);
            busca.focus();
        }

        function fechar(focarBotao) {
            painel.hidden = true;
            botao.setAttribute('aria-expanded', 'false');
            if (focarBotao) botao.focus();
        }

        function escolher(valor) {
            campo.classList.remove('invalido');
            select.value = valor;
            select.setCustomValidity('');
            select.dispatchEvent(new Event('change', { bubbles: true }));
            atualizarBotao();
            fechar(true);
        }

        painel.addEventListener('fechar', function () { fechar(false); });
        botao.addEventListener('click', function () { painel.hidden ? abrir() : fechar(true); });
        select.addEventListener('focus', function () { botao.focus(); });
        select.addEventListener('invalid', function () {
            campo.classList.add('invalido');
            botao.focus();
        });
        busca.addEventListener('input', function () { montarLista(); marcarAtivo(0); });
        busca.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown') { e.preventDefault(); marcarAtivo(ativo + 1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); marcarAtivo(ativo - 1); }
            else if (e.key === 'Enter') {
                e.preventDefault();
                const item = itens()[ativo];
                if (item) escolher(item.dataset.valor);
            } else if (e.key === 'Escape') { e.preventDefault(); fechar(true); }
        });
        botao.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrir(); }
        });
        lista.addEventListener('click', function (e) {
            e.preventDefault(); // evita que o clique dentro do <label> ative o select escondido
            const li = e.target.closest('li[role="option"]');
            if (li) escolher(li.dataset.valor);
        });
        painel.addEventListener('click', function (e) { if (e.target === painel) e.preventDefault(); });
        document.addEventListener('click', function (e) {
            if (!painel.hidden && !campo.contains(e.target)) fechar(false);
        });

        new MutationObserver(atualizarBotao).observe(select, { childList: true, attributes: true, attributeFilter: ['disabled'] });
        select.addEventListener('change', atualizarBotao);
        atualizarBotao();
    }

    estilizar(uf, 'Buscar estado...');
    estilizar(cidade, 'Buscar cidade...');
})();
