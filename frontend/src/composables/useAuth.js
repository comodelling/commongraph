import { reactive, computed } from "vue";

const state = reactive({
  token: localStorage.getItem("token") || null,
});

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token);

  const setToken = (token) => {
    state.token = token;
    localStorage.setItem("token", token);
  };

  const clearToken = () => {
    state.token = null;
    localStorage.removeItem("token");
  };

  return { isLoggedIn, setToken, clearToken };
}
