<template>
  <div class="side-menu">
    <div class="title">Menu</div>
    <router-link to="/">Main page</router-link><br />
    <router-link to="/node/new">New proposal</router-link><br />
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
        // router.push(`/node/${proposal.node_id}`);
        window.location.href = `/node/${proposal.node_id}`;
      } catch (error) {
        console.error('Error fetching random proposal:', error);
      }
    };

    const createNewNode = async () => {
      try {
        const newNode = {
          id: 'new',
          label: 'New Node',
          data: {
            title: 'New Node',
            scope: 'scope',  // inherited scope
            node_type: 'proposal',
        },
      };
        console.log('Creating new node:', newNode);
        router.push({ name: 'NodeEdit', params: { id: 'new' } });
      } catch (error) {
        console.error('Error creating new node:', error);
      }
    };
    return {
      fetchRandomProposal,
      createNewNode, 
    };
  },
};
</script>

<style scoped>
.side-menu {
  width: 150px;
  min-width: 150px;
  height: 90vh;
  border: 1px solid #ccc;
  padding: 10px;
  font-size: 12px;
  /* margin-top: 50px; */
  margin-left: 10px;
  margin-top: 20px;
  padding-top: 50px;
}
.side-menu .title {
  font-size: 20px;
  font-weight: bold;
}
</style>