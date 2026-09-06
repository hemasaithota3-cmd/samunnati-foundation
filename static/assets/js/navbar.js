/**
 * Mobile navigation drawer.
 * Vanilla JS, no dependencies. Traps focus lightly and restores it on close.
 */
export function initNavbar() {
  const toggle = document.querySelector("[data-nav-toggle]");
  const closeBtn = document.querySelector("[data-nav-close]");
  const drawer = document.querySelector("[data-nav-drawer]");
  const scrim = document.querySelector("[data-nav-scrim]");
  const panel = document.querySelector("[data-nav-panel]");
  if (!toggle || !drawer || !panel) return;

  let lastFocused = null;

  const open = () => {
    lastFocused = document.activeElement;
    drawer.setAttribute("data-open", "true");
    toggle.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    const firstLink = panel.querySelector("a, button");
    firstLink?.focus();
  };

  const close = () => {
    drawer.setAttribute("data-open", "false");
    toggle.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    (lastFocused || toggle).focus();
  };

  toggle.addEventListener("click", open);
  closeBtn?.addEventListener("click", close);
  scrim?.addEventListener("click", close);

  drawer.addEventListener("keydown", (e) => {
    if (e.key === "Escape") close();
  });

  panel.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", close);
  });
}
