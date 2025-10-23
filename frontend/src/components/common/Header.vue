<template>
  <header class="app-header">
    <div class="header-left">
      <!-- Menu toggle button -->
      <button class="menu-toggle" @click="toggleSideMenu" aria-label="Toggle menu">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
      
      <!-- Platform name with link to about -->
      <router-link to="/" class="platform-name">
        {{ platformName || 'CommonGraph' }}
      </router-link>
    </div>

    <!-- Centered search bar -->
    <div class="header-center">
      <SearchBar 
        :initialQuery="searchQuery" 
        @search="handleSearch"
        @focus-change="handleSearchFocus"
      />
    </div>

    <!-- Right side links -->
    <div class="header-right">
      <!-- Theme toggle -->
      <ThemeToggle />
      
      <a v-if="repoUrl" :href="repoUrl" target="_blank" class="header-link" title="Go to source code">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
        </svg>
        <!-- <span>Code</span> -->
      </a>
      
      <a v-if="docUrl" :href="docUrl" target="_blank" class="header-link" title="Go to documentation">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
        </svg>
        <!-- <span>Docs</span> -->
      </a>
    </div>
  </header>
</template>

<script>
import { useRouter, useRoute } from "vue-router";
import { watch, onMounted, ref } from "vue";
import { useConfig } from "../../composables/useConfig";
import { useAuth } from "../../composables/useAuth";
import { useTheme } from "../../composables/useTheme";
import SearchBar from "./SearchBar.vue";
import ThemeToggle from "./ThemeToggle.vue";

export default {
  components: {
    SearchBar,
    ThemeToggle
  },
  props: {
    isSideMenuOpen: {
      type: Boolean,
      default: true
    }
  },
  emits: ['toggle-side-menu'],
  setup(props, { emit }) {
    const router = useRouter();
    const route = useRoute();
    const { platformName } = useConfig();
    const { isLoggedIn } = useAuth();
    const { loadUserTheme } = useTheme();
    
    // Search focus state
    const isSearchFocused = ref(false);

    // Get environment variables for external links
    const repoUrl = import.meta.env.VITE_REPO_URL;
    const docUrl = import.meta.env.VITE_DOC_URL;

    // Watch for login status changes and load user theme
    watch(isLoggedIn, (newIsLoggedIn) => {
      if (newIsLoggedIn) {
        loadUserTheme();
      }
    });

    // Load user theme on component mount if already logged in
    onMounted(() => {
      if (isLoggedIn.value) {
        loadUserTheme();
      }
    });

    const toggleSideMenu = () => {
      emit('toggle-side-menu');
    };

    const handleSearch = (parsedQuery) => {
      // Navigate to search page with query parameters
      const queryParams = {
        q: parsedQuery.text || '',
        node_type: parsedQuery.nodeType || '',
        edge_type: parsedQuery.edgeType || '',
        tags: parsedQuery.tags ? parsedQuery.tags.join(',') : ''
      };
      
      // Remove empty parameters
      Object.keys(queryParams).forEach(key => {
        if (!queryParams[key]) {
          delete queryParams[key];
        }
      });

      router.push({
        name: 'SearchPage',
        query: queryParams
      });
    };

    const handleSearchFocus = (focused) => {
      isSearchFocused.value = focused;
    };

    // Get current search query from route if we're on search page
    const searchQuery = route.name === 'SearchPage' ? route.query.q || '' : '';

    return {
      platformName,
      repoUrl,
      docUrl,
      toggleSideMenu,
      handleSearch,
      handleSearchFocus,
      isSearchFocused,
      searchQuery
    };
  }
};
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  height: 50px;
  background-color: var(--background-color);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  position: relative;
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 200px;
}

.menu-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  color: var(--text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s ease;
}

.menu-toggle:hover {
  background-color: var(--border-color);
}

.platform-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
  text-decoration: none;
  transition: color 0.2s ease;
}

.platform-name:hover {
  color: #646cff;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 600px;
  margin: 0 2rem;
  /* Ensure search doesn't overflow */
  min-width: 0; /* Allow flexbox to shrink */
  overflow: hidden;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem; /* Reduced from 1rem for more compact layout */
  min-width: 120px; /* Reduced from 200px */
  justify-content: flex-end;
}

.header-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 6px 8px; /* Reduced padding for more compact icons */
  color: var(--text-color);
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s ease, color 0.2s ease;
  font-size: 0.9rem;
}

.header-link:hover {
  background-color: var(--border-color);
  color: #646cff;
}

.header-link span {
  font-weight: 500;
}

/* Dark mode adjustments */
body.dark .app-header {
  box-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .header-center {
    margin: 0 0.8rem;
    flex: 1;
  }
  
  .header-link span {
    display: none;
  }
  
  .header-right {
    min-width: 100px; /* Keep space for all icons */
    gap: 0.3rem;
  }
  
  .header-left {
    min-width: 140px; /* Space for menu + platform name */
  }
  
  .header-link {
    padding: 4px 6px;
  }
}

@media (max-width: 600px) {
  /* Platform name disappears first to give search more space */
  .platform-name {
    display: none;
  }
  
  .header-left {
    min-width: 50px; /* Just the menu button */
  }
  
  .header-center {
    margin: 0 0.5rem;
    flex: 2; /* Give search bar more priority */
  }
  
  /* When search is focused, expand to nearly full width */
  .header-center .search-bar.search-focused {
    margin-right: -0.3rem; /* Slightly overlap margins for more space */
  }
}

@media (max-width: 480px) {
  .app-header {
    padding: 0 0.3rem;
  }
  
  .header-center {
    margin: 0 0.3rem;
  }
  
  .header-right {
    min-width: 90px; /* Maintain space for icons */
    gap: 0.2rem;
  }
  
  .header-link {
    padding: 3px 4px;
  }
}

@media (max-width: 400px) {
  .header-center {
    margin: 0 0.2rem;
  }
  
  .header-right {
    min-width: 80px;
  }
  
  /* When focused, search bar takes almost all available space */
  .header-center .search-bar.search-focused {
    margin-right: -0.1rem;
  }
}
</style>
