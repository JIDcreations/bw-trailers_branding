/* BW huisstijlpagina: version switch, copy colour.
   All visible text comes from the HTML (built from src/copy/<lang>.json). */
(function () {
  "use strict";

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
