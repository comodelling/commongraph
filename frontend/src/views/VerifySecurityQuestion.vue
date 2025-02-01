<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Verify Security Question</h2>
      <form @submit.prevent="fetchSecurityQuestion" v-if="!securityQuestion">
        <label>
          Username:
          <input v-model="username" required />
        </label>
        <button type="submit">Enter</button>
      </form>
      <form @submit.prevent="verifySecurityQuestion" v-else>
        <label>
          Security Question:
          <input v-model="securityQuestion" disabled />
        </label>
        <label>
          Answer:
          <input v-model="answer" required />
        </label>
        <button type="submit">Verify</button>
      </form>
      <p v-if="resetToken" style="color: green">
        Your reset token: {{ resetToken }}
      </p>
      <p v-if="error" style="color: red">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

export default {
  setup() {
    const username = ref("");
    const securityQuestion = ref("");
    const answer = ref("");
    const resetToken = ref(null);
    const error = ref(null);
    const router = useRouter();

    const fetchSecurityQuestion = async () => {
      error.value = null;
      try {
        const response = await axios.get(
          `${import.meta.env.VITE_BACKEND_URL}/auth/security-question`,
          { params: { username: username.value } },
        );
        if (response.data.security_question) {
          securityQuestion.value = response.data.security_question;
        } else {
          error.value = "No security question found for this user.";
        }
      } catch (err) {
        error.value = "Failed to fetch security question.";
      }
    };

    const verifySecurityQuestion = async () => {
      error.value = null;
      try {
        const response = await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/auth/verify-security-question`,
          { username: username.value, answer: answer.value },
        );
        console.log(response.data);
        router.push({
          path: "/reset-password",
          query: { token: response.data.reset_token },
        });
      } catch (err) {
        error.value = "Incorrect answer to the security question.";
      }
    };

    return {
      username,
      securityQuestion,
      answer,
      resetToken,
      verifySecurityQuestion,
      fetchSecurityQuestion,
      error,
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
</style>
