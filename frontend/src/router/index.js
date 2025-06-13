import { createRouter, createWebHistory } from "vue-router";
import Layout from "../components/Layout.vue";
import MainPage from "../views/MainPage.vue";
import SearchPage from "../views/SearchPage.vue";
import Focus from "../views/ElementFocus.vue";
import About from "../views/About.vue";
import Login from "../views/Login.vue";
import Signup from "../views/Signup.vue";
import UserSettings from "../views/UserSettings.vue";
import ResetPassword from "../views/ResetPassword.vue";
import Favourites from "../views/Favourites.vue";
import VerifySecurityQuestion from "../views/VerifySecurityQuestion.vue";
import UpdateSecurityQuestion from "../views/UpdateSecurityQuestion.vue";
import Schema from "../views/Schema.vue";
import { useUnsaved } from "../composables/useUnsaved";

const routes = [
  {
    path: "/",
    name: "MainPage",
    component: Layout,
    children: [
      { path: "", name: "Main Page", component: MainPage },
      { path: "about", name: "About", component: About },
      { path: "search", name: "SearchPage", component: SearchPage },
      { path: "schema", name: "Schema", component: Schema },
      { path: "/login", name: "Login", component: Login },
      { path: "/signup", name: "Signup", component: Signup },
      { path: "/settings", name: "UserSettings", component: UserSettings },
      { path: "/favourites", name: "Favourites", component: Favourites },
      {
        path: "/verify-security-question",
        name: "VerifySecurityQuestion",
        component: VerifySecurityQuestion,
      },
      {
        path: "/update-security-question",
        name: "UpdateSecurityQuestion",
        component: UpdateSecurityQuestion,
      },
      {
        path: "/reset-password",
        name: "ResetPassword",
        component: ResetPassword,
      },
      {
        // Consolidated Node view (including rating in the left panel)
        path: "/node/:id",
        name: "NodeView",
        component: Focus,
        props: true,
      },
      {
        path: "/edge/:source_id/:target_id",
        name: "EdgeView",
        component: Focus,
        props: true,
      },
      {
        path: "/node/:id/edit",
        name: "NodeEdit",
        component: Focus,
        props: true,
      },
      {
        path: "/edge/:source_id/:target_id/edit",
        name: "EdgeEdit",
        component: Focus,
        props: true,
      },
      {
        path: "/node/:id/history",
        name: "NodeHistory",
        component: Focus,
        props: true,
      },
      {
        path: "/edge/:source_id/:target_id/history",
        name: "EdgeHistory",
        component: Focus,
        props: true,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to, from, next) => {
  // If leaving the edit view (NodeEdit or EdgeEdit) during submission,
  // skip the unsaved changes check.
  if (
    (from.name === "NodeEdit" || from.name === "EdgeEdit") &&
    (to.name === "NodeView" ||
      to.name === "EdgeView" ||
      to.name === "NodeHistory" ||
      to.name === "EdgeHistory")
  ) {
    next();
    return;
  }
  const { hasUnsavedChanges } = useUnsaved();
  if (hasUnsavedChanges.value) {
    if (window.confirm("You have unsaved edits. Leave without saving?")) {
      const { setUnsaved } = useUnsaved();
      setUnsaved(false);
      next();
    } else {
      next(false);
    }
  } else {
    next();
  }
});

export default router;
