<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>User Settings</h2>
      <div v-if="loading">Loading settings...</div>
      <div v-else-if="error">{{ error }}</div>
      <div v-else>
        <p><strong>Username:</strong> {{ user.username }}</p>
        <div class="theme-selector">
          <label>
            <strong>Preferred Theme:</strong>
            <input type="radio" value="system" v-model="preferredTheme" />
            System Default
          </label>
          <label>
            <input type="radio" value="light" v-model="preferredTheme" />
            Light
          </label>
          <label>
            <input type="radio" value="dark" v-model="preferredTheme" />
            Dark
          </label>
        </div>
        <button @click="navigateToUpdateSecurityQuestion">
          Update Security Question
        </button>
        <br /><br />
        <button @click="logout">Logout</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from "vue";
import api from "../api/axios";
import router from "../router";
import { useAuth } from "../composables/useAuth";

export default {
  setup() {
    const user = ref({});
    const loading = ref(true);
    const error = ref(null);
    const { getAccessToken, clearTokens } = useAuth();
    const preferredTheme = ref("system");
    const token = getAccessToken();

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

    watch(preferredTheme, async (newTheme) => {
      applyTheme(newTheme);
      localStorage.setItem("theme", newTheme);

      if (token) {
        try {
          const response = await api.patch(
            `/users/preferences`,
            { theme: newTheme },
            { headers: { Authorization: `Bearer ${token}` } },
          );
          user.value = response.data;
        } catch (err) {
          error.value = "Failed to update preferences.";
        }
      }
    });

    const fetchUser = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await api.get(
          `/users/me`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        user.value = response.data;
        preferredTheme.value =
          user.value.preferences?.theme ||
          localStorage.getItem("theme") ||
          "system";
        applyTheme(preferredTheme.value);
      } catch (err) {
        error.value = "Failed to fetch user settings.";
      } finally {
        loading.value = false;
      }
    };

    const logout = () => {
      clearTokens();
      router.push("/login");
    };

    const navigateToUpdateSecurityQuestion = () => {
      router.push("/update-security-question");
    };

    onMounted(() => {
      if (token) {
        fetchUser();
      } else {
        preferredTheme.value = localStorage.getItem("theme") || "system";
        applyTheme(preferredTheme.value);
        error.value = "Not authenticated. Please log in.";
        loading.value = false;
      }
    });

    return {
      user,
      loading,
      error,
      logout,
      preferredTheme,
      navigateToUpdateSecurityQuestion: navigateToUpdateSecurityQuestion,
    };
  },
};
</script>

<style scoped>
.theme-selector {
  margin-bottom: 1rem;
}
.theme-selector label {
  margin-right: 1rem;
}

.form-wrapper {
  width: 450px;
}

</style>
