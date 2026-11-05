document.addEventListener('submit', (event) => {
    if (!event.target.matches('.interesse-demo')) return;
    event.preventDefault();
    event.target.querySelector('[role="status"]').textContent =
        'Demonstração concluída. Nenhum contato foi enviado.';
});
