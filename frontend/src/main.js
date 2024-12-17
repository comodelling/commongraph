import { createApp } from "vue";
import App from "./App.vue";
import router from "./router"; // Importing the router we created
import "./assets/styles.css";

const app = createApp(App);

app.use(router); // Use the router with the application

app.mount("#app"); // Mount the app
