/* AI 推特日报 - Calendar App */

(function () {
  "use strict";

  // State
  let digests = {};        // { "2026-02-11": { title, summary, html } }
  let currentYear;
  let currentMonth;        // 0-indexed
  let selectedDate = null;

  // DOM refs
  const calendarGrid = document.getElementById("calendarGrid");
  const currentMonthEl = document.getElementById("currentMonth");
  const prevBtn = document.getElementById("prevMonth");
  const nextBtn = document.getElementById("nextMonth");
  const themeToggle = document.getElementById("themeToggle");
  const digestPanel = document.getElementById("digestPanel");
  const digestPlaceholder = document.getElementById("digestPlaceholder");
  const digestContent = document.getElementById("digestContent");
  const digestDate = document.getElementById("digestDate");
  const digestSummary = document.getElementById("digestSummary");
  const digestBody = document.getElementById("digestBody");
  const closeDigest = document.getElementById("closeDigest");

  // ===== Theme =====

  function initTheme() {
    const saved = localStorage.getItem("theme");
    if (saved) {
      document.documentElement.setAttribute("data-theme", saved);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  }

  // ===== Data Loading =====

  async function loadDigests() {
    try {
      const resp = await fetch("data/digests.json");
      const data = await resp.json();
      data.forEach(function (d) {
        digests[d.date] = d;
      });
      // Navigate to the most recent digest's month, or current month
      if (data.length > 0) {
        const latest = data[data.length - 1].date;
        const parts = latest.split("-");
        currentYear = parseInt(parts[0]);
        currentMonth = parseInt(parts[1]) - 1;
      }
      renderCalendar();
    } catch (e) {
      console.error("Failed to load digests:", e);
    }
  }

  // ===== Calendar Rendering =====

  function renderCalendar() {
    // Clear day cells (keep weekday headers)
    var cells = calendarGrid.querySelectorAll(".day-cell");
    cells.forEach(function (c) { c.remove(); });

    // Update month label
    var monthNames = [
      "1月", "2月", "3月", "4月", "5月", "6月",
      "7月", "8月", "9月", "10月", "11月", "12月"
    ];
    currentMonthEl.textContent = currentYear + "年" + monthNames[currentMonth];

    // Calendar math
    var firstDay = new Date(currentYear, currentMonth, 1);
    var daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    // Monday = 0, Sunday = 6 (ISO week)
    var startDow = (firstDay.getDay() + 6) % 7;

    var today = new Date();
    var todayStr = formatDate(today.getFullYear(), today.getMonth(), today.getDate());

    // Empty cells before first day
    for (var i = 0; i < startDow; i++) {
      var empty = document.createElement("div");
      empty.className = "day-cell empty";
      calendarGrid.appendChild(empty);
    }

    // Day cells
    for (var d = 1; d <= daysInMonth; d++) {
      var dateStr = formatDate(currentYear, currentMonth, d);
      var cell = document.createElement("div");
      cell.className = "day-cell";
      cell.textContent = d;

      if (dateStr === todayStr) {
        cell.classList.add("today");
      }

      if (digests[dateStr]) {
        cell.classList.add("has-digest");
        var dot = document.createElement("span");
        dot.className = "dot";
        cell.appendChild(dot);
        cell.setAttribute("data-date", dateStr);
        cell.addEventListener("click", onDayClick);
      }

      if (dateStr === selectedDate) {
        cell.classList.add("selected");
      }

      calendarGrid.appendChild(cell);
    }
  }

  function formatDate(y, m, d) {
    return y + "-" + String(m + 1).padStart(2, "0") + "-" + String(d).padStart(2, "0");
  }

  // ===== Digest Display =====

  function onDayClick(e) {
    var cell = e.currentTarget;
    var dateStr = cell.getAttribute("data-date");
    showDigest(dateStr);
  }

  function showDigest(dateStr) {
    var d = digests[dateStr];
    if (!d) return;

    selectedDate = dateStr;
    renderCalendar();

    // Format display date
    var parts = dateStr.split("-");
    digestDate.textContent = parseInt(parts[1]) + "月" + parseInt(parts[2]) + "日 " + d.title;

    if (d.summary) {
      digestSummary.textContent = d.summary;
      digestSummary.hidden = false;
    } else {
      digestSummary.hidden = true;
    }

    digestBody.innerHTML = d.html;
    digestPlaceholder.hidden = true;
    digestContent.hidden = false;

    // Scroll to digest on mobile
    if (window.innerWidth <= 480) {
      digestPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function hideDigest() {
    selectedDate = null;
    digestContent.hidden = true;
    digestPlaceholder.hidden = false;
    renderCalendar();
  }

  // ===== Navigation =====

  function goToPrevMonth() {
    currentMonth--;
    if (currentMonth < 0) {
      currentMonth = 11;
      currentYear--;
    }
    renderCalendar();
  }

  function goToNextMonth() {
    currentMonth++;
    if (currentMonth > 11) {
      currentMonth = 0;
      currentYear++;
    }
    renderCalendar();
  }

  // ===== Keyboard Navigation =====

  function onKeyDown(e) {
    if (e.key === "ArrowLeft") goToPrevMonth();
    else if (e.key === "ArrowRight") goToNextMonth();
    else if (e.key === "Escape") hideDigest();
  }

  // ===== Init =====

  function init() {
    var now = new Date();
    currentYear = now.getFullYear();
    currentMonth = now.getMonth();

    initTheme();
    loadDigests();

    themeToggle.addEventListener("click", toggleTheme);
    prevBtn.addEventListener("click", goToPrevMonth);
    nextBtn.addEventListener("click", goToNextMonth);
    closeDigest.addEventListener("click", hideDigest);
    document.addEventListener("keydown", onKeyDown);
  }

  init();
})();
