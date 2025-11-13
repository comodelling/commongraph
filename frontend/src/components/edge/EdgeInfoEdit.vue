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
            :disabled="!computedEdgeTypeOptions.includes(type)"
            :title="tooltips.edge[type] || tooltips.edge.type"
          >
            {{ capitalise(type) }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="isAllowed('references')" class="field">
      <strong :title="tooltips.edge.references">References:</strong>
      <div class="field-content">
        <div class="references-container">
          <div
            v-for="(reference, index) in editedEdge.references"
            :key="index"
            class="reference-item"
            :class="{ 'invalid-reference': !reference.trim() }"
          >
            <span
              v-if="editingField !== `reference-${index}`"
              @click="startEditing(`reference-${index}`)"
              class="reference-text"
              >{{ reference || "Click to add reference" }}</span
            >
            <input
              v-else
              v-model="editedEdge.references[index]"
              @blur="stopEditing(`reference-${index}`)"
              @keyup.enter="stopEditing(`reference-${index}`)"
              @keyup.escape="cancelReferenceEdit(index)"
              :ref="`reference-${index}Input`"
              class="reference-input"
              placeholder="Enter reference..."
            />
            <button
              class="delete-reference-button"
              @click="deleteReference(index)"
              title="Delete reference"
            >
              ×
            </button>
          </div>
        </div>
        <button class="add-button add-reference-button" @click="addReference">
          + Reference
        </button>
      </div>
    </div>
    <div class="field" v-if="isAllowed('description')">
      <strong :title="tooltips.edge.description">Description:</strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'description' && editedEdge.description"
          @click="startEditing('description')"
          >{{ editedEdge.description }}</span
        >
        <textarea
          v-else-if="editingField === 'description'"
          v-model="editedEdge.description"
          @blur="stopEditing('description')"
          ref="descriptionInput"
        ></textarea>
        <button
          v-else
          class="add-button add-description-button"
          @click="addDescription"
        >
          + Description
        </button>
      </div>
    </div>

    <button class="submit-button" @click="submit">{{ actionLabel }}</button>
    <p class="license-notice" v-if="license">
      By publishing changes, you irrevocably agree to release your contribution
      under the
      <a
        :href="getLicenseUrl(license)"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ license }}
      </a>
      license.
    </p>
  </div>
</template>

<script>
import api from "../../api/axios";
import _ from "lodash";
import tooltips from "../../assets/tooltips.json";
import { onMounted } from "vue";
import { useAuth } from "../../composables/useAuth";
import { useUnsaved } from "../../composables/useUnsaved";
import { useConfig } from "../../composables/useConfig";
import {
  loadGraphSchema,
  getAllowedEdgeTypes,
} from "../../composables/useGraphSchema";

export default {
  props: {
    edge: { type: Object, required: true },
    sourceType: { type: String, required: false, default: null },
    targetType: { type: String, required: false, default: null },
  },
  emits: ["publish-edge"],
  setup() {
    const { edgeTypes, load, license, getLicenseUrl } = useConfig();
    onMounted(load);
    onMounted(loadGraphSchema);
    return { edgeTypes, license, getLicenseUrl };
  },
  data() {
    return {
      editingField: null,
      editedEdge: _.cloneDeep(this.edge),
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
    computedEdgeTypeOptions() {
      // If both ends are known, only return allowed; else return all
      console.log(
        "Source type:",
        this.sourceType,
        "Target type:",
        this.targetType,
      );
      if (this.sourceType && this.targetType) {
        return getAllowedEdgeTypes(this.sourceType, this.targetType);
      }
      return Object.keys(this.edgeTypes);
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
    isTypeAllowed(type) {
      // only disable when both ends are known
      if (this.sourceType && this.targetType) {
        return getAllowedEdgeTypes(this.sourceType, this.targetType).includes(
          type,
        );
      }
      return true;
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
    deleteReference(index) {
      this.editedEdge.references.splice(index, 1);
    },
    cancelReferenceEdit(index) {
      // If it's an empty reference, remove it
      if (!this.editedEdge.references[index].trim()) {
        this.deleteReference(index);
      }
      this.editingField = null;
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
        this.editedEdge.tags = (this.editedEdge.tags || []).map((tag) =>
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
            `/edges/`,
            this.editedEdge,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          console.log("Created edge returned:", response.data);
        } else {
          response = await api.put(
            `/edges`,
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

<style scoped>
/* Additional spacing for field consistency - closer to view mode */
.field {
  margin: 5px 0;
}

/* Reference container styling */
.references-container {
  margin: 0;
  padding: 0;
}

/* Consistent spacing for add buttons */
.add-button {
  margin: 4px 0 0 0 !important;
  align-self: flex-start;
}

/* License notice styling */
.license-notice {
  font-size: 0.75rem;
  color: #999;
  margin-top: 12px;
  line-height: 1.3;
}

.license-notice a {
  color: #0066cc;
  text-decoration: none;
  font-weight: 500;
}

.license-notice a:hover {
  text-decoration: underline;
}
</style>
