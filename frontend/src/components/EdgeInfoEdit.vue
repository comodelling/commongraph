<template>
  <div>
    <div class="field">
      <strong :title="tooltips.edge.type">Type:</strong>
      <div class="field-content">
        <select v-model="editedEdge.edge_type">
          <option
            v-for="(props, type) in edgeTypes"
            :key="type"
            :value="type"
            :title="tooltips.edge[type] || tooltips.edge.type"
          >
            {{ capitalise(type) }}
          </option>
        </select>
      </div>
    </div>

    <div  v-if="isAllowed('references')" class="field" >
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

    <strong v-if="isAllowed('description')" :title="tooltips.edge.description">Description:</strong>
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

    <button class="submit-button" @click="submit">{{ actionLabel }}</button>
  </div>
</template>

<script>
import api from "../axios";
import _ from "lodash";
import tooltips from "../assets/tooltips.json";
import { onMounted } from "vue";
import { useAuth } from "../composables/useAuth";
import { useUnsaved } from "../composables/useUnsaved";
import { useConfig } from "../composables/useConfig";

export default {
  props: {
    edge: Object,
  },
  emits: ["publish-edge"],
  setup() {
    const { edgeTypes, load } = useConfig();
    onMounted(load);
    return { edgeTypes };
  },
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
    allowedFields() {
      if (!this.edgeTypes || !this.editedEdge.edge_type) {
        return Object.keys(this.editedEdge);
      }
      return this.edgeTypes[this.editedEdge.edge_type].properties || [];
    },
    actionLabel() {
      return this.editedEdge.new ? "Create" : "Submit";
    },
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
    isAllowed(field) {
      return this.allowedFields.includes(field);
    },
    capitalise(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    },
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
      if (this.isAllowed("references")) {
        this.editedEdge.references = this.editedEdge.references.map((ref) =>
          ref.trim(),
        );
      }
      if (this.isAllowed("tags")) {
        this.editedEdge.tags = this.editedEdge.tags.map((tag) =>
          tag.trim(),
        );
      }
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
