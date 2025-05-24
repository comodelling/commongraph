import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { useConfig } from "./composables/useConfig";
import "./assets/styles.css";

const { load, nodeTypes } = useConfig();

async function bootstrap() {
  // Wait until the config is loaded once
  await load();

  const app = createApp(App);

  // Apply theme before mounting
  const applyTheme = (theme) => {
    if (theme === "system") {
      const systemPrefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;
      document.body.classList.toggle("dark", systemPrefersDark);
    } else {
      document.body.classList.toggle("dark", theme === "dark");
    }
  };

  const userTheme = localStorage.getItem("theme") || "system";
  applyTheme(userTheme);

  app.use(router);
  app.mount("#app");
}

bootstrap();