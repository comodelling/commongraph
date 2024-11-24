<template>
  <div :class="['layout', { 'full-width': isFocused }]">
    <SideMenu />
    <div class="content">
      <router-view></router-view> <!-- For rendering other components/pages -->
    </div>
  </div>
</template>

<script>
import SideMenu from './SideMenu.vue';

export default {
  components: {
    SideMenu,
  },
  computed: {
    isFocused() {
      // Uses a condition to determine if we're in a focused state
      return this.$route.name === 'Focus';  // Adjust based on specific route focus
    },
  },
};
</script>

<style scoped>
.layout {
  display: flex;                   /* Flexbox layout for side menu and content */
  max-width: 1200px;              /* Centered default layout */
  margin: 0 auto;                 /* Center the layout */
  border: 1px solid black;         /* Border for layout */
  height: 100%;                   /* Full height */
}

.content {
  display: flex;                   /* Flex for internal layout */
  flex-grow: 1;                   /* Allow content to expand */
  margin-left: 30px;                   /* Default margin */
  margin-top: 20px;
  padding: 20px;                  /* Padding for content */
  border: 1px solid #ccc;         /* Border for content */
  max-height: 100vh;
}

.full-width {
  max-width: 100%;                /* Allow full width in focused view */
}
</style>