import { createApp } from "vue";
import App from "./App.vue";
import router from "./router"; // Importing the router we created
import "./assets/styles.css";

const app = createApp(App);

const applyTheme = (theme) => {
  if (theme === "system") {
    const systemPrefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;
    document.body.classList.toggle("dark", systemPrefersDark);
  } else {
    document.body.classList.toggle("dark", theme === "dark");
  }
};

// Fetch the user's theme preference from localStorage or default to system
const userTheme = localStorage.getItem("theme") || "system";
applyTheme(userTheme);

app.use(router);
app.mount("#app");
