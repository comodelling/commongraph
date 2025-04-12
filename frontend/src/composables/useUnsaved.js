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
