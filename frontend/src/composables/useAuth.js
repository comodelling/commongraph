import { reactive, computed } from "vue";

const state = reactive({
  accessToken: localStorage.getItem("accessToken") || null,
  refreshToken: localStorage.getItem("refreshToken") || null,
});

export function useAuth() {
  const isLoggedIn = computed(() => !!state.accessToken);

  const setTokens = ({ accessToken, refreshToken }) => {
    state.accessToken = accessToken;
    state.refreshToken = refreshToken;
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
  };

  const clearTokens = () => {
    state.accessToken = null;
    state.refreshToken = null;
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
  };

  const getAccessToken = () => state.accessToken;
  const getRefreshToken = () => state.refreshToken;

  return {
    isLoggedIn,
    setTokens,
    clearTokens,
    getAccessToken,
    getRefreshToken,
  };
}
