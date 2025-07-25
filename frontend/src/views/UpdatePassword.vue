<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Update Password</h2>
      <form @submit.prevent="updatePassword">
        <label>
          Current Password:
          <input
            v-model="passwordForm.currentPassword"
            type="password"
            placeholder="Enter your current password"
            required
            :disabled="loading"
          />
        </label>
        <label>
          New Password:
          <input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="Enter your new password"
            required
            minlength="6"
            :disabled="loading"
          />
        </label>
        <label>
          Confirm New Password:
          <input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="Confirm your new password"
            required
            minlength="6"
            :disabled="loading"
          />
        </label>
        <button type="submit" :disabled="loading">
          {{ loading ? "Updating..." : "Update Password" }}
        </button>
      </form>
      <p v-if="error" style="color: red">{{ error }}</p>
      <p v-if="success" style="color: green">{{ success }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import api from "../api/axios";
import { useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";

export default {
  setup() {
    const passwordForm = ref({
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    });
    const error = ref(null);
    const success = ref(null);
    const loading = ref(false);
    const router = useRouter();
    const { getAccessToken } = useAuth();
    const token = getAccessToken();

    const updatePassword = async () => {
      error.value = null;
      success.value = null;

      // Validate passwords match
      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        error.value = "New passwords do not match.";
        return;
      }

      // Validate password length
      if (passwordForm.value.newPassword.length < 6) {
        error.value = "New password must be at least 6 characters long.";
        return;
      }

      // Validate current password is provided
      if (!passwordForm.value.currentPassword) {
        error.value = "Current password is required.";
        return;
      }

      loading.value = true;

      try {
        await api.patch(
          "/users/password",
          {
            current_password: passwordForm.value.currentPassword,
            new_password: passwordForm.value.newPassword,
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        success.value = "Password updated successfully!";
        // Navigate back to settings after a short delay
        setTimeout(() => {
          router.push("/settings");
        }, 2000);
      } catch (err) {
        if (err.response?.data?.detail) {
          error.value = err.response.data.detail;
        } else {
          error.value = "Failed to update password. Please try again.";
        }
      } finally {
        loading.value = false;
      }
    };

    return {
      passwordForm,
      updatePassword,
      error,
      success,
      loading,
    };
  },
};
</script>

<style scoped>
.form-wrapper {
  width: 400px;
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

input {
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
