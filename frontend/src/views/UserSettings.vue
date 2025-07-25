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
            <input type="radio" value="system" v-model="currentTheme" />
            System Default
          </label>
          <label>
            <input type="radio" value="light" v-model="currentTheme" />
            Light
          </label>
          <label>
            <input type="radio" value="dark" v-model="currentTheme" />
            Dark
          </label>
        </div>
        <button @click="navigateToUpdateSecurityQuestion">
          Update Security Question
        </button>
        <br /><br />
        <button @click="navigateToUpdatePassword">
          Change Password
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
import { useTheme } from "../composables/useTheme";

export default {
  setup() {
    const user = ref({});
    const loading = ref(true);
    const error = ref(null);
    const { getAccessToken, clearTokens } = useAuth();
    const { currentTheme, setTheme, loadUserTheme } = useTheme();
    const token = getAccessToken();

    const fetchUser = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await api.get(
          `/users/me`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        user.value = response.data;
        // Load user's theme preference from the backend
        if (user.value.preferences?.theme) {
          setTheme(user.value.preferences.theme);
        }
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

    const navigateToUpdatePassword = () => {
      router.push("/update-password");
    };

    onMounted(() => {
      if (token) {
        fetchUser();
      } else {
        error.value = "Not authenticated. Please log in.";
        loading.value = false;
      }
    });

    return {
      user,
      loading,
      error,
      logout,
      currentTheme,
      navigateToUpdateSecurityQuestion,
      navigateToUpdatePassword,
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
