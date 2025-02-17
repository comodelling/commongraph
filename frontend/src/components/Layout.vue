<template>
  <div :class="['layout', { 'full-width': isFocused }]">
    <SideMenu />
    <div class="content">
      <router-view></router-view>
    </div>
    <!-- New pane for rating -->
    <div class="rating-pane">
      <router-view name="rating"></router-view>
    </div>
  </div>
</template>

<script>
import SideMenu from "./SideMenu.vue";

export default {
  components: { SideMenu },
  computed: {
    isFocused() {
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
  flex: 1;
  margin: 2px auto;
  padding: 3px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  /* max-height: 90%; */
  /* overflow-y: auto; */
  padding-right: 150px;
  justify-content: center;
}

.full-width {
  max-width: 100%;
}
</style>
