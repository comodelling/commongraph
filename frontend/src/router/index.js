import { createRouter, createWebHistory } from "vue-router";
import Layout from "../components/common/Layout.vue";
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
import UpdatePassword from "../views/UpdatePassword.vue";
import Schema from "../views/Schema.vue";
import AdminUsers from "../views/AdminUsers.vue";
import DemoViewer from "../views/DemoViewer.vue";
import BetaNotice from "../views/BetaNotice.vue";
import { useUnsaved } from "../composables/useUnsaved";
import { useAuth } from "../composables/useAuth";
import { useConfig } from "../composables/useConfig";

const routes = [
  // Main app routes - with Layout
  {
    path: "/",
    name: "MainPage",
    component: Layout,
    children: [
      {
        path: "",
        name: "Main Page",
        component: MainPage,
        meta: { requiresRead: true },
      },
      { path: "about", name: "About", component: About },
      { path: "beta", name: "BetaNotice", component: BetaNotice },
      {
        path: "search",
        name: "SearchPage",
        component: SearchPage,
        meta: { requiresRead: true },
      },
      {
        path: "schema",
        name: "Schema",
        component: Schema,
        meta: { requiresRead: true },
      },
      // Demo routes - now inside Layout for header/sidebar
      {
        path: "/demo/:demoId",
        name: "Demo",
        component: DemoViewer,
        props: true,
      },
      {
        path: "/demo/:demoId/node/:id",
        name: "DemoNode",
        component: DemoViewer,
        props: true,
      },
      {
        path: "/demo/:demoId/edge/:source_id/:target_id",
        name: "DemoEdge",
        component: DemoViewer,
        props: true,
      },
      { path: "/login", name: "Login", component: Login },
      {
        path: "/signup",
        name: "Signup",
        component: Signup,
        meta: { requiresSignupEnabled: true },
      },
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
        path: "/update-password",
        name: "UpdatePassword",
        component: UpdatePassword,
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
        meta: { requiresRead: true },
      },
      {
        path: "/edge/:source_id/:target_id",
        name: "EdgeView",
        component: Focus,
        props: true,
        meta: { requiresRead: true },
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
      {
        path: "/admin/users",
        name: "AdminUsers",
        component: AdminUsers,
        meta: { requiresAdmin: true },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Global navigation error handler
router.onError((error) => {
  console.error("Router error:", error);

  // Handle URI errors specifically
  if (error instanceof URIError || error.message?.includes("URI")) {
    console.warn("URI Error in router, redirecting to home");
    router.push("/").catch(() => {
      // If push fails, force redirect
      window.location.href = "/";
    });
    return;
  }

  // For other errors, try to navigate to home
  router.push("/").catch(() => {
    window.location.href = "/";
  });
});

router.beforeEach(async (to, from, next) => {
  try {
    // Validate the route path for malformed characters
    const path = to.path;

    // Check for non-ASCII characters or suspicious patterns
    if (!/^[\x00-\x7F]*$/.test(decodeURIComponent(path))) {
      console.warn("Malformed path detected:", path);
      next("/");
      return;
    }

    // Additional validation for specific attack patterns
    const suspiciousPatterns = [
      /wp-/i,
      /admin/i,
      /phpmyadmin/i,
      /config/i,
      /\.env/i,
      /\.git/i,
    ];

    // If the destination is a registered admin route (uses meta.requiresAdmin),
    // allow it to bypass the generic "admin" pattern block. This lets legitimate
    // admin pages defined in routes (like /admin/users) pass validation while
    // still blocking unregistered suspicious paths that include "/admin".
    const isAdminRoute = to.matched.some(
      (record) => record.meta && record.meta.requiresAdmin,
    );
    if (
      !isAdminRoute &&
      suspiciousPatterns.some((pattern) => pattern.test(path))
    ) {
      console.warn("Suspicious path detected:", path);
      next("/");
      return;
    } else if (
      isAdminRoute &&
      suspiciousPatterns.some((pattern) => pattern.test(path))
    ) {
      // Log but allow legitimate admin routes (they should still be protected server-side)
      console.info(
        "Suspicious pattern matched but route requires admin; allowing:",
        path,
      );
    }
  } catch (error) {
    console.error("Path validation error:", error);
    next("/");
    return;
  }

  // Check if signup is enabled for routes that require it
  const requiresSignupEnabled = to.matched.some(
    (record) => record.meta?.requiresSignupEnabled,
  );
  if (requiresSignupEnabled) {
    const { allowSignup, configLoaded } = useConfig();

    // If config isn't loaded yet, load it
    if (!configLoaded.value) {
      const { load } = useConfig();
      await load();
    }

    // Check if signup is enabled
    if (!allowSignup.value) {
      console.log("Signup is disabled, redirecting to login");
      next({ name: "Login" });
      return;
    }
  }

  // Check read permissions for routes that require it
  const requiresRead = to.matched.some((record) => record.meta?.requiresRead);
  if (requiresRead) {
    const { isLoggedIn } = useAuth();
    const { permissions } = useConfig();

    // If permissions aren't loaded yet, load them
    if (!permissions.value) {
      const { load } = useConfig();
      await load();
    }

    // Check if user has read permission
    if (permissions.value && !permissions.value.read) {
      // User doesn't have read permission, redirect to beta notice
      console.log("User lacks read permission, redirecting to beta notice");
      next({ name: "BetaNotice" });
      return;
    }
  }

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
