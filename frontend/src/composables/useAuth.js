import { reactive, computed } from "vue";

const state = reactive({
  token: localStorage.getItem("authToken") || null,
});

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token);

  const setToken = (token) => {
    state.token = token;
    localStorage.setItem("authToken", token);
  };

  const clearToken = () => {
    state.token = null;
    localStorage.removeItem("authToken");
  };

  return { isLoggedIn, setToken, clearToken };
}
