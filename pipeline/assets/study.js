/* Study mode: hide answers, reveal with one tap. Persists across pages. */
(function () {
  var KEY = "jiuwen-study-mode";

  function getMode() {
    try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; }
  }
  function setMode(v) {
    try { localStorage.setItem(KEY, v ? "1" : "0"); } catch (e) {}
    document.body.classList.toggle("study-on", v);
    updateBtn();
  }
  function updateBtn() {
    var b = document.getElementById("study-toggle");
    if (b) b.textContent = getMode() ? "Study mode: ON" : "Study mode: OFF";
  }

  function wrapQuestions() {
    var root = document.querySelector("article.md-content__inner") || document.querySelector(".md-content");
    if (!root) return;

    root.querySelectorAll("h2").forEach(function (h) {
      if (h.dataset.qaWrapped) return;
      if (!/^\d+\.\s/.test(h.textContent.trim())) return;

      var group = [], n = h.nextElementSibling;
      while (n && n.tagName !== "H2") { group.push(n); n = n.nextElementSibling; }
      if (!group.length) return;

      // Only treat as a Q&A card if the group actually contains a "General:" answer.
      var isQA = group.some(function (el) {
        return /^\s*General:/.test(el.textContent || "");
      });
      if (!isQA) return;

      h.dataset.qaWrapped = "1";
      var box = document.createElement("div");
      box.className = "qa-answer";
      h.parentNode.insertBefore(box, h.nextSibling);
      group.forEach(function (el) { box.appendChild(el); });

      var bar = document.createElement("button");
      bar.className = "qa-reveal";
      bar.type = "button";
      bar.textContent = "Show answer";
      box.parentNode.insertBefore(bar, box);
      bar.addEventListener("click", function () {
        var shown = box.classList.toggle("revealed");
        bar.textContent = shown ? "Hide answer" : "Show answer";
      });
    });
  }

  function addToggle() {
    if (document.getElementById("study-toggle")) return;
    var b = document.createElement("button");
    b.id = "study-toggle";
    b.className = "study-toggle";
    b.type = "button";
    b.addEventListener("click", function () { setMode(!getMode()); });
    document.body.appendChild(b);
    updateBtn();
  }

  function init() {
    addToggle();
    wrapQuestions();
    document.body.classList.toggle("study-on", getMode());
  }

  function schedule() {
    setTimeout(init, 250);
    setTimeout(init, 900);   // re-run after Mermaid finishes rendering
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule);
  } else {
    schedule();
  }
})();
