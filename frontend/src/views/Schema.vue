<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
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
