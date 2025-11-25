<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>
import { useConfig } from "./composables/useConfig";
import { watch } from "vue";

export default {
  name: "App",
  setup() {
    const { platformName } = useConfig();

    // Update document title when platformName changes
    watch(
      platformName,
      (newName) => {
        if (newName) {
          document.title = newName;
        }
      },
      { immediate: true },
    );

    return { platformName };
  },
};
</script>

<style scoped></style>
