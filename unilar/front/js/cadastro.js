const form = document.querySelector('.cad-form');
const etapas = [...form.querySelectorAll('fieldset')];
const indicadores = [...document.querySelectorAll('.cad-progresso li')];
const voltar = form.querySelector('.cad-voltar');
let etapa = 0;
function mostrar(indice) {
    etapa = indice;
    etapas.forEach((campo, i) => campo.hidden = i !== indice);
    indicadores.forEach((item, i) => {
        if (i === indice) item.setAttribute('aria-current', 'step');
        else item.removeAttribute('aria-current');
    });
    document.querySelector('.cad-passo').textContent = 'PASSO ' + (indice + 1) + ' DE 3';
    voltar.hidden = indice === 0;
    form.querySelector('.cad-enviar span').textContent = indice === 1 ? 'Continuar' : 'Criar conta';
    if (indice === 2) {
        const resumo = form.querySelector('.cad-resumo');
        resumo.replaceChildren();
        for (const [campo, titulo] of Object.entries({nome:'Nome', email:'E-mail', endereco:'Endereço', cidade:'Cidade'})) {
            const dt = document.createElement('dt'), dd = document.createElement('dd');
            dt.textContent = titulo;
            dd.textContent = form.elements[campo].value;
            resumo.append(dt, dd);
        }
    }
}
form.noValidate = true;
mostrar(0);
voltar.addEventListener('click', () => mostrar(etapa - 1));
form.addEventListener('submit', event => {
    form.elements.confirmar.setCustomValidity(form.elements.senha.value === form.elements.confirmar.value ? '' : 'As senhas precisam ser iguais.');
    for (let i = 0; i <= etapa; i++) {
        const invalido = [...etapas[i].querySelectorAll('input, select')].find(input => !input.checkValidity());
        if (invalido) {
            event.preventDefault();
            mostrar(i);
            invalido.reportValidity();
            return;
        }
    }
    if (etapa < 2) {
        event.preventDefault();
        mostrar(etapa + 1);
    }
});
form.querySelectorAll('.cad-olho').forEach(button => button.addEventListener('click', () => {
    const input = button.previousElementSibling;
    input.type = input.type === 'password' ? 'text' : 'password';
    button.setAttribute('aria-label', input.type === 'password' ? 'Mostrar senha' : 'Ocultar senha');
}));
