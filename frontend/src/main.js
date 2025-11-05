import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { useConfig } from "./composables/useConfig";
import "./assets/styles.css";

const { load, nodeTypes } = useConfig();

async function bootstrap() {
  try {
    // Wait until the config is loaded once
    await load();

    const app = createApp(App);

    // Global error handler for URI and other errors
    app.config.errorHandler = (err, vm, info) => {
      console.error("Global error handler:", err, info);

      // Handle URI errors specifically
      if (err instanceof URIError || err.message?.includes("URI")) {
        console.warn("URI Error detected, redirecting to home");
        if (window.location.pathname !== "/") {
          window.location.href = "/";
        }
        return;
      }

      // Log other errors but don't crash the app
      console.error("Application error:", err);
    };

    // Handle unhandled promise rejections
    window.addEventListener("unhandledrejection", (event) => {
      console.error("Unhandled promise rejection:", event.reason);

      // Prevent default browser error handling for URI errors
      if (
        event.reason instanceof URIError ||
        event.reason?.message?.includes("URI")
      ) {
        event.preventDefault();
        console.warn("URI Error in promise, redirecting to home");
        if (window.location.pathname !== "/") {
          window.location.href = "/";
        }
      }
    });

    // Apply theme before mounting
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

    const userTheme = localStorage.getItem("theme") || "system";
    applyTheme(userTheme);

    app.use(router);
    app.mount("#app");
  } catch (error) {
    console.error("Bootstrap error:", error);

    // Fallback: show a basic error page
    document.body.innerHTML = `
      <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
        <h1>Application Error</h1>
        <p>Sorry, there was an error loading the application.</p>
        <button onclick="window.location.reload()">Reload Page</button>
      </div>
    `;
  }
}

bootstrap();
