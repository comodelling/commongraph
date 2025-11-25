// SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { ref } from "vue";
const hasUnsavedChanges = ref(false);

export function useUnsaved() {
  function setUnsaved(value) {
    hasUnsavedChanges.value = value;
  }
  return {
    hasUnsavedChanges,
    setUnsaved,
  };
}
