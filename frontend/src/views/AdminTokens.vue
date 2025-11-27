<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
<template>
  <div class="container tokens-container">
    <div class="form-wrapper tokens-wrapper">
      <div v-if="hasAdminRights">
        <div class="header-section">
          <h2>Manage Signup Tokens</h2>
          <span class="info-icon" :title="helpText">ℹ️</span>
        </div>

        <!-- Generate Token Section -->
        <div class="generate-section">
          <h3>Generate New Token</h3>
          <form @submit.prevent="generateToken">
            <label>
              Notes (optional):
              <input
                v-model="newTokenNotes"
                placeholder="e.g., 'For Jane Doe' or 'Beta tester batch 1'"
                maxlength="300"
              />
            </label>
            <button type="submit" :disabled="generating">
              {{ generating ? "Generating..." : "Generate Token" }}
            </button>
          </form>
          <p v-if="generateError" class="error">{{ generateError }}</p>
        </div>

        <!-- Newly Created Token Display -->
        <div v-if="newlyCreatedToken" class="new-token-display">
          <h3>✅ Token Created Successfully</h3>
          <p class="token-info">
            Share this signup link with your invitee. They can use it once to
            sign up:
          </p>
          <div class="token-box">
            <code class="signup-link">{{ signupLink(newlyCreatedToken) }}</code>
            <button
              @click="copyToClipboard(signupLink(newlyCreatedToken))"
              class="btn-copy"
              :title="
                copiedLink === signupLink(newlyCreatedToken)
                  ? 'Copied!'
                  : 'Copy to clipboard'
              "
            >
              {{ copiedLink === signupLink(newlyCreatedToken) ? "✓" : "📋" }}
            </button>
          </div>
          <!-- <p class="token-warning">
            ⚠️ Save this link now — you won't be able to view the full token
            again.
          </p> -->
        </div>

        <!-- Tokens List -->
        <div class="tokens-section">
          <h3>All Tokens</h3>
          <div class="filter-buttons">
            <button
              @click="filter = 'all'"
              :class="{ active: filter === 'all' }"
            >
              All ({{ tokens.length }})
            </button>
            <button
              @click="filter = 'active'"
              :class="{ active: filter === 'active' }"
            >
              Active ({{ activeTokens.length }})
            </button>
            <button
              @click="filter = 'used'"
              :class="{ active: filter === 'used' }"
            >
              Used ({{ usedTokens.length }})
            </button>
          </div>

          <div v-if="loading" class="loading">Loading tokens...</div>
          <div v-else-if="filteredTokens.length === 0" class="no-tokens">
            No {{ filter === "all" ? "" : filter }} tokens found.
          </div>
          <div v-else class="tokens-table">
            <div class="table-header">
              <div class="col-token">Token (partial)</div>
              <div class="col-status">Status</div>
              <div class="col-created">Created</div>
              <div class="col-notes">Notes</div>
              <div class="col-actions">Actions</div>
            </div>
            <div
              v-for="token in filteredTokens"
              :key="token.token"
              class="token-row"
              :class="{ used: token.used_by }"
            >
              <div class="col-token">
                <code>{{ truncateToken(token.token) }}</code>
              </div>
              <div class="col-status">
                <span v-if="token.used_by" class="status-badge used">
                  Used by {{ token.used_by }}
                  <br />
                  <small>{{ formatDate(token.used_at) }}</small>
                </span>
                <span v-else class="status-badge active">Active</span>
              </div>
              <div class="col-created">
                <div>{{ token.created_by }}</div>
                <small>{{ formatDate(token.created_at) }}</small>
              </div>
              <div class="col-notes">
                {{ token.notes || "—" }}
              </div>
              <div class="col-actions">
                <button
                  v-if="!token.used_by"
                  @click="copyToClipboard(signupLink(token.token))"
                  class="btn-copy-small"
                  :title="
                    copiedLink === signupLink(token.token)
                      ? 'Copied!'
                      : 'Copy signup link'
                  "
                >
                  {{ copiedLink === signupLink(token.token) ? "✓" : "📋" }}
                </button>
                <button
                  @click="deleteToken(token.token)"
                  :disabled="deletingToken === token.token"
                  class="btn-delete"
                  :title="
                    token.used_by
                      ? 'Delete used token'
                      : 'Revoke and delete token'
                  "
                >
                  {{ deletingToken === token.token ? "..." : "🗑️" }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
      </div>
      <div v-else class="access-denied">
        <p>You do not have permission to access this page.</p>
        <router-link to="/">Go to Main Page</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import api from "../api/axios";
import { useAuth } from "../composables/useAuth";

export default {
  setup() {
    const { isAdmin, isSuperAdmin } = useAuth();
    const hasAdminRights = computed(() => isAdmin.value || isSuperAdmin.value);

    const tokens = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const success = ref(null);
    const newTokenNotes = ref("");
    const generating = ref(false);
    const generateError = ref(null);
    const newlyCreatedToken = ref(null);
    const deletingToken = ref(null);
    const filter = ref("all");
    const copiedLink = ref(null);

    const helpText = `This page lets you generate one-time signup tokens for inviting users to the platform.

• Generate a token with optional notes to track who it's for
• Copy the signup link and send it to your invitee
• Track which tokens are active or have been used
• Delete/revoke tokens as needed`;

    const activeTokens = computed(() => tokens.value.filter((t) => !t.used_by));
    const usedTokens = computed(() => tokens.value.filter((t) => t.used_by));
    const filteredTokens = computed(() => {
      if (filter.value === "active") return activeTokens.value;
      if (filter.value === "used") return usedTokens.value;
      return tokens.value;
    });

    const fetchTokens = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await api.get("/auth/admin/signup-tokens");
        tokens.value = response.data;
      } catch (err) {
        error.value =
          "Failed to load tokens. " + (err.response?.data?.detail || "");
      } finally {
        loading.value = false;
      }
    };

    const generateToken = async () => {
      generating.value = true;
      generateError.value = null;
      newlyCreatedToken.value = null;
      try {
        const response = await api.post("/auth/admin/generate-signup-token", {
          notes: newTokenNotes.value || null,
        });
        newlyCreatedToken.value = response.data.token;
        newTokenNotes.value = "";
        await fetchTokens();
        success.value = "Token generated successfully!";
        setTimeout(() => {
          success.value = null;
        }, 3000);
      } catch (err) {
        generateError.value =
          "Failed to generate token. " + (err.response?.data?.detail || "");
      } finally {
        generating.value = false;
      }
    };

    const deleteToken = async (token) => {
      if (
        !confirm(
          "Are you sure you want to delete this token? This action cannot be undone.",
        )
      ) {
        return;
      }
      deletingToken.value = token;
      error.value = null;
      try {
        await api.delete(`/auth/admin/signup-tokens/${token}`);
        await fetchTokens();
        success.value = "Token deleted successfully!";
        setTimeout(() => {
          success.value = null;
        }, 3000);
      } catch (err) {
        error.value =
          "Failed to delete token. " + (err.response?.data?.detail || "");
      } finally {
        deletingToken.value = null;
      }
    };

    const signupLink = (token) => {
      const baseUrl = window.location.origin;
      return `${baseUrl}/signup?token=${encodeURIComponent(token)}`;
    };

    const truncateToken = (token) => {
      return token.length > 16 ? `${token.substring(0, 12)}...` : token;
    };

    const formatDate = (dateString) => {
      if (!dateString) return "—";
      const date = new Date(dateString);
      return date.toLocaleDateString() + " " + date.toLocaleTimeString();
    };

    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text);
        copiedLink.value = text;
        setTimeout(() => {
          copiedLink.value = null;
        }, 2000);
      } catch (err) {
        console.error("Failed to copy to clipboard:", err);
      }
    };

    onMounted(() => {
      if (hasAdminRights.value) {
        fetchTokens();
      }
    });

    return {
      hasAdminRights,
      tokens,
      loading,
      error,
      success,
      newTokenNotes,
      generating,
      generateError,
      newlyCreatedToken,
      deletingToken,
      filter,
      activeTokens,
      usedTokens,
      filteredTokens,
      copiedLink,
      helpText,
      generateToken,
      deleteToken,
      signupLink,
      truncateToken,
      formatDate,
      copyToClipboard,
    };
  },
};
</script>

