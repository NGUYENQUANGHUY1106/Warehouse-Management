document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;

  document.querySelector("[data-sidebar-toggle]")?.addEventListener("click", () => {
    if (window.innerWidth <= 800) body.classList.toggle("is-menu-open");
    else body.classList.toggle("is-collapsed");
  });

  document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
    body.classList.toggle("is-dark");
  });

  const modal = document.getElementById("global-modal");
  const openModal = (title) => {
    if (!modal) return;
    modal.querySelector("#modal-title").textContent = title || "Thao tác mới";
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
  };
  const closeModal = () => {
    modal?.classList.remove("is-open");
    modal?.setAttribute("aria-hidden", "true");
  };
  document.querySelectorAll("[data-modal-open]").forEach((button) => {
    button.addEventListener("click", () => openModal(button.dataset.modalOpen));
  });
  document.querySelectorAll("[data-modal-close]").forEach((button) => button.addEventListener("click", closeModal));
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeModal(); });

  document.querySelectorAll("[data-tabs]").forEach((tabs) => {
    const buttons = tabs.querySelectorAll("[data-tab]");
    const panels = tabs.parentElement.querySelectorAll("[data-panel]");
    buttons.forEach((button) => button.addEventListener("click", () => {
      buttons.forEach((item) => item.classList.remove("is-active"));
      panels.forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      tabs.parentElement.querySelector(`[data-panel='${button.dataset.tab}']`)?.classList.add("is-active");
    }));
  });

  document.querySelectorAll("form[data-validate]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      let valid = true;
      form.querySelectorAll("[required]").forEach((input) => {
        input.classList.toggle("is-invalid", !input.value.trim());
        if (!input.value.trim()) valid = false;
      });
      if (valid) {
        const button = form.querySelector("[type='submit']");
        if (button) { const old = button.textContent; button.textContent = "Đã lưu ✓"; setTimeout(() => { button.textContent = old; closeModal(); }, 900); }
      }
    });
  });

  const chartDefaults = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: "#64748b", font: { size: 10 } } }, y: { grid: { color: "#e2e8f0" }, ticks: { display: false }, border: { display: false } } } };
  const dashboard = document.getElementById("dashboardChart");
  if (dashboard && window.Chart) new Chart(dashboard, { type: "line", data: { labels: ["T2", "T3", "T4", "T5", "T6", "T7", "CN"], datasets: [{ data: [18, 34, 27, 55, 42, 68, 59], borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.08)", fill: true, tension: 0, pointRadius: 0, borderWidth: 3 }] }, options: chartDefaults });
  const reports = document.getElementById("reportsChart");
  if (reports && window.Chart) new Chart(reports, { type: "bar", data: { labels: ["T5", "T6", "T7", "T8", "T9", "T10"], datasets: [{ label: "Doanh thu", data: [32, 39, 45, 52, 58, 68], backgroundColor: "#2563eb", borderRadius: 7 }, { label: "Lợi nhuận", data: [12, 16, 19, 24, 28, 33], backgroundColor: "#10b981", borderRadius: 7 }] }, options: { ...chartDefaults, plugins: { legend: { display: true, labels: { usePointStyle: true, boxWidth: 8 } } } } });
});
