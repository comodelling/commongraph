<template>
  <div class="element-info">
    <div class="tabs">
      <button :class="{ active: currentTab === 'read' }" @click="currentTab = 'read'">Read</button>
      <button :class="{ active: currentTab === 'edit' }" @click="currentTab = 'edit'">Edit</button>
    </div>
    <h2>Node Information</h2>
    <div v-if="node">
      <component :is="currentTabComponent" :node="node" @publish="publishNode" />
    </div>
    <div v-else>
      <p>Node not found</p>
    </div>
  </div>
</template>

<script>
import NodeInfoRead from './NodeInfoRead.vue';
import NodeInfoEdit from './NodeInfoEdit.vue';

export default {
  props: {
    node: {
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
      return this.currentTab === 'read' ? NodeInfoRead : NodeInfoEdit;
    },
  },
  methods: {
    publishNode(updatedNode) {
      this.$emit('update-node', updatedNode);
      this.currentTab = 'read';
    },
  },
};
</script>
