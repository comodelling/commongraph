<template>
  <div>
    <div class="field">
      <strong :title="tooltips.edge.type">
        Type:
        <span
          v-if="edgeTypeHasStatus && !isDraft && !isCurrentUserAdmin"
          class="status-lock"
          title="Protected when not in draft"
        >
          🔒
        </span>
      </strong>
      <div class="field-content">
        <select
          v-model="editedEdge.edge_type"
          @keydown.enter="moveToNextField('type')"
          @keydown.tab="handleTabKey($event, 'type')"
          :disabled="!canEditField('edge_type')"
          tabindex="0"
        >
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
          @dblclick="startEditing('description')"
          @keydown.enter="startEditing('description')"
          tabindex="0"
          >{{ editedEdge.description }}</span
        >
        <textarea
          v-else-if="editingField === 'description'"
          v-model="editedEdge.description"
          @blur="stopEditing('description')"
          @keydown.escape="cancelEditing('description')"
          @keydown.ctrl.enter="moveToNextField('description')"
          @keydown.meta.enter="moveToNextField('description')"
          ref="descriptionInput"
        ></textarea>
        <button
          v-else
          class="add-button add-description-button"
          @click="addDescription"
          @keydown.enter="addDescription"
          tabindex="0"
        >
          + Description
        </button>
      </div>
    </div>

    <button
      class="submit-button"
      @click="submit"
      @keydown.enter="submit"
      tabindex="0"
    >
      {{ actionLabel }}
    </button>
    <p class="license-notice" v-if="license">
      By editing the description, you agree to release your contribution under
      the
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
      debouncedPreviewEmit: _.debounce((val) => {
        this.$emit("preview-edge-update", val);
      }, 200),
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
    isDraft() {
      return this.editedEdge.status === "draft";
    },
    isCurrentUserAdmin() {
      const { hasAdminRights } = useAuth();
      return hasAdminRights.value || false;
    },
    // Check if draft option should be disabled
    isDraftOptionDisabled() {
      // If the edge is new or currently in draft status, allow selecting draft
      if (this.editedEdge.new || this.isDraft) {
        return false;
      }
      // If edge is not in draft status, disable the draft option
      return true;
    },
    // Check if the current edge type has a status field
    edgeTypeHasStatus() {
      return this.allowedFields.includes("status");
    },
    canEditField() {
      return (fieldName) => {
        // If new edge or in draft status, allow all field edits
        if (this.editedEdge.new || this.isDraft) {
          return true;
        }
        // If edge type doesn't have status field, allow all edits
        if (!this.edgeTypeHasStatus) {
          return true;
        }
        // If non-draft and edge type has status, only admins can edit edge_type
        const restrictedFields = ["edge_type"];
        if (restrictedFields.includes(fieldName)) {
          return this.isCurrentUserAdmin;
        }
        // Status field is always editable (but validation happens on backend for draft reversion)
        // Other fields can be edited by anyone
        return true;
      };
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
    getFieldOrder() {
      // Define the logical order of fields for keyboard navigation
      const baseFields = ["type", "description"];
      return baseFields.filter(
        (field) => field === "type" || this.isAllowed(field),
      );
    },
    moveToNextField(currentField) {
      this.stopEditing(currentField);
      const fieldOrder = this.getFieldOrder();
      const currentIndex = fieldOrder.indexOf(currentField);
      if (currentIndex < fieldOrder.length - 1) {
        const nextField = fieldOrder[currentIndex + 1];
        this.$nextTick(() => {
          this.startEditing(nextField);
        });
      } else {
        // Last field - focus submit button
        this.$nextTick(() => {
          const submitButton = this.$el.querySelector(".submit-button");
          if (submitButton) submitButton.focus();
        });
      }
    },
    moveToPrevField(currentField) {
      this.stopEditing(currentField);
      const fieldOrder = this.getFieldOrder();
      const currentIndex = fieldOrder.indexOf(currentField);
      if (currentIndex > 0) {
        const prevField = fieldOrder[currentIndex - 1];
        this.$nextTick(() => {
          this.startEditing(prevField);
        });
      }
    },
    handleTabKey(event, currentField) {
      event.preventDefault();
      if (event.shiftKey) {
        this.moveToPrevField(currentField);
      } else {
        this.moveToNextField(currentField);
      }
    },
    cancelEditing(field) {
      // Restore original value and stop editing
      this.editedEdge = _.cloneDeep(this.edge);
      this.stopEditing(field);
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
    editedEdge: {
      handler(newVal) {
        // Emit preview updates for both new and existing edges
        // Skip only when submitting to avoid duplicate updates
        if (!this.isSubmitting) {
          this.debouncedPreviewEmit(newVal);
        }
      },
      deep: true,
    },
  },
};
</script>

<style scoped>
/* Additional spacing for field consistency - closer to view mode */
.field {
  margin: 5px 0;
}

.status-lock {
  margin-left: 4px;
  font-size: 0.8em;
  opacity: 0.7;
}

/* Styling for disabled fields */
select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f5f5f5;
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
