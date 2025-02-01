<template>
  <div>
    <h2>Sign Up</h2>
    <form @submit.prevent="signup">
      <label>
        Username:
        <input v-model="username" required />
      </label>
      <label>
        Email (optional):
        <input v-model="email" type="email" />
      </label>
      <label>
        Display Name (optional):
        <input v-model="displayName" />
      </label>
      <label>
        Password:
        <input type="password" v-model="password" required />
      </label>
      <label>
        Confirm Password:
        <input type="password" v-model="confirmPassword" required />
      </label>
      <button type="submit">Sign Up</button>
    </form>
    <p v-if="error" style="color: red">{{ error }}</p>
    <p v-if="success" style="color: green">{{ success }}</p>
  </div>
</template>

<script>
import { ref } from "vue";
import axios from "axios";
import router from "../router";

export default {
  setup() {
    const username = ref("");
    const email = ref("");
    const displayName = ref("");
    const password = ref("");
    const confirmPassword = ref("");
    const error = ref(null);
    const success = ref(null);
    const minPasswordLength = 8; // minimum required characters

    const signup = async () => {
      error.value = null;
      success.value = null;

      if (password.value.length < minPasswordLength) {
        error.value = `Password must be at least ${minPasswordLength} characters long.`;
        return;
      }

      if (password.value !== confirmPassword.value) {
        error.value = "Passwords do not match!";
        return;
      }

      try {
        const user_data = {
          username: username.value,
          password: password.value,
          ...(email.value && { email: email.value }),
          ...(displayName.value && { display_name: displayName.value }),
        };
        const response = await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/auth/signup`,
          user_data,
        );
        success.value = `Signup successful for ${response.data.username}. Please log in.`;
        router.push({
          path: "/login",
          query: { message: "Signup successful. Please log in." },
        });
        // }, 500);
      } catch (err) {
        error.value =
          "Signup failed. " + (err.response?.data.detail || "Try again later.");
      }
    };

    return {
      username,
      email,
      displayName,
      password,
      confirmPassword,
      signup,
      error,
      success,
    };
  },
};
</script>

<style scoped>
form {
  display: flex;
  flex-direction: column;
}

label {
  display: block;
  margin-bottom: 1rem;
}
</style>
