<template>
  <div :class="['layout', { 'full-width': isFocused }]">
    <SideMenu />
    <div class="main-content">
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
.full-width {
  max-width: 100%;
}
</style>
