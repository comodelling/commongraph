<template>
  <div class="container">
    <div class="form-wrapper">
      <div v-if="hasAdminRights">
        <div class="header-section">
          <h2>Manage Users</h2>
          <span class="info-icon" :title="legendText">ℹ️</span>
        </div>
        <div v-if="users.length === 0" class="no-users">No users found.</div>
        <div v-else class="users-table">
          <div class="table-header">
            <div class="col-username">Username</div>
            <div class="col-status">Account Status</div>
            <div class="col-admin">Admin</div>
            <div class="col-super-admin">Super Admin</div>
          </div>
          <div v-for="user in users" :key="user.username" class="user-row">
            <div class="col-username">
              <span class="username">{{ user.username }}</span>
            </div>
            <div class="col-status">
              <button
                v-if="!user.is_active"
                @click="approve(user.username)"
                :disabled="isProcessing(user.username)"
                class="btn-approve"
              >
                Approve
              </button>
              <span v-else class="status-badge active">Active</span>
              <span v-if="isProcessing(user.username)" class="processing">
                Processing...
              </span>
            </div>
            <div class="col-admin">
              <label class="checkbox-container">
                <input
                  type="checkbox"
                  :checked="user.is_admin"
                  :disabled="user.is_super_admin || isProcessing(user.username)"
                  @change="toggleAdmin(user)"
                />
                <span class="checkmark"></span>
              </label>
            </div>
            <div class="col-super-admin">
              <label class="checkbox-container">
                <input
                  type="checkbox"
                  :checked="user.is_super_admin"
                  :disabled="!isSuperAdmin || isProcessing(user.username)"
                  @change="toggleSuperAdmin(user)"
                />
                <span class="checkmark"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
      <div v-else>
        <p>Not authorized to view this page.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, toRefs } from "vue";
import { useAuth } from "../composables/useAuth";
import api from "../api/axios";

const { getAccessToken, hasAdminRights, isSuperAdmin } = useAuth();
const state = reactive({
  users: [],
  processingUsers: new Set(), // Track which users are being processed
});
const { users } = toRefs(state);

const legendText = `Admin: Can manage users and has full system access
Super Admin: Has admin rights that cannot be revoked (only by other super admins)
Account Status: Users must be approved before they can access the system`;

function isProcessing(username) {
  return state.processingUsers.has(username);
}

function setProcessing(username, processing) {
  if (processing) {
    state.processingUsers.add(username);
  } else {
    state.processingUsers.delete(username);
  }
}

