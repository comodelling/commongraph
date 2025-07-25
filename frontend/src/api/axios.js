import axios from "axios";
import qs    from "qs";           // <— new import
import { jwtDecode } from "jwt-decode";
import { useAuth } from "../composables/useAuth";

const { getAccessToken, getRefreshToken, setTokens, clearTokens } = useAuth();

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  paramsSerializer: params =>    // <— add this block
    qs.stringify(params, { arrayFormat: "repeat" }),
});

// Request interceptor to add token and refresh if needed
api.interceptors.request.use(
  async (config) => {
    let token = getAccessToken();
    if (token) {
      try {
        const decoded = jwtDecode(token);
        const currentTime = Date.now() / 1000;
        if (decoded.exp < currentTime) {
          // Token expired, try to refresh it
          const refreshToken = getRefreshToken();
          const response = await axios.post(
            `${import.meta.env.VITE_API_URL}/auth/refresh`,
            {},
            { headers: { Authorization: `Bearer ${refreshToken}` } },
          );
          setTokens({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
          });
          token = response.data.access_token;
        }
      } catch (error) {
        console.error("Error refreshing token", error);
        clearTokens();
      }
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

export default api;