/**
 * Seamless infinite auto-scroll strips (Recent Activities + Co-Founders).
 * Approach: duplicate the track's children once so translating -50% loops
 * with no visible jump. Pure CSS transform animation (see scroller.css) -
 * this script only prepares the DOM, it does not drive the animation loop.
 */
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

export function initScrollers() {
  document.querySelectorAll("[data-scroller]").forEach((scroller) => {
    const track = scroller.querySelector("[data-scroller-track]");
    if (!track) return;

    if (prefersReducedMotion.matches) {
      // Leave content as-is: a single, manually-scrollable row. No duplication needed.
      return;
    }

    // Duplicate children for a seamless loop.
    const originalChildren = Array.from(track.children);
    originalChildren.forEach((child) => {
      const clone = child.cloneNode(true);
      clone.setAttribute("aria-hidden", "true");
      // Cloned images are decorative duplicates; prevent duplicate tab stops.
      clone.querySelectorAll("a, button").forEach((el) => el.setAttribute("tabindex", "-1"));
      track.appendChild(clone);
    });

    // Tune duration relative to content width so speed feels consistent
    // regardless of how many cards are in a given strip.
    const speedPxPerSecond = scroller.dataset.speed ? Number(scroller.dataset.speed) : 45;
    requestAnimationFrame(() => {
      const singleSetWidth = track.scrollWidth / 2;
      const duration = Math.max(18, singleSetWidth / speedPxPerSecond);
      track.style.setProperty("--scroll-duration", `${duration}s`);
    });
  });
}
