const tg = window.Telegram.WebApp;
tg.expand();

async function loadRoutes() {
    const res = await fetch("/api/routes");
    const data = await res.json();

    const ul = document.getElementById("routes");
    ul.innerHTML = "";

    data.forEach(r => {
        const li = document.createElement("li");
        li.textContent = `${r.route} — ${r.address}`;
        ul.appendChild(li);
    });
}
