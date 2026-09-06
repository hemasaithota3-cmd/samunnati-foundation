(function () {
  const bellCount = document.querySelector("[data-bell-count]");
  const toastContainer = document.querySelector("[data-toast-container]");
  const sidebar = document.querySelector("[data-admin-sidebar]");
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");

  sidebarToggle?.addEventListener("click", () => sidebar?.classList.toggle("open"));

  const pollUrl = document.body.dataset.notificationsPollUrl;
  const pollInterval = Number(document.body.dataset.notificationsPollInterval || 15000);
  if (!pollUrl) return;

  let knownIds = new Set();
  let firstRun = true;

  async function poll() {
    try {
      const res = await fetch(pollUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } });
      if (!res.ok) return;
      const data = await res.json();

      if (bellCount) {
        bellCount.textContent = data.unread_count;
        bellCount.style.display = data.unread_count > 0 ? "flex" : "none";
      }

      if (!firstRun) {
        const newOnes = data.latest.filter((n) => !n.is_read && !knownIds.has(n.id));
        newOnes.forEach((n) => showToast(n));
      }
      knownIds = new Set(data.latest.map((n) => n.id));
      firstRun = false;
    } catch (err) {
      // Silent fail - polling resumes on the next interval.
    }
  }

  function showToast(notification) {
    if (!toastContainer) return;
    const el = document.createElement("div");
    el.className = "toast";
    el.innerHTML = `<strong>${notification.title}</strong><br>${notification.message}`;
    el.style.cursor = "pointer";
    el.addEventListener("click", () => { window.location.href = notification.url; });
    toastContainer.appendChild(el);
    setTimeout(() => el.remove(), 8000);
  }

  poll();
  setInterval(poll, pollInterval);
})();
