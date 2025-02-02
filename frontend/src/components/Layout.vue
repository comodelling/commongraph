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
  /* Allow content to expand */
  flex-grow: 1;
  margin-left: 10px;
  margin-right: 10px;
  margin-top: 10px;
  padding: 20px;
  border: 1px solid #ccc;
  max-height: 100%;
  /* Enable vertical scrolling */
  overflow-y: auto;
}

.full-width {
  max-width: 100%;
}
</style>
