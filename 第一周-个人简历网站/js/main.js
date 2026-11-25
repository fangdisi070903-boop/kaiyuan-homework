(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  /* ---------- 主题切换 ---------- */
  var themeToggle = document.getElementById("theme-toggle");
  var themeLabel = themeToggle ? themeToggle.querySelector(".theme-label") : null;
  var storedTheme = null;

  try {
    storedTheme = localStorage.getItem("resume-theme");
  } catch (error) {
    storedTheme = null;
  }

  var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var theme = storedTheme || (prefersDark ? "dark" : "light");

  function applyTheme(value) {
    root.setAttribute("data-theme", value);
    if (themeLabel) {
      themeLabel.textContent = value === "dark" ? "浅色" : "深色";
    }
    if (themeToggle) {
      themeToggle.setAttribute("aria-pressed", value === "dark" ? "true" : "false");
    }
  }

  applyTheme(theme);

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      theme = theme === "dark" ? "light" : "dark";
      applyTheme(theme);
      try {
        localStorage.setItem("resume-theme", theme);
      } catch (error) {
        /* 隐私模式下无法写入，忽略即可 */
      }
    });
  }

  /* ---------- 移动端导航 ---------- */
  var navToggle = document.querySelector(".nav-toggle");
  var siteNav = document.getElementById("site-nav");

  function closeNav() {
    if (!siteNav || !navToggle) return;
    siteNav.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  }

  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () {
      var isOpen = siteNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    siteNav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") {
        closeNav();
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeNav();
    }
  });

  /* ---------- 导航高亮 ---------- */
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".site-nav a[href^='#']"));
  var sections = navLinks
    .map(function (link) {
      var id = link.getAttribute("href").slice(1);
      return document.getElementById(id);
    })
    .filter(Boolean);

  if ("IntersectionObserver" in window && sections.length) {
    var sectionObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          navLinks.forEach(function (link) {
            var isCurrent = link.getAttribute("href") === "#" + entry.target.id;
            link.classList.toggle("is-active", isCurrent);
          });
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );

    sections.forEach(function (section) {
      sectionObserver.observe(section);
    });
  }

  /* ---------- 年份 ---------- */
  var yearNode = document.getElementById("year");
  if (yearNode) {
    yearNode.textContent = String(new Date().getFullYear());
  }
})();
