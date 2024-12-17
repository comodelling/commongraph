<template>
  <div :class="['layout', { 'full-width': isFocused }]">
    <SideMenu />
    <div class="content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import SideMenu from "./SideMenu.vue";

export default {
  components: {
    SideMenu,
  },
  computed: {
    isFocused() {
      // Uses a condition to determine if we're in a focused state
      return ["NodeView", "NodeEdit", "EdgeView", "EdgeEdit"].includes(
        this.$route.name,
      );
    },
  },
};
</script>

<style scoped>
.layout {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  border: 1px solid black;
  height: 100%;
}

.content {
  display: flex;
  flex-grow: 1; /* Allow content to expand */
  margin-left: 30px;
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ccc;
  max-height: 100%;
  overflow-y: auto; /* Enable vertical scrolling */
}

.full-width {
  max-width: 100%;
}
</style>
