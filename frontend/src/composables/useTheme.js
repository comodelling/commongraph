import { ref, watch } from "vue";
import api from "../api/axios";

const currentTheme = ref(localStorage.getItem("theme") || "system");
const isDark = ref(false);

// Function to apply theme to the document
const applyTheme = (theme) => {
  if (theme === "system") {
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.body.classList.toggle("dark", systemPrefersDark);
    isDark.value = systemPrefersDark;
  } else {
    const darkMode = theme === "dark";
    document.body.classList.toggle("dark", darkMode);
    isDark.value = darkMode;
  }
};

// Initialize theme on module load
applyTheme(currentTheme.value);

// Listen for system theme changes when using "system" setting
const systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
systemThemeQuery.addEventListener("change", () => {
  if (currentTheme.value === "system") {
    applyTheme(currentTheme.value);
  }
});

export function useTheme() {
  // Watch for theme changes and persist them
  watch(currentTheme, async (newTheme) => {
    applyTheme(newTheme);
    localStorage.setItem("theme", newTheme);

    // Update user preferences if logged in
    const token = localStorage.getItem("accessToken");
    if (token) {
      try {
        await api.patch(
          "/users/preferences",
          { theme: newTheme },
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } catch (err) {
        console.warn("Failed to update theme preference:", err);
      }
    }
  });

  // Function to toggle between light and dark (skipping system)
  const toggleTheme = () => {
    if (currentTheme.value === "dark") {
      currentTheme.value = "light";
    } else {
      // If current theme is "light" or "system", switch to dark
      currentTheme.value = "dark";
    }
  };

  // Function to set theme directly
  const setTheme = (theme) => {
    if (["light", "dark", "system"].includes(theme)) {
      currentTheme.value = theme;
    }
  };

  // Function to load user's saved theme preference
  const loadUserTheme = async () => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      try {
        const response = await api.get("/users/me", {
          headers: { Authorization: `Bearer ${token}` }
        });
        const userTheme = response.data.preferences?.theme;
        if (userTheme && ["light", "dark", "system"].includes(userTheme)) {
          currentTheme.value = userTheme;
        }
      } catch (err) {
        console.warn("Failed to load user theme preference:", err);
      }
    }
  };

  return {
    currentTheme,
    isDark,
    toggleTheme,
    setTheme,
    applyTheme,
    loadUserTheme
  };
}
