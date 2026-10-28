(() => {
"use strict";
const $ = s => document.querySelector(s);
const app = $("#imovelApp"), backdrop = $("#modalBackdrop");
let previousFocus, toastTimer;
function showToast(message) {
    $("#toast").textContent = message;
    $("#toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 4500);
}
function openModal(title, html) {
    if (backdrop.hidden) previousFocus = document.activeElement;
    $("#modalTitle").textContent = title;
    $("#modalBody").innerHTML = html;
    backdrop.hidden = false;
    document.body.classList.add("imovel-aberto");
    $("#modalClose").focus();
}
function closeModal() {
    backdrop.hidden = true;
    document.body.classList.remove("imovel-aberto");
    previousFocus?.focus();
}
$("#modalClose").addEventListener("click", closeModal);
backdrop.addEventListener("click", e => { if (e.target === backdrop) closeModal(); });
document.addEventListener("keydown", e => {
    if (backdrop.hidden) return;
    if (e.key === "Escape") closeModal();
    if (e.key === "Tab") {
        const nodes = [...backdrop.querySelectorAll("button, input, textarea, select, a[href]")].filter(n => !n.disabled);
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
});
async function post(url, data) {
    const response = await fetch(url, {method: "POST", credentials: "same-origin",
        headers: {"X-CSRFToken": app.querySelector("[name=csrfmiddlewaretoken]").value, "Accept": "application/json"}, body: data});
    if (!response.headers.get("content-type")?.includes("application/json"))
        throw new Error("Não foi possível salvar. Recarregue a página e tente novamente.");
    const result = await response.json();
    if (!response.ok) throw new Error(Object.values(result.erros || {}).flat().map(e => e.message).join(" ") || "Não foi possível salvar.");
    return result;
}
function wireForm(id, url) {
    const form = $(id);
    form.addEventListener("submit", async e => {
        e.preventDefault();
        const button = form.querySelector("[type=submit]"), error = form.querySelector("[role=alert]");
        button.disabled = true; error.textContent = "";
        try {
            const result = await post(url, new FormData(form));
            openModal("Solicitação registrada", '<p id="resultMessage" role="status"></p><button class="primary" id="finishRequest" type="button">Concluir</button>');
            $("#resultMessage").textContent = result.mensagem;
            $("#finishRequest").addEventListener("click", closeModal);
        } catch (exception) { error.textContent = exception.message; }
        finally { button.disabled = false; }
    });
}
const thumbs = [...document.querySelectorAll(".thumbnails img")];
let photo = 0;
function showPhoto(i) {
    photo = (i + thumbs.length) % thumbs.length;
    $("#mainPhoto").src = thumbs[photo].dataset.full;
    $("#mainPhoto").alt = thumbs[photo].alt;
    thumbs.forEach((t, j) => t.classList.toggle("selected", j === photo));
    $("#photoCounter").textContent = `${photo + 1}/${thumbs.length}`;
}
thumbs.forEach((t, i) => {
    t.addEventListener("click", () => showPhoto(i));
    t.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showPhoto(i); } });
});
$("#prevPhoto").addEventListener("click", () => showPhoto(photo - 1));
$("#nextPhoto").addEventListener("click", () => showPhoto(photo + 1));
$("#morePhotos").addEventListener("click", () => {
    openModal("Fotos do imóvel", `<div class="modal-gallery">${thumbs.map((t, i) => `<button type="button" class="modal-thumb" data-index="${i}"><img src="${t.dataset.full}" alt="${t.alt}"><span>Foto ${i + 1}</span></button>`).join("")}</div>`);
    document.querySelectorAll(".modal-thumb").forEach(b => b.addEventListener("click", () => { showPhoto(Number(b.dataset.index)); closeModal(); }));
});
function updateFavorite(saved) {
    const b = $("#favoriteBtn");
    b.classList.toggle("is-favorite", saved);
    b.textContent = saved ? "♥" : "♡";
    b.setAttribute("aria-pressed", String(saved));
    b.setAttribute("aria-label", saved ? "Remover dos favoritos" : "Favoritar imóvel");
    b.title = b.getAttribute("aria-label");
}
updateFavorite(JSON.parse($("#favorito-inicial").textContent));
$("#favoriteBtn").addEventListener("click", async () => {
    $("#favoriteBtn").disabled = true;
    try {
        const result = await post(app.dataset.favoritoUrl, new FormData());
        updateFavorite(result.favorito);
        showToast(result.favorito ? "Imóvel salvo nos favoritos deste navegador." : "Imóvel removido dos favoritos.");
    } catch (e) { showToast(e.message); }
    finally { $("#favoriteBtn").disabled = false; }
});
const identity = '<label>Seu nome<input name="nome" maxlength="120" autocomplete="name" required></label><label>Seu e-mail<input name="email" type="email" maxlength="254" autocomplete="email" required></label>';
$("#contactBtn").addEventListener("click", () => {
    openModal("Entrar em contato", `<p class="modal-intro">Registre seu interesse na Kitnet no Centro.</p><form id="contactForm" class="modal-form">${identity}
    <label>Mensagem<textarea name="mensagem" maxlength="3000" rows="3" required>Olá! Tenho interesse na kitnet de R$ 750/mês. O imóvel ainda está disponível?</textarea></label>
    <p role="alert"></p><button class="primary" type="submit">Registrar interesse</button></form>
    <p class="form-note">Seu contato será salvo no UniLar. O envio de e-mail ao proprietário ainda não está disponível.</p>`);
    wireForm("#contactForm", app.dataset.contatoUrl);
});
$("#scheduleBtn").addEventListener("click", () => {
    const minDate = new Intl.DateTimeFormat("sv-SE", {timeZone: "America/Sao_Paulo"}).format(new Date());
    openModal("Agendar visita", `<p class="modal-intro">Escolha uma data e um horário de preferência.</p><form id="scheduleForm" class="modal-form">${identity}
    <label>Data<input name="data" type="date" min="${minDate}" required></label>
    <label>Horário<select name="horario" required><option value="">Selecione</option><option>09:00</option><option>10:00</option><option>11:00</option><option>14:00</option><option>15:00</option><option>16:00</option><option>17:00</option></select></label>
    <label>Observação<textarea name="observacao" maxlength="1000" rows="2"></textarea></label><p role="alert"></p>
    <button class="primary" type="submit">Solicitar visita</button></form>
    <p class="form-note">O pedido será salvo no UniLar. A visita depende de confirmação do proprietário.</p>`);
    wireForm("#scheduleForm", app.dataset.visitaUrl);
});
$("#ownerListingsBtn").addEventListener("click", () => {
    openModal("Imóveis de João Vitor", `<div class="listing-mini"><img src="${thumbs[0].dataset.full}" alt="Kitnet no Centro"><div><strong>Kitnet no Centro</strong><p>Rio Paranaíba - MG</p><b>R$ 750/mês</b></div></div><p class="form-note">Este é o único imóvel disponível nesta etapa do projeto.</p>`);
});
})();

