/* BW huisstijlpagina: menu, submenus, version switch, copy colour.
   All visible text comes from the HTML (built from src/copy/<lang>.json). */
(function () {
  "use strict";

  var mobileMenu = window.matchMedia("(max-width: 59.99em)");

  /* Disclosures: language list and submenus */
  var disclosures = Array.prototype.slice.call(document.querySelectorAll("[data-disclosure]"));

  function setOpen(item, open) {
    var btn = item.querySelector("button[aria-expanded]");
    item.classList.toggle("is-open", open);
    btn.setAttribute("aria-expanded", String(open));
  }

  disclosures.forEach(function (item) {
    var btn = item.querySelector("button[aria-expanded]");
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") !== "true";
      // On desktop only one dropdown is open at a time
      if (!mobileMenu.matches || item.classList.contains("lang")) {
        disclosures.forEach(function (other) {
          if (other !== item) setOpen(other, false);
        });
      }
      setOpen(item, open);
    });
    // Close a desktop dropdown when focus leaves it
    item.addEventListener("focusout", function (e) {
      if (mobileMenu.matches && !item.classList.contains("lang")) return;
      if (!item.contains(e.relatedTarget)) setOpen(item, false);
    });
  });

  /* Mobile menu */
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("main-nav");

  function setMenu(open) {
    toggle.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("is-open", open);
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setMenu(toggle.getAttribute("aria-expanded") !== "true");
    });
    mobileMenu.addEventListener("change", function () {
      setMenu(false);
    });
  }

  document.addEventListener("click", function (e) {
    disclosures.forEach(function (item) {
      if (!item.contains(e.target) && (!mobileMenu.matches || item.classList.contains("lang"))) {
        setOpen(item, false);
      }
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    disclosures.forEach(function (item) {
      if (item.classList.contains("is-open")) {
        setOpen(item, false);
        if (item.contains(document.activeElement)) item.querySelector("button").focus();
      }
    });
    if (toggle && toggle.getAttribute("aria-expanded") === "true") {
      setMenu(false);
      toggle.focus();
    }
  });

  /* Logo version: with baseline or mark only */
  var switcher = document.querySelector("[data-version-switch]");
  if (switcher) {
    switcher.addEventListener("change", function (e) {
      var version = e.target.value; // "logo" or "mark"
      document.querySelectorAll(".variant").forEach(function (card) {
        var img = card.querySelector(".variant__preview img");
        img.src = img.getAttribute("src").replace(/[^/]+$/, img.dataset[version]);
        img.alt = img.dataset[version === "logo" ? "altLogo" : "altMark"];
        card.querySelectorAll(".fmt").forEach(function (link) {
          var file = link.dataset[version];
          link.setAttribute("href", link.getAttribute("href").replace(/[^/]+$/, file));
          link.setAttribute("download", file);
        });
      });
    });
  }

  /* Copy HEX */
  var status = document.querySelector("[data-copy-status]");

  function announce(text) {
    if (!status) return;
    status.textContent = "";
    window.setTimeout(function () { status.textContent = text; }, 50);
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var value = btn.dataset.copy;
      var done = function () {
        btn.classList.add("is-done");
        announce(value + " " + status.dataset.copied);
        window.setTimeout(function () { btn.classList.remove("is-done"); }, 1600);
      };
      var fail = function () { announce(status.dataset.failed); };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(value).then(done, fail);
      } else {
        fail();
      }
    });
  });
})();
