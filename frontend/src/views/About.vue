<template>
  <div class="about">
    <div class="commongraph-about">
      <header class="about-header">
        <h1 class="platform-title">About {{ platformName }}</h1>
        <div class="subtitle">{{ platformTagline }}</div>
      </header>

      <p class="description" v-html="platformDescription"></p>

      <p class="description">
        It is powered by <b>CommonGraph</b>, a free and open source tool to
        build graph-based co-production platforms.
      </p>

      <div class="description">
        <p>
          For any feedback, please reach out at:
          <a :href="`mailto:${adminEmail}`" class="contact-link">{{
            adminEmail
          }}</a
          >.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import { useConfig } from "../composables/useConfig";

export default {
  setup() {
    const { platformName, platformTagline, platformDescription, load } =
      useConfig();
    const adminEmail = import.meta.env.VITE_ADMIN_EMAIL;

    onMounted(load);

    return { platformName, platformTagline, platformDescription, adminEmail };
  },
};
</script>

<style scoped>
.about {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  line-height: 1.6;
  background-color: var(--background-color);
  color: var(--text-color);
}

.about-header {
  text-align: center;
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid var(--border-color);
}

.platform-title {
  font-size: 2.5rem;
  color: var(--text-color);
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.subtitle {
  font-size: 1.2rem;
  color: var(--text-color);
  font-style: italic;
  opacity: 0.7;
}

.content-section {
  margin-bottom: 2rem;
}

.description {
  font-size: 1.1rem;
  color: var(--text-color);
  margin-bottom: 1.5rem;
  text-align: justify;
}

.highlight {
  /* background-color: var(--highlight-color); */
  padding: 3px 6px;
  border-radius: 4px;
  font-weight: 600;
  border: 1px solid var(--border-color);
}

.contact-section {
  background-color: var(--node-color);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  border-left: 4px solid var(--border-color);
  margin-top: 1rem;
  border: 1px solid var(--border-color);
}

.contact-link {
  color: #646cff;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.contact-link:hover {
  color: #535bf2;
}

.customization-notice {
  background-color: var(--node-color);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
  position: relative;
}

.customization-notice::before {
  content: "⚠️";
  position: absolute;
  top: -10px;
  left: 15px;
  background-color: var(--background-color);
  padding: 0 10px;
  font-size: 1.2rem;
}

.customization-notice h3 {
  color: var(--text-color);
  margin-bottom: 1rem;
  margin-top: 0.5rem;
}

.customization-notice p,
.customization-notice ul {
  color: var(--text-color);
  opacity: 0.9;
}

.customization-notice ul {
  padding-left: 1.5rem;
}

.customization-notice li {
  margin-bottom: 0.5rem;
}

.customization-notice code {
  background-color: var(--highlight-color);
  padding: 3px 6px;
  border-radius: 3px;
  font-family: "Courier New", monospace;
  font-size: 0.9rem;
  border: 1px solid var(--border-color);
  color: var(--text-color);
}

@media (max-width: 768px) {
  .about {
    padding: 1rem;
  }

  .platform-title {
    font-size: 2rem;
  }

  .description {
    text-align: left;
  }

  .about-header {
    margin-bottom: 2rem;
  }
}
</style>
