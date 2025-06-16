/* static/school/js/main.js */

// LOGIN-PAGE JS SCRIPTs
document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const form = document.getElementById("loginForm");
  const userIdInput = document.getElementById("userId");
  const passwordInput = document.getElementById("password");
  const toggleIcon = document.getElementById("toggleIcon");
  const togglePassword = document.getElementById("togglePassword");
  const errorMessage = document.getElementById("loginError");

  // LOGIN FORM HANDLER
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const id = userIdInput.value.trim();
      const pass = passwordInput.value;

      try {
        const response = await fetch("/api/school/login/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ id, pass }),
        });

        const data = await response.json();

        if (response.ok) {
          localStorage.setItem("token", data.token);
          localStorage.setItem("user_id", data.user_id);
          window.location.href = "/api/school/mark-view/";
        } else {
          errorMessage.textContent = data.error || "Login failed";
        }
      } catch (err) {
        console.error(err);
        errorMessage.textContent = "Server error";
      }
    });
  }

  // TOGGLE PASSWORD VISIBILITY
  if (togglePassword && passwordInput && toggleIcon) {
    togglePassword.addEventListener("click", () => {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";
      toggleIcon.classList.remove("fa-eye", "fa-eye-slash");
      toggleIcon.classList.add(isPassword ? "fa-eye-slash" : "fa-eye");
    });
  }

  // AUTO REDIRECT TO LOGIN IF USER NOT AUTHENTICATED
  const user = localStorage.getItem("user_id");
  const usernameEl = document.getElementById("username");
  if (!user) {
    window.location.href = "/api/school/login-page/";
  } else if (usernameEl) {
    usernameEl.textContent = user;
  }
});
