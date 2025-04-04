document.addEventListener("DOMContentLoaded", function () {
    // Login Form Validation
    const loginForm = document.querySelector(".login-container form");
    if (loginForm) {
        loginForm.addEventListener("submit", function (e) {
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;
            if (!username || !password) {
                e.preventDefault();
                alert("Please fill in all fields.");
            }
        });
    }

    // Register Form Validation
    const registerForm = document.querySelector(".registration-container form");
    if (registerForm) {
        registerForm.addEventListener("submit", function (e) {
            const password = document.getElementById("password").value;
            if (password.length < 6) {
                e.preventDefault();
                alert("Password must be at least 6 characters.");
            }
        });
    }

    // Search Bar Interaction
    const searchBtn = document.querySelector(".search-btn");
    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            const searchInput = document.getElementById("search-input").value;
            if (searchInput) {
                alert(`Searching for: ${searchInput}`);
            } else {
                alert("Please enter a search term.");
            }
        });
    }

    // Button Hover Effects
    const buttons = document.querySelectorAll("button, .actions a, .medibuddy-btn, .service-btn, .cta-btn, .sidebar nav a");
    buttons.forEach(button => {
        button.addEventListener("mouseenter", () => {
            button.style.transform = "scale(1.05)";
        });
        button.addEventListener("mouseleave", () => {
            button.style.transform = "scale(1)";
        });
    });
});