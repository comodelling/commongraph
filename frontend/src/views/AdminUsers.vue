<template>
  <div v-if="isAdmin">  <!-- only show if current user is admin -->
    <h1>Manage Users</h1>
    <div v-for="user in users" :key="user.username" class="user-row">
      <span>{{ user.username }}</span>
      <span v-if="!user.is_active"><button @click="approve(user.username)">Approve</button></span>
      <span v-if="!user.is_admin"><button @click="promote(user.username)">Promote to Admin</button></span>
    </div>
  </div>
  <div v-else>
    <p>Not authorized.</p>
  </div>
</template>

<script setup>
import { onMounted, reactive, toRefs } from "vue";
import { useAuth } from "../composables/useAuth";
import api from "../api/axios";

const { getAccessToken } = useAuth();
const state = reactive({ users: [], isAdmin: false });
const { users, isAdmin } = toRefs(state);

async function fetchUsers() {
  const token = getAccessToken();
  const res = await api.get("/users/", { headers: { Authorization: `Bearer ${token}` } });
  state.users = res.data;
}

async function approve(username) {
  const token = getAccessToken();
  const res = await api.patch(`/users/${username}/approve`, null, { headers: { Authorization: `Bearer ${token}` } });
  Object.assign(state.users.find(u => u.username === username), res.data);
}

async function promote(username) {
  const token = getAccessToken();
  const res = await api.patch(`/users/${username}/promote`, null, { headers: { Authorization: `Bearer ${token}` } });
  Object.assign(state.users.find(u => u.username === username), res.data);
}

onMounted(async () => {
  // fetch current user to check is_admin
  const token = getAccessToken();
  const me = (await api.get("/users/me", { headers: { Authorization: `Bearer ${token}` } })).data;
  state.isAdmin = me.is_admin;
  if (state.isAdmin) await fetchUsers();
});
</script>

<style scoped>
.user-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}
</style>