<style scoped>
.tokens-container {
  display: block;
  box-sizing: border-box;
  height: auto;
  /* Use the viewport and subtract the header height so the view fits
     the visible area correctly in multiple layouts */
  min-height: calc(100vh - 60px);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 2rem 1rem 4rem 1rem; /* bottom padding to ensure content isn't clipped */
}

.tokens-wrapper {
  width: 95%;
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 1.5rem;
}

.header-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.info-icon {
  font-size: 1.2rem;
  cursor: help;
  opacity: 0.7;
}

.generate-section {
  background: var(--background-secondary, #f5f5f5);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.generate-section h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.generate-section form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.generate-section label {
  text-align: left;
}

.generate-section input {
  margin-top: 0.5rem;
}

.new-token-display {
  background: #e8f5e9;
  border: 2px solid #4caf50;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.new-token-display h3 {
  margin-top: 0;
  color: #2e7d32;
}

.token-info {
  margin-bottom: 1rem;
  font-weight: 500;
}

.token-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #4caf50;
}

.signup-link {
  flex: 1;
  word-break: break-all;
  font-size: 0.9rem;
  color: #1976d2;
}

.btn-copy {
  padding: 0.5rem 1rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  min-width: 3rem;
}

.btn-copy:hover {
  background: #45a049;
}

