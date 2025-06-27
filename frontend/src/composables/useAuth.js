import { reactive, computed } from "vue";
import api from "../api/axios";

const state = reactive({
  accessToken: localStorage.getItem("accessToken") || null,
  refreshToken: localStorage.getItem("refreshToken") || null,
  isAdmin: false,
});

async function loadUser() {
  if (!state.accessToken) return;
  try {
    const res = await api.get("/users/me", { headers: { Authorization: `Bearer ${state.accessToken}` } });
    state.isAdmin = res.data.is_admin;
  } catch {
    state.isAdmin = false;
  }
}

// initialize admin flag on module load
loadUser();

export function useAuth() {
  const isLoggedIn = computed(() => !!state.accessToken);

  const setTokens = ({ accessToken, refreshToken }) => {
    state.accessToken = accessToken;
    state.refreshToken = refreshToken;
    localStorage.setItem("accessToken", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
    loadUser();
  };

  const clearTokens = () => {
    state.accessToken = null;
    state.refreshToken = null;
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    state.isAdmin = false;
  };

  const getAccessToken = () => state.accessToken;
  const getRefreshToken = () => state.refreshToken;

  const isAdmin = computed(() => state.isAdmin);

  return {
    isLoggedIn,
    setTokens,
    clearTokens,
    getAccessToken,
    getRefreshToken,
    isAdmin,
  };
}