async function fetchUsers() {
  const token = getAccessToken();
  try {
    const res = await api.get("/users/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    state.users = res.data;
  } catch (error) {
    console.error("Failed to fetch users:", error);
  }
}

async function approve(username) {
  setProcessing(username, true);
  try {
    const token = getAccessToken();
    const res = await api.patch(`/users/${username}/approve`, null, {
      headers: { Authorization: `Bearer ${token}` },
    });
    // Update the user in our local array
    const userIndex = state.users.findIndex((u) => u.username === username);
    if (userIndex !== -1) {
      state.users[userIndex] = res.data;
    }
  } catch (error) {
    console.error("Failed to approve user:", error);
  } finally {
    setProcessing(username, false);
  }
}

async function toggleAdmin(user) {
  setProcessing(user.username, true);
  try {
    const token = getAccessToken();
    let res;
    if (user.is_admin) {
      // Demote from admin
      res = await api.patch(`/users/${user.username}/demote`, null, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } else {
      // Promote to admin
      res = await api.patch(`/users/${user.username}/promote`, null, {
        headers: { Authorization: `Bearer ${token}` },
      });
    }
    // Update the user in our local array
    const userIndex = state.users.findIndex(
      (u) => u.username === user.username,
    );
    if (userIndex !== -1) {
      state.users[userIndex] = res.data;
    }
  } catch (error) {
    console.error("Failed to toggle admin status:", error);
    // Show user-friendly error
    if (error.response?.status === 403) {
      alert(
        "Permission denied: You don't have sufficient privileges to perform this action.",
      );
    } else {
      alert("Failed to update user permissions. Please try again.");
    }
    // Refresh users to ensure UI is in sync
    await fetchUsers();
  } finally {
    setProcessing(user.username, false);
  }
}

async function toggleSuperAdmin(user) {
  setProcessing(user.username, true);
  try {
    const token = getAccessToken();
    const res = await api.patch(`/users/${user.username}/super-admin`, null, {
      headers: { Authorization: `Bearer ${token}` },
    });
    // Update the user in our local array
    const userIndex = state.users.findIndex(
      (u) => u.username === user.username,
    );
    if (userIndex !== -1) {
      state.users[userIndex] = res.data;
    }
  } catch (error) {
    console.error("Failed to toggle super admin status:", error);
    // Show user-friendly error
    if (error.response?.status === 403) {
      alert(
        "Permission denied: Only super admins can manage super admin status.",
      );
    } else {
      alert("Failed to update super admin status. Please try again.");
    }
    // Refresh users to ensure UI is in sync
    await fetchUsers();
  } finally {
    setProcessing(user.username, false);
  }
}

onMounted(async () => {
  if (hasAdminRights.value) {
    await fetchUsers();
  }
});
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: calc(100vh - 120px); /* Ensure space below header */
}

.header-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.header-section h2 {
  margin: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.info-icon {
  cursor: help;
  font-size: 1.2rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.info-icon:hover {
  opacity: 1;
}

.form-wrapper {
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  color: var(--text-color);
}

h2 {
  margin-bottom: 2rem;
  color: var(--text-color);
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
}

.no-users {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 2rem;
}

.users-table {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr;
  gap: 1rem;
  background: var(--background-color);
  border: 1px solid var(--border-color);
  padding: 1rem;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 2px solid var(--border-color);
}

.user-row {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  align-items: center;
  transition: background-color 0.2s;
  background: var(--background-color);
}

.user-row:hover {
  background-color: var(--node-color);
}

.user-row:last-child {
  border-bottom: none;
}

.col-username,
.col-status,
.col-admin,
.col-super-admin {
  display: flex;
  align-items: center;
}

.username {
  font-weight: 500;
  color: var(--text-color);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.active {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

body.dark .status-badge.active {
  background-color: #1e3a2e;
  color: #4ade80;
  border: 1px solid #065f46;
}

/* Custom checkbox styling */
.checkbox-container {
  display: block;
  position: relative;
  cursor: pointer;
  font-size: 18px;
  user-select: none;
}

.checkbox-container input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: relative;
  display: inline-block;
  height: 20px;
  width: 20px;
  background-color: var(--background-color);
  border: 2px solid var(--border-color);
  border-radius: 4px;
  transition: all 0.2s;
}

.checkbox-container:hover input ~ .checkmark {
  background-color: var(--node-color);
}

.checkbox-container input:checked ~ .checkmark {
  background-color: #007bff;
  border-color: #007bff;
}

.checkbox-container input:disabled ~ .checkmark {
  background-color: var(--node-color);
  border-color: var(--border-color);
  cursor: not-allowed;
  opacity: 0.5;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.checkbox-container input:checked ~ .checkmark:after {
  display: block;
}

.checkbox-container .checkmark:after {
  left: 6px;
  top: 2px;
  width: 6px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.btn-approve {
  background-color: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-approve:hover:not(:disabled) {
  background-color: #218838;
}

.btn-approve:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.processing {
  color: #007bff;
  font-style: italic;
  font-size: 0.875rem;
  margin-left: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  .form-wrapper {
    padding: 1rem;
  }

  .table-header,
  .user-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .table-header {
    display: none; /* Hide header on mobile, show labels inline */
  }

  .user-row {
    padding: 1.5rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .col-username::before {
    content: "Username: ";
    font-weight: 600;
  }
  .col-status::before {
    content: "Status: ";
    font-weight: 600;
  }
  .col-admin::before {
    content: "Admin: ";
    font-weight: 600;
  }
  .col-super-admin::before {
    content: "Super Admin: ";
    font-weight: 600;
  }
}
</style>
