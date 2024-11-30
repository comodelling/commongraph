<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <a href="#" @click="fetchRandomProposal">Random proposal</a><br />
    <router-link to="/about">About ObjectiveNet</router-link>
  </div>
</template>

<script>
import axios from 'axios';
import { useRouter } from 'vue-router';

export default {
  setup() {
    const router = useRouter();

    const fetchRandomProposal = async () => {
      try {
        const response = await axios.get(`${import.meta.env.VITE_BACKEND_URL}/nodes/random?node_type=proposal`);
        const proposal = response.data;
        console.log('Random proposal:', proposal);
        router.push(`/focus/${proposal.node_id}`);
      } catch (error) {
        console.error('Error fetching random proposal:', error);
      }
    };

    return {
      fetchRandomProposal,
    };
  },
};
</script>

<style scoped>
.side-menu {
  width: 175px;
  min-width: 150px;
  height: 90vh;
  border: 1px solid #ccc;
  padding: 10px;
  font-size: 12px;
  /* margin-top: 50px; */
  margin-left: 10px;
  margin-top: 20px;
}
.side-menu .title {
  font-size: 20px;
  font-weight: bold;
}
</style>