/**
 * Online Quiz System - Client Interactions
 * Course: BBAT104 Fundamentals of Total Quality Management (AU-24-5942)
 * Quality Goal: Q08 - Improve User Satisfaction
 * Features Active: Theme Toggle (Feature 3) & Keyboard Shortcuts (Feature 4)
 */

(function () {
    "use strict";

    // -------------------------------------------------------------------------
    // 1. Theme Management (Light / Dark Mode Toggle - Quality Goal Q08)
    // -------------------------------------------------------------------------
    const THEME_STORAGE_KEY = "bbat104_quiz_theme";
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    const themeLabel = document.getElementById("themeLabel");

    function getPreferredTheme() {
        const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (storedTheme === "light" || storedTheme === "dark") {
            return storedTheme;
        }
        // Fall back to system color scheme preference
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return "dark";
        }
        return "light";
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem(THEME_STORAGE_KEY, theme);

        if (themeToggleBtn) {
            themeToggleBtn.setAttribute("aria-pressed", String(theme === "dark"));
        }

        if (themeIcon && themeLabel) {
            if (theme === "dark") {
                themeIcon.textContent = "☀️";
                themeLabel.textContent = "Light Mode";
            } else {
                themeIcon.textContent = "🌙";
                themeLabel.textContent = "Dark Mode";
            }
        }
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        applyTheme(newTheme);
    }

    // Initialize theme on page load
    const initialTheme = getPreferredTheme();
    applyTheme(initialTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", toggleTheme);
    }

    // -------------------------------------------------------------------------
    // 2. Keyboard Shortcuts (Quality Goal Q08 Feature 4)
    // -------------------------------------------------------------------------
    document.addEventListener("keydown", function (event) {
        const activeElement = document.activeElement;
        const isEditing = activeElement instanceof HTMLElement
            && (activeElement.isContentEditable
                || ["INPUT", "TEXTAREA", "SELECT"].includes(activeElement.tagName));
        if (isEditing || event.altKey || event.ctrlKey || event.metaKey || event.repeat) {
            return;
        }

        // Shortcut: Press 'T' or 't' to toggle theme
        if (event.key.toLowerCase() === "t") {
            event.preventDefault();
            toggleTheme();
        }
    });

    console.log("BBAT104 Online Quiz System (Phase 2 Shell Active) - Quality Goal Q08: Shortcuts & Theme Toggle initialized.");
})();
