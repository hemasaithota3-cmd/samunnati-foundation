/**
 * Count-up effect for the Impact section.
 * Triggers once per element when it enters the viewport. No animation
 * library - a single requestAnimationFrame loop per stat.
 */
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function animateCount(el) {
  const target = Number(el.dataset.countTo || "0");
  const suffix = el.dataset.suffix || "";
  if (prefersReducedMotion.matches || target === 0) {
    el.textContent = `${target}${suffix}`;
    return;
  }

  const duration = 1200;
  const start = performance.now();

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = Math.round(eased * target);
    el.textContent = `${value}${suffix}`;
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

export function initImpactCounters() {
  const stats = document.querySelectorAll("[data-count-to]");
  if (!stats.length) return;

  if (!("IntersectionObserver" in window)) {
    stats.forEach(animateCount);
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.4 }
  );

  stats.forEach((el) => observer.observe(el));
}
