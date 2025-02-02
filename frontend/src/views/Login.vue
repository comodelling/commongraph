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
        <button type="submit">Login</button>
      </form>
      <p v-if="error" style="color: red">{{ error }}</p>
      <div class="links">
        <router-link to="/signup">Sign Up</router-link>
        |
        <router-link to="/reset-password">Reset Password</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import axios from "axios";
import router from "../router";
import { useAuth } from "../composables/useAuth";

export default {
  setup(props, { attrs }) {
    const { setToken } = useAuth();
    const username = ref("");
    const password = ref("");
    const error = ref(null);
    const infoMessage = ref(null);

    onMounted(() => {
      if (router.currentRoute.value.query.message) {
        infoMessage.value = router.currentRoute.value.query.message;
      }
      if (localStorage.getItem("token")) {
        router.push("/settings");
      }
    });

    const login = async () => {
      error.value = null;
      try {
        const response = await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/auth/login`,
          new URLSearchParams({
            username: username.value,
            password: password.value,
          }),
        );
        setToken(response.data.access_token);
        router.push("/settings");
      } catch (err) {
        error.value = "Login failed. Check your credentials.";
      }
    };

    return { username, password, login, error, infoMessage };
  },
};
</script>

<style scoped>
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100vw; /* ensures full width for left/right centering */
  height: 80vh; /* centers vertically */
}

.form-wrapper {
  width: 300px;
  text-align: center;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

label {
  text-align: left;
}

.links {
  font-size: 13px;
}
</style>
