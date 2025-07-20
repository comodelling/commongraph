import { reactive, computed } from "vue";
// Breaking circular import: use fetch instead of axios
const BACKEND_URL = import.meta.env.VITE_API_URL;

const state = reactive({
  accessToken: localStorage.getItem("accessToken") || null,
  refreshToken: localStorage.getItem("refreshToken") || null,
  isAdmin: false,
  isSuperAdmin: false,
});

async function loadUser() {
  if (!state.accessToken) return;
  try {
    const res = await fetch(`${BACKEND_URL}/users/me`, {
      headers: { Authorization: `Bearer ${state.accessToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      state.isAdmin = data.is_admin;
      state.isSuperAdmin = data.is_super_admin;
    } else {
      state.isAdmin = false;
      state.isSuperAdmin = false;
    }
  } catch {
    state.isAdmin = false;
    state.isSuperAdmin = false;
  }
}

// initialize admin flag on module load
loadUser();

export function useAuth() {
  // refresh user info whenever composable is used
  loadUser();
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
    state.isSuperAdmin = false;
  };

  const getAccessToken = () => state.accessToken;
  const getRefreshToken = () => state.refreshToken;

  const isAdmin = computed(() => state.isAdmin);
  const isSuperAdmin = computed(() => state.isSuperAdmin);
  const hasAdminRights = computed(() => state.isAdmin || state.isSuperAdmin);

  return {
    isLoggedIn,
    setTokens,
    clearTokens,
    getAccessToken,
    getRefreshToken,
    isAdmin,
    isSuperAdmin,
    hasAdminRights,
  };
}
