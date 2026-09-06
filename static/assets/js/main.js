import { onsiteImages, founderImages, eventImages } from "../config/images.js";
import { initNavbar } from "./navbar.js";
import { initScrollers } from "./scroller.js";
import { initImpactCounters } from "./counter.js";

function renderActivities() {
  const track = document.querySelector("[data-activities-track]");
  if (!track) return;
  track.innerHTML = onsiteImages
    .map(
      (img) => `
      <li class="activity-card">
        <img src="${img.src}" alt="${img.alt}" loading="lazy" decoding="async" width="600" height="450" />
      </li>`
    )
    .join("");
}

function renderFounders() {
  const track = document.querySelector("[data-founders-track]");
  if (!track) return;
  track.innerHTML = founderImages
    .map(
      (f) => `
      <li class="founder-card">
        <div class="founder-card__photo">
          <img src="${f.src}" alt="${f.alt}" loading="lazy" decoding="async" width="480" height="480" />
        </div>
        <h3>${f.name}</h3>
        <p>${f.role}</p>
      </li>`
    )
    .join("");
}

function renderEventImages() {
  document.querySelectorAll("[data-event-image]").forEach((el, i) => {
    const img = eventImages[i];
    if (!img) return;
    el.src = img.src;
    el.alt = img.alt;
  });
}

function boot() {
  renderActivities();
  renderFounders();
  renderEventImages();
  initNavbar();
  initScrollers();
  initImpactCounters();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
