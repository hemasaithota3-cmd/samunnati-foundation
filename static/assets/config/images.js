/**
 * SAMUNNATHI — Centralized Image Configuration
 * ---------------------------------------------
 * Replace paths below with real files. Keep filenames the same, or update
 * both the path here AND the file on disk. Nothing elsewhere in the code
 * needs to change.
 *
 * Folder map:
 *   static/assets/images/logo/       -> brand logo (nav + footer + hero mark)
 *   static/assets/images/onsite/     -> "Recent Activities" auto-scroll strip
 *   static/assets/images/founders/   -> "Meet Our Co-Founders" auto-scroll strip
 *   static/assets/images/events/     -> "Upcoming Events" cards
 */

export const logo = {
  nav: {
    webp: "/static/assets/images/logo/logo-nav.webp",
    png: "/static/assets/images/logo/logo-nav.png",
  },
  large: {
    webp: "/static/assets/images/logo/logo-lg.webp",
    png: "/static/assets/images/logo/logo-lg.png",
  },
};

// heroImage intentionally left NONE — the hero uses typography + brand shapes only.
export const heroImage = null;

export const onsiteImages = [
  { src: "/static/assets/images/onsite/onsite-1.svg", alt: "Samunnathi mentors leading a classroom career-guidance session" },
  { src: "/static/assets/images/onsite/onsite-2.svg", alt: "Students participating in a Samunnathi workshop" },
  { src: "/static/assets/images/onsite/onsite-3.svg", alt: "A Samunnathi volunteer guiding a student through college applications" },
  { src: "/static/assets/images/onsite/onsite-4.svg", alt: "Students at a Samunnathi outreach event" },
  { src: "/static/assets/images/onsite/onsite-5.svg", alt: "A mentorship session at a partner school" },
  { src: "/static/assets/images/onsite/onsite-6.svg", alt: "Samunnathi team distributing educational resources" },
];

export const founderImages = [
  { src: "/static/assets/images/founders/founder-1.svg", alt: "Photo of Co-Founder 1", name: "Founder Name 1", role: "Co-Founder" },
  { src: "/static/assets/images/founders/founder-2.svg", alt: "Photo of Co-Founder 2", name: "Founder Name 2", role: "Co-Founder" },
  { src: "/static/assets/images/founders/founder-3.svg", alt: "Photo of Co-Founder 3", name: "Founder Name 3", role: "Co-Founder" },
  { src: "/static/assets/images/founders/founder-4.svg", alt: "Photo of Co-Founder 4", name: "Founder Name 4", role: "Co-Founder" },
  { src: "/static/assets/images/founders/founder-5.svg", alt: "Photo of Co-Founder 5", name: "Founder Name 5", role: "Co-Founder" },
];

export const eventImages = [
  { src: "/static/assets/images/events/event-1.svg", alt: "Photo from upcoming event 1" },
  { src: "/static/assets/images/events/event-2.svg", alt: "Photo from upcoming event 2" },
  { src: "/static/assets/images/events/event-3.svg", alt: "Photo from upcoming event 3" },
];