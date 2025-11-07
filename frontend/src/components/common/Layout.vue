<template>
  <div class="app-layout">
    <!-- Top header bar -->
    <Header
      :isSideMenuOpen="isSideMenuOpen"
      @toggle-side-menu="toggleSideMenu"
    />

    <!-- Main layout area -->
    <div
      :class="[
        'layout',
        { 'full-width': isFocused, 'menu-collapsed': !isSideMenuOpen },
      ]"
    >
      <!-- Side menu (collapsible) -->
      <SideMenu v-if="isSideMenuOpen" />

      <!-- Main content area -->
      <div class="main-content">
        <router-view></router-view>
      </div>

      <!-- Rating pane for focused views -->
      <div class="rating-pane">
        <router-view name="rating"></router-view>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import SideMenu from "../common/SideMenu.vue";
import Header from "../common/Header.vue";

export default {
  components: {
    SideMenu,
    Header,
  },
  setup() {
    const isSideMenuOpen = ref(true);

    const toggleSideMenu = () => {
      isSideMenuOpen.value = !isSideMenuOpen.value;
      // Store preference in localStorage
      localStorage.setItem("sideMenuOpen", isSideMenuOpen.value.toString());
    };

    // Restore menu state from localStorage
    onMounted(() => {
      const stored = localStorage.getItem("sideMenuOpen");
      if (stored !== null) {
        isSideMenuOpen.value = stored === "true";
      }
    });

    return {
      isSideMenuOpen,
      toggleSideMenu,
    };
  },
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
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.layout {
  display: flex;
  flex: 1;
  padding: 4px 4px 4px 4px;
  overflow: hidden;
  background-color: var(--background-color);
  transition: all 0.3s ease;
}

.main-content {
  flex: 1;
  background-color: var(--background-color);
  border-radius: 5px;
  margin: 0 0 2px 2px;
  overflow-y: auto;
}

.full-width {
  max-width: 100%;
}

/* Smooth transitions for menu collapse/expand */
.layout {
  transition: all 0.3s ease;
}
</style>
