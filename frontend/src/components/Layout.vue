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
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.content {
  display: flex;
  flex-grow: 1;
  margin: 2px auto;
  padding: 3px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  max-height: 100%;
  /* Enable vertical scrolling */
  overflow-y: auto;

  /* align-items: center; */
  justify-content: center;
  /* width: 70vw; ensures full width for left/right centering */
  /* height: 80vh; */
}

.full-width {
  max-width: 100%;
}
</style>
