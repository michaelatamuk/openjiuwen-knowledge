/* Difficulty filter + sort for question entries (client-side, per topic page). */
(function () {
  function init() {
    var root = document.querySelector("article.md-content__inner") || document.querySelector(".md-content");
    if (!root) return;

    var headings = Array.prototype.filter.call(root.querySelectorAll("h2"), function (h) {
      return /^\d+\.\s/.test((h.textContent || "").trim());
    });
    if (headings.length < 2) return;

    var boxes = [];
    headings.forEach(function (h, i) {
      var box = document.createElement("div");
      box.className = "q-entry";
      h.parentNode.insertBefore(box, h);
      box.appendChild(h);
      while (box.nextElementSibling && box.nextElementSibling.tagName !== "H2") {
        box.appendChild(box.nextElementSibling);
      }
      var badge = box.querySelector(".badge");
      box.dataset.difficulty = badge ? (badge.textContent || "").trim().toLowerCase() : "";
      box.dataset.order = String(i);
      boxes.push(box);
    });

    var bar = document.createElement("div");
    bar.className = "q-controls";
    var levels = ["all", "basic", "intermediate", "advanced"];
    levels.forEach(function (lvl) {
      var c = document.createElement("button");
      c.type = "button";
      c.className = "q-chip" + (lvl === "all" ? " active" : "");
      c.dataset.level = lvl;
      c.textContent = lvl.charAt(0).toUpperCase() + lvl.slice(1);
      c.addEventListener("click", function () { setFilter(lvl); });
      bar.appendChild(c);
    });

    var sortMode = "number";
    var sortBtn = document.createElement("button");
    sortBtn.type = "button";
    sortBtn.className = "q-chip q-sort";
    sortBtn.textContent = "Sort: number";
    sortBtn.addEventListener("click", function () {
      sortMode = sortMode === "number" ? "difficulty" : "number";
      sortBtn.textContent = "Sort: " + sortMode;
      sort(sortMode);
    });
    bar.appendChild(sortBtn);

    boxes[0].parentNode.insertBefore(bar, boxes[0]);

    function setFilter(level) {
      Array.prototype.forEach.call(bar.querySelectorAll(".q-chip[data-level]"), function (c) {
        c.classList.toggle("active", c.dataset.level === level);
      });
      boxes.forEach(function (b) {
        b.style.display = (level === "all" || b.dataset.difficulty === level) ? "" : "none";
      });
    }

    function sort(mode) {
      var rank = { basic: 0, intermediate: 1, advanced: 2 };
      var arr = boxes.slice();
      if (mode === "difficulty") {
        arr.sort(function (a, b) {
          var ra = rank[a.dataset.difficulty], rb = rank[b.dataset.difficulty];
          ra = ra === undefined ? 9 : ra; rb = rb === undefined ? 9 : rb;
          return ra - rb || (Number(a.dataset.order) - Number(b.dataset.order));
        });
      } else {
        arr.sort(function (a, b) { return Number(a.dataset.order) - Number(b.dataset.order); });
      }
      var parent = arr[0].parentNode;
      arr.forEach(function (b) { parent.appendChild(b); });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
