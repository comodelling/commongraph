<template>
  <div>
    <h2>User Settings</h2>
    <div v-if="loading">Loading settings...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <p><strong>Username:</strong> {{ user.username }}</p>
      <p>
        <strong>Preferred Theme:</strong>
        {{ user.preferences?.theme || "default" }}
      </p>
      <button @click="logout">Logout</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import axios from "axios";
import router from "../router";
import { useAuth } from "../composables/useAuth";

export default {
  setup() {
    const user = ref({});
    const loading = ref(true);
    const error = ref(null);
    const { clearToken } = useAuth();
    const token = localStorage.getItem("token");

    const fetchUser = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/user/me`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        user.value = response.data;
      } catch (err) {
        error.value = "Failed to fetch user settings.";
      } finally {
        loading.value = false;
      }
    };

    const logout = () => {
      clearToken();
      router.push("/login");
    };

    onMounted(() => {
      if (token) {
        fetchUser();
      } else {
        error.value = "Not authenticated. Please log in.";
        loading.value = false;
      }
    });

    return { user, loading, error, logout };
  },
};
</script>
