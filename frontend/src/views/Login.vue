<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Login</h2>
      <div v-if="infoMessage" style="color: green">{{ infoMessage }}</div>
      <form @submit.prevent="login">
        <label>
          Username:
          <input v-model="username" required />
        </label>
        <label>
          Password:
          <input type="password" v-model="password" required />
        </label>
        <button type="submit">Log in</button>
      </form>
      <p v-if="error" style="color: red">{{ error }}</p>
      <div class="links">
        <router-link to="/signup" v-if="allowSignup">Sign Up</router-link>
        <span v-if="allowSignup"> | </span>
        <router-link to="/verify-security-question">Reset Password</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import api from "../api/axios";
import router from "../router";
import { useAuth } from "../composables/useAuth";
import { useConfig } from "../composables/useConfig";

export default {
  setup() {
    const { setTokens } = useAuth();
    const { allowSignup, load } = useConfig();
    const username = ref("");
    const password = ref("");
    const error = ref(null);
    const infoMessage = ref(null);
    const { getAccessToken } = useAuth();

    onMounted(async () => {
      await load();
      if (router.currentRoute.value.query.message) {
        infoMessage.value = router.currentRoute.value.query.message;
      }
      if (getAccessToken()) {
        router.push("/settings");
      }
    });

    const login = async () => {
      error.value = null;
      try {
        const response = await api.post(
          `/auth/login`,
          new URLSearchParams({
            username: username.value,
            password: password.value,
          }),
        );
        // assuming response.data contains both tokens returned from the backend
        console.log("Login response:", response.data);
        setTokens({
          accessToken: response.data.access_token,
          refreshToken: response.data.refresh_token,
        });
        router.push("/settings");
      } catch (err) {
        error.value = "Login failed. Check your credentials.";
      }
    };

    return { username, password, login, error, infoMessage, allowSignup };
  },
};
</script>

<style scoped>
form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.links {
  font-size: 13px;
  text-align: center;
}
</style>
