<template>
  <div>
    <h2 :title="edgeTypeTooltip">
      {{ edge.edge_type === "require" ? "Condition" : "Implication" }}
    </h2>

    <div class="field">
      <strong :title="tooltips.edge.references">References:</strong><br />
      <ul>
        <li
          v-for="(reference, index) in editedEdge.references"
          :key="index"
          :class="{ 'invalid-reference': !reference.trim() }"
          class="field-content"
        >
          <span
            v-if="editingField !== `reference-${index}`"
            @click="startEditing(`reference-${index}`)"
            >{{ reference || "Click to edit" }}</span
          >
          <input
            v-else
            v-model="editedEdge.references[index]"
            @blur="stopEditing(`reference-${index}`)"
            :ref="`reference-${index}Input`"
          />
        </li>
      </ul>
      <button class="add-reference-button" @click="addReference">
        + Reference
      </button>
    </div>
    <br />

    <strong :title="tooltips.edge.description">Description:</strong>
    <div
      class="field"
      v-if="editedEdge.description || editingField === 'description'"
    >
      <div class="field-content">
        <span
          v-if="editingField !== 'description'"
          @click="startEditing('description')"
          >{{ editedEdge.description }}</span
        >
        <textarea
          v-else
          v-model="editedEdge.description"
          @blur="stopEditing('description')"
          ref="descriptionInput"
        ></textarea>
      </div>
    </div>
    <button
      v-if="!editedEdge.description"
      class="add-description-button"
      @click="addDescription"
    >
      + Description
    </button>

    <button class="submit-button" @click="submit">Submit</button>
  </div>
</template>

<script>
import api from "../axios";
import _ from "lodash";
import tooltips from "../assets/tooltips.json";
import { useAuth } from "../composables/useAuth";
import { useUnsaved } from "../composables/useUnsaved";

export default {
  props: {
    edge: Object,
  },
  emits: ["publish-edge"],
  data() {
    const editedEdge = _.cloneDeep(this.edge);
    return {
      editingField: null,
      editedEdge: editedEdge,
      tooltips,
      isSubmitting: false,
    };
  },
  computed: {
    edgeTypeTooltip() {
      return this.tooltips.edge[this.edge.edge_type] || this.tooltips.edge.type;
    },
    hasLocalUnsavedChanges() {
      if (this.isSubmitting) return false;
      return JSON.stringify(this.edge) !== JSON.stringify(this.editedEdge);
    },
  },
  beforeRouteLeave(to, from, next) {
    if (this.isSubmitting) {
      next();
      return;
    }
    if (this.hasLocalUnsavedChanges) {
      if (!window.confirm("You have unsaved edits. Leave without saving?")) {
        next(false);
        return;
      }
    }
    next();
  },
  beforeRouteUpdate(to, from, next) {
    if (this.isSubmitting) {
      next();
      return;
    }
    if (this.hasLocalUnsavedChanges) {
      if (!window.confirm("You have unsaved edits. Leave without saving?")) {
        next(false);
        return;
      }
    }
    next();
  },
  mounted() {
    window.addEventListener("beforeunload", this.onBeforeUnload);
  },
  beforeUnmount() {
    window.removeEventListener("beforeunload", this.onBeforeUnload);
  },
  methods: {
    onBeforeUnload(e) {
      if (this.hasLocalUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    },
    confirmDiscardChanges() {
      if (this.hasLocalUnsavedChanges) {
        return window.confirm("You have unsaved edits. Leave without saving?");
      }
      return true;
    },
    startEditing(field) {
      this.editingField = field;
      this.$nextTick(() => {
        const refName = `${field}Input`;
        const ref = this.$refs[refName];
        if (Array.isArray(ref)) {
          ref[0].focus();
        } else if (ref) {
          ref.focus();
        }
      });
    },
    stopEditing(field) {
      if (this.editingField === field) {
        this.editingField = null;
      }
    },
    addReference() {
      if (
        this.editingField === null ||
        !this.editingField.startsWith("reference-")
      ) {
        this.editedEdge.references.push("");
        this.$nextTick(() => {
          this.startEditing(
            `reference-${this.editedEdge.references.length - 1}`,
          );
        });
      }
    },
    addDescription() {
      this.editedEdge.description = "";
      this.$nextTick(() => {
        this.startEditing("description");
      });
    },
    async submit() {
      const { getAccessToken } = useAuth();
      const token = getAccessToken();

      this.editedEdge.references = this.editedEdge.references.filter(
        (ref) => ref.trim() !== "",
      );
      console.log("Submitting edge:", this.editedEdge);
      let response;
      try {
        this.isSubmitting = true;
        if (this.editedEdge.new) {
          delete this.editedEdge.new;
          response = await api.post(
            `${import.meta.env.VITE_BACKEND_URL}/edge/`,
            this.editedEdge,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          console.log("Created edge returned:", response.data);
        } else {
          response = await api.put(
            `${import.meta.env.VITE_BACKEND_URL}/edge`,
            this.editedEdge,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          console.log("Updated edge returned:", response.data);
        }
        this.$emit("publish-edge", response.data);
      } catch (error) {
        console.error("Failed to update edge:", error);
      } finally {
        this.isSubmitting = false;
      }
    },
  },
  watch: {
    edge: {
      handler(newEdge) {
        this.editedEdge = _.cloneDeep(newEdge);
      },
      deep: true,
    },
    hasLocalUnsavedChanges(newVal) {
      const { setUnsaved } = useUnsaved();
      setUnsaved(newVal);
    },
  },
};
</script>
