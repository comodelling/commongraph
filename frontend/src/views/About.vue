<template>
  <div class="about">
    <h1>About {{ platformName }}</h1>
    <p>
      {{ platformName }} is a platform based on CommonGraph, a free and open source software enabling groups to model graphs collaboratively.

    </p>

  </div>
</template>


<script>
import { onMounted } from "vue";
import { useConfig } from "../composables/useConfig";


export default {
    setup() {
    const { platformName, load } = useConfig();
    onMounted(load);
    return { platformName };
  },
};
</script>

<style scoped>
.about {
  padding: 30px 120px;
  /* padding-left: 100px; */
}
</style>
