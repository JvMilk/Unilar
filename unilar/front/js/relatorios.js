if (typeof Chart === 'function') {
    const linhas = JSON.parse(document.getElementById('report-data').textContent);
    const formatoMes = new Intl.DateTimeFormat('pt-BR', {
        month: 'short',
        year: '2-digit',
        timeZone: 'UTC',
    });
    const labels = linhas.map(({mes}) => formatoMes.format(new Date(mes)));

    function serie(campo, label, cor) {
        return {
            label,
            data: linhas.map(linha => linha[campo]),
            backgroundColor: cor,
            borderColor: cor,
            borderRadius: 5,
        };
    }

    function desenhar(id, type, datasets) {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        canvas.parentElement.hidden = false;
        new Chart(canvas, {
            type,
            data: {labels, datasets},
            options: {
                maintainAspectRatio: false,
                interaction: {mode: 'index', intersect: false},
                plugins: {legend: {display: datasets.length > 1, position: 'bottom'}},
                scales: {
                    x: {grid: {display: false}, ticks: {maxRotation: 0}},
                    y: {beginAtZero: true, ticks: {precision: 0}},
                },
            },
        });
    }

    desenhar('report-access-chart', 'line', [{
        ...serie('acessos', 'Acessos', '#315fdb'),
        backgroundColor: '#315fdb1a',
        fill: true,
        tension: 0.25,
    }]);
    desenhar('report-activity-chart', 'bar', [
        serie('duvidas', 'Dúvidas', '#6554ce'),
        serie('visitas', 'Pedidos de visita', '#3375de'),
        serie('alugueis', 'Aluguéis confirmados', '#238565'),
    ]);
}
