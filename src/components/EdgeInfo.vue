<template>
    <div class="element-info">
      <div class="tabs">
        <button :class="{ active: currentTab === 'read' }" @click="currentTab = 'read'">Read</button>
        <button :class="{ active: currentTab === 'edit' }" @click="currentTab = 'edit'">Edit</button>
      </div>
      <h2>Edge Information</h2>
      <div v-if="edge">
        <component :is="currentTabComponent" :edge="edge" @publish="publishEdge" />
      </div>
      <div v-else>
        <p>Edge not found</p>
      </div>
    </div>
  </template>
  
  <script>
  import EdgeInfoRead from './EdgeInfoRead.vue';
  import EdgeInfoEdit from './EdgeInfoEdit.vue';
  
  export default {
    props: {
      edge: {
        type: Object,
        required: false,
        default: undefined,
      },
    },
    data() {
      return {
        currentTab: 'read',
      };
    },
    computed: {
      currentTabComponent() {
        return this.currentTab === 'read' ? EdgeInfoRead : EdgeInfoEdit;
      },
    },
    methods: {
      publishEdge(updatedEdge) {
        this.$emit('update-edge', updatedEdge);
        this.currentTab = 'read';
      },
    },
  };
  </script>