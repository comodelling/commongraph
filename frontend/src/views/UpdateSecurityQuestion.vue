<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Update Security Question</h2>
      <form @submit.prevent="updateSecurityQuestion">
        <label>
          Security Question:
          <select v-model="securityQuestion" required>
            <option value="">Please select a security question</option>
            <option value="What is your mother's maiden name?">
              What is your mother's maiden name?
            </option>
            <option value="What was the name of your first pet?">
              What was the name of your first pet?
            </option>
            <option value="What was the make and model of your first car?">
              What was the make and model of your first car?
            </option>
            <option value="What town where you were born in?">
              What town where you were born in?
            </option>
            <option value="What was your favorite subject in school?">
              What was your favorite subject in school?
            </option>
          </select>
        </label>
        <label>
          Security Answer:
          <input
            v-model="securityAnswer"
            type="password"
            placeholder="Enter your answer"
            required
          />
        </label>
        <button type="submit">Save</button>
      </form>
      <p v-if="error" style="color: red">{{ error }}</p>
      <p v-if="success" style="color: green">{{ success }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

export default {
  setup() {
    const securityQuestion = ref("");
    const securityAnswer = ref("");
    const error = ref(null);
    const success = ref(null);
    const router = useRouter();
    const token = localStorage.getItem("token");

    const updateSecurityQuestion = async () => {
      error.value = null;
      success.value = null;

      if (!securityQuestion.value || !securityAnswer.value) {
        error.value = "Both security question and answer must be provided.";
        return;
      }

      if (securityAnswer.value.length < 3) {
        error.value = "Security answer must be at least 3 characters long.";
        return;
      }

      try {
        const security_settings = {
          security_question: securityQuestion.value,
          security_answer: securityAnswer.value,
        };
        const response = await axios.patch(
          `${import.meta.env.VITE_BACKEND_URL}/user/security-settings`,
          security_settings,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        success.value = "Security question and answer updated successfully.";
        router.push("/settings");
      } catch (err) {
        error.value =
          "Failed to update security settings. " +
          (err.response?.data.detail || "Try again later.");
      }
    };

    return {
      securityQuestion,
      securityAnswer,
      updateSecurityQuestion,
      error,
      success,
    };
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
  width: 400px;
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
</style>
