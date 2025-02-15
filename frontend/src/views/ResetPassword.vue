<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Reset Password</h2>
      <form @submit.prevent="resetPassword">
        <label>
          New Password:
          <input type="password" v-model="newPassword" required />
        </label>
        <button type="submit">Reset Password</button>
      </form>
      <p v-if="success" style="color: green">{{ success }}</p>
      <p v-if="error" style="color: red">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import api from "../axios";
import { useRoute } from "vue-router";
import { useRouter } from "vue-router";

export default {
  setup() {
    const route = useRoute();
    const token = route.query.token;
    const newPassword = ref("");
    const success = ref(null);
    const error = ref(null);
    const router = useRouter();

    const resetPassword = async () => {
      error.value = null;
      try {
        const response = await api.post(
          `${import.meta.env.VITE_BACKEND_URL}/auth/reset-password`,
          { token, new_password: newPassword.value },
        );
        success.value = response.data.msg;
        router.push("/login");
      } catch (err) {
        error.value = "Failed to reset password.";
      }
    };

    return { newPassword, resetPassword, success, error };
  },
};
</script>

<style scoped>
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100vw;
  height: 80vh;
}

.form-wrapper {
  width: 300px;
  text-align: center;
  border-radius: 8px;
  padding: 20px;
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
</style>
