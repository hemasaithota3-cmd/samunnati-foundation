/**
 * Progressive-enhancement only. The server re-validates everything - this
 * just gives faster feedback and stops accidental double submits.
 */
export function initFormEnhancements() {
  document.querySelectorAll("form[data-validate]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        form.reportValidity();
        return;
      }
      const submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText = submitBtn.textContent;
        submitBtn.textContent = "Submitting…";
      }
    });
  });

  // Resume file size hint (client-side only; server enforces the real limit).
  document.querySelectorAll('input[type="file"][data-max-mb]').forEach((input) => {
    input.addEventListener("change", () => {
      const maxBytes = Number(input.dataset.maxMb) * 1024 * 1024;
      const feedback = input.closest(".file-drop")?.querySelector("[data-file-feedback]");
      if (!input.files.length || !feedback) return;
      const file = input.files[0];
      if (file.size > maxBytes) {
        feedback.textContent = "This file is larger than 5 MB — please choose a smaller file.";
        feedback.style.color = "#A32626";
      } else {
        feedback.textContent = `Selected: ${file.name}`;
        feedback.style.color = "";
      }
    });
  });

  if (window.location.hash === "#form" || document.body.dataset.scrollToForm === "true") {
    document.querySelector(".form-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initFormEnhancements);
} else {
  initFormEnhancements();
}
