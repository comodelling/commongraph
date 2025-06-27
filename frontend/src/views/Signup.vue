<template>
  <div class="container">
    <div class="form-wrapper">
      <h2>Sign Up</h2>
      <form @submit.prevent="signup">
        <label>
          Username:
          <input
            v-model="username"
            placeholder="Enter your username"
            required
          />
        </label>
        <label>
          Password:
          <input
            type="password"
            v-model="password"
            placeholder="Enter your password"
            required
          />
        </label>
        <label>
          Confirm Password:
          <input
            type="password"
            v-model="confirmPassword"
            placeholder="Confirm your password"
            required
          />
        </label>
        <label title="Recommended for password reset">
          Security Question (recommended):
          <select v-model="securityQuestion">
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
          <br />
          <input
            v-model="securityAnswer"
            type="password"
            placeholder="Enter your answer"
            required
          />
        </label>
        <label>
          Email (optional):
          <input v-model="email" type="email" placeholder="Enter your email" />
        </label>
        <label>
          Display Name (optional):
          <input v-model="displayName" placeholder="Enter your display name" />
        </label>
        <button type="submit">Sign Up</button>
      </form>
      <p v-if="error" style="color: red">{{ error }}</p>
      <p v-if="success" style="color: green">{{ success }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import api from "../api/axios";
import router from "../router";

export default {
  setup() {
    const username = ref("");
    const email = ref("");
    const displayName = ref("");
    const password = ref("");
    const confirmPassword = ref("");
    const securityQuestion = ref("");
    const securityAnswer = ref("");
    const error = ref(null);
    const success = ref(null);
    const minPasswordLength = 8;
    const minAnswerLength = 3;

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

      if (
        (securityQuestion.value && !securityAnswer.value) ||
        (!securityQuestion.value && securityAnswer.value)
      ) {
        error.value = "Both security question and answer must be provided.";
        return;
      }

      if (
        securityAnswer.value &&
        securityAnswer.value.length < minAnswerLength
      ) {
        error.value = `Security answer must be at least ${minAnswerLength} characters long.`;
        return;
      }

      try {
        const user_data = {
          username: username.value,
          password: password.value,
          ...(securityQuestion.value && {
            security_question: securityQuestion.value,
          }),
          ...(securityAnswer.value && {
            security_answer: securityAnswer.value,
          }),
          ...(email.value && { email: email.value }),
          ...(displayName.value && { display_name: displayName.value }),
        };
        const response = await api.post(
          `/auth/signup`,
          user_data,
        );
        success.value = `Signup successful for ${response.data.username}. Please log in.`;
        router.push({
          path: "/login",
          query: { message: "Signup successful. Please log in." },
        });
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
      securityQuestion,
      securityAnswer,
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
  gap: 1rem;
  margin-top: 1rem;
}

label {
  text-align: left;
}
</style>
