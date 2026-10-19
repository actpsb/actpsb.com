// Progressive enhancement entry point. The site is fully usable without it.
document.documentElement.classList.add("js");

// Responsive navigation: below 1024px the link list collapses behind a native button.
(function () {
  var nav = document.querySelector(".site-nav");
  var toggle = nav && nav.querySelector(".nav-toggle");
  var menu = nav && nav.querySelector(".nav-menu");
  if (!toggle || !menu) return;

  var desktop = window.matchMedia("(min-width: 1024px)");
  var open = false;

  function render() {
    if (desktop.matches) {
      toggle.hidden = true;
      menu.hidden = false;
      toggle.setAttribute("aria-expanded", "false");
      return;
    }
    toggle.hidden = false;
    menu.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  }

  function setOpen(next, returnFocus) {
    open = next;
    render();
    if (returnFocus) toggle.focus();
  }

  toggle.addEventListener("click", function () { setOpen(!open, false); });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && open && !desktop.matches) setOpen(false, true);
  });

  document.addEventListener("click", function (event) {
    if (open && !nav.contains(event.target)) setOpen(false, false);
  });

  document.addEventListener("focusin", function (event) {
    if (open && !nav.contains(event.target)) setOpen(false, false);
  });

  desktop.addEventListener("change", function () { open = false; render(); });
  render();
})();

// Scroll reveal for the approach steps. Steps stay visible unless observation starts successfully.
(function () {
  var steps = document.querySelectorAll(".approach__step");
  if (!steps.length || !("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  try {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    steps.forEach(function (step) { step.classList.add("reveal"); observer.observe(step); });
    // Safety net: never leave content hidden if intersection events do not arrive.
    window.setTimeout(function () {
      steps.forEach(function (step) { step.classList.add("is-visible"); });
    }, 3000);
  } catch (e) {
    steps.forEach(function (step) { step.classList.remove("reveal"); });
  }
})();
