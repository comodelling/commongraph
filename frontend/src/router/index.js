import { createRouter, createWebHistory } from "vue-router";
import Layout from "../components/Layout.vue";
import MainPage from "../views/MainPage.vue";
import SearchPage from "../views/SearchPage.vue";
import Focus from "../views/ElementFocus.vue";
import About from "../views/About.vue";
import Login from "../views/Login.vue";
import Signup from "../views/Signup.vue";
import UserSettings from "../views/UserSettings.vue";

const routes = [
  {
    path: "/",
    name: "MainPage",
    component: Layout,
    children: [
      {
        path: "",
        name: "Main Page",
        component: MainPage,
      },
      {
        path: "about",
        name: "About",
        component: About,
      },
      {
        path: "search",
        name: "SearchPage",
        component: SearchPage,
      },
      {
        path: "login",
        name: "Login",
        component: Login,
      },
      {
        path: "signup",
        name: "Signup",
        component: Signup,
      },
      {
        path: "settings",
        name: "UserSettings",
        component: UserSettings,
      },
      {
        path: "/node/:id",
        name: "NodeView",
        component: Focus,
      },
      {
        path: "/edge/:source_id/:target_id",
        name: "EdgeView",
        component: Focus,
      },
      {
        path: "/node/:id/edit",
        name: "NodeEdit",
        component: Focus,
      },
      {
        path: "/edge/:source_id/:target_id/edit",
        name: "EdgeEdit",
        component: Focus,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