.token-warning {
  margin-top: 1rem;
  margin-bottom: 0;
  color: #f57c00;
  font-weight: 500;
}

.tokens-section {
  margin-top: 2rem;
}

.filter-buttons {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.filter-buttons button {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color, #ccc);
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.filter-buttons button.active {
  background: var(--color-primary, #4a9eff);
  color: white;
  border-color: var(--color-primary, #4a9eff);
}

.loading,
.no-tokens {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.tokens-table {
  border: 1px solid var(--border-color, #ddd);
  border-radius: 4px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 2fr 2fr 3fr 1.5fr;
  gap: 1rem;
  padding: 1rem;
  background: var(--background-secondary, #f5f5f5);
  font-weight: bold;
  border-bottom: 1px solid var(--border-color, #ddd);
}

.token-row {
  display: grid;
  grid-template-columns: 2fr 2fr 2fr 3fr 1.5fr;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color, #eee);
  align-items: center;
}

.token-row:last-child {
  border-bottom: none;
}

.token-row.used {
  opacity: 0.7;
  background: var(--background-secondary, #fafafa);
}

.col-token code {
  font-size: 0.85rem;
  background: var(--background-secondary, #f5f5f5);
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
}

.col-status small {
  font-size: 0.75rem;
  color: #666;
}

.col-created {
  font-size: 0.9rem;
}

.col-created small {
  font-size: 0.75rem;
  color: #666;
}

.col-notes {
  font-size: 0.9rem;
  color: #555;
  font-style: italic;
}

.col-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-badge.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.used {
  background: #fff3e0;
  color: #e65100;
}

.btn-copy-small,
.btn-delete {
  padding: 0.4rem 0.8rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-copy-small {
  background: #2196f3;
  color: white;
}

.btn-copy-small:hover {
  background: #1976d2;
}

.btn-delete {
  background: #f44336;
  color: white;
}

.btn-delete:hover {
  background: #d32f2f;
}

.btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: #d32f2f;
  margin-top: 1rem;
}

.success {
  color: #2e7d32;
  margin-top: 1rem;
  font-weight: 500;
}

.access-denied {
  padding: 2rem;
  text-align: center;
}

.access-denied p {
  margin-bottom: 1rem;
  color: #d32f2f;
  font-size: 1.1rem;
}
</style>
