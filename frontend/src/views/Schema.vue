<template>
  <div class="schema-page">
    <GraphSchema />
  </div>
</template>

<script lang="ts">
import GraphSchema from "../components/graph/GraphSchema.vue";

export default {
  name: "Schema",
  components: { GraphSchema },
};
</script>

<style scoped>
.schema-page {
  width: 100%;
  height: 100%;
}
</style>
