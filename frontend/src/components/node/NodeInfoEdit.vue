<template>
  <div>
    <!-- Title Field -->
    <div class="field" v-if="isAllowed('title')">
      <strong :title="tooltips.node.title">
        Title:
        <span
          v-if="nodeTypeHasStatus && !isDraft && !isCurrentUserAdmin"
          class="status-lock"
          title="Protected when not in draft"
        >
          🔒
        </span>
      </strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'title'"
          @click="canEditField('title') && startEditing('title')"
          @dblclick="canEditField('title') && startEditing('title')"
          @keydown.enter="canEditField('title') && startEditing('title')"
          :class="{
            'error-text': titleError,
            'field-disabled': !canEditField('title'),
          }"
          :tabindex="canEditField('title') ? 0 : -1"
        >
          {{ editedNode.title || "Click to add a title" }}
        </span>
        <input
          v-else
          v-model="editedNode.title"
          @blur="stopEditing('title')"
          @keydown.enter="moveToNextField('title')"
          @keydown.escape="cancelEditing('title')"
          @keydown.tab="handleTabKey($event, 'title')"
          ref="titleInput"
          :class="{ 'error-input': titleError }"
        />
      </div>
    </div>
    <!-- Type Field (always allowed) -->
    <div class="field">
      <strong :title="tooltips.node.type">
        Type:
        <span
          v-if="nodeTypeHasStatus && !isDraft && !isCurrentUserAdmin"
          class="status-lock"
          title="Locked for non-admins when not in draft"
        >
          🔒
        </span>
      </strong>
      <div class="field-content">
        <select
          v-model="editedNode.node_type"
          ref="typeInput"
          @keydown.enter="moveToNextField('type')"
          @keydown.tab="handleTabKey($event, 'type')"
          :disabled="!canEditField('type')"
          tabindex="0"
        >
          <option
            v-for="(props, type) in nodeTypes"
            :key="type"
            :value="type"
            :disabled="!isTypeAllowed(type)"
            :title="tooltips.node[type] || tooltips.node.type"
          >
            {{ capitalise(type) }}
          </option>
        </select>
      </div>
    </div>
    <!-- Scope Field -->
    <div class="field" v-if="isAllowed('scope')">
      <strong :title="tooltips.node.scope">
        Scope:
        <span
          v-if="nodeTypeHasStatus && !isDraft && !isCurrentUserAdmin"
          class="status-lock"
          title="Protected when not in draft"
        >
          🔒
        </span>
      </strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'scope'"
          @click="canEditField('scope') && startEditing('scope')"
          @dblclick="canEditField('scope') && startEditing('scope')"
          @keydown.enter="canEditField('scope') && startEditing('scope')"
          :class="{
            'error-text': scopeError,
            'field-disabled': !canEditField('scope'),
          }"
          :tabindex="canEditField('scope') ? 0 : -1"
        >
          {{ editedNode.scope || "Click to add a scope" }}
        </span>
        <ScopeAutocomplete
          v-else
          v-model="editedNode.scope"
          @blur="stopEditing('scope')"
          @keydown.enter="moveToNextField('scope')"
          @keydown.escape="cancelEditing('scope')"
          @keydown.tab="handleTabKey($event, 'scope')"
          :error="scopeError"
          ref="scopeInput"
        />
      </div>
    </div>
    <!-- Status Field -->
    <div class="field" v-if="isAllowed('status')">
      <strong :title="tooltips.node.status">Status:</strong>
      <div class="field-content">
        <select
          v-model="editedNode.status"
          ref="statusInput"
          @keydown.enter="moveToNextField('status')"
          @keydown.tab="handleTabKey($event, 'status')"
          tabindex="0"
        >
          <option
            value="draft"
            :title="tooltips.node.draft"
            :disabled="isDraftOptionDisabled"
          >
            Draft
          </option>
          <option value="live" :title="tooltips.node.live">Live</option>
          <option value="realised" :title="tooltips.node.realised">
            Realised
          </option>
          <option value="unrealised" :title="tooltips.node.unrealised">
            Unrealised
          </option>
        </select>
      </div>
    </div>
    <!-- References Field -->
    <div class="field" v-if="isAllowed('references')">
      <strong :title="tooltips.node.references">References:</strong>
      <div class="field-content">
        <div class="references-container">
          <div
            v-for="(reference, index) in editedNode.references"
            :key="index"
            class="reference-item"
            :class="{ 'invalid-reference': !reference.trim() }"
          >
            <span
              v-if="editingField !== `reference-${index}`"
              @click="startEditing(`reference-${index}`)"
              class="reference-text"
            >
              {{ reference || "Click to add reference" }}
            </span>
            <input
              v-else
              v-model="editedNode.references[index]"
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
    <!-- Description Field -->
    <div class="field" v-if="isAllowed('description')">
      <strong :title="tooltips.node.description">Description:</strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'description' && editedNode.description"
          @click="startEditing('description')"
          @dblclick="startEditing('description')"
          @keydown.enter="startEditing('description')"
          tabindex="0"
        >
          {{ editedNode.description }}
        </span>
        <textarea
          v-else-if="editingField === 'description'"
          v-model="editedNode.description"
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
    <!-- Tags Field -->
    <div class="field" v-if="isAllowed('tags')">
      <strong :title="tooltips.node.tags">Tags:</strong>
      <div class="field-content">
        <div
          v-if="editingField !== 'tags'"
          class="tags-preview"
          @click="canEditField('tags') && startEditing('tags')"
          @keydown.enter="canEditField('tags') && startEditing('tags')"
          tabindex="0"
        >
          <span
            v-if="editedNode.tags.length"
            v-for="(tag, index) in editedNode.tags"
            :key="`${tag}-${index}`"
            class="tag"
            role="button"
            tabindex="0"
            @click.stop="handleTagPreviewClick(tag, index)"
            @keydown.enter.prevent.stop="handleTagPreviewClick(tag, index)"
          >
            {{ tag }}
          </span>
          <span v-else class="tag-placeholder">Click to add tags</span>
        </div>
        <TagSelector
          v-else
          v-model="editedNode.tags"
          ref="tagsInput"
          :edit-request="tagEditRequest"
          @blur="stopEditing('tags')"
          @keydown="handleTagSelectorKeydown"
          @edit-request-consumed="handleTagEditConsumed"
        />
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
    <p class="license-notice" v-if="shouldShowLicenseNotice">
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
import { useAuth } from "../../composables/useAuth";
import { useUnsaved } from "../../composables/useUnsaved";
// Import the meta config composable
import { useConfig } from "../../composables/useConfig";
import { onBeforeMount, onMounted } from "vue";
import {
  loadGraphSchema,
  getAllowedTargetNodeTypes,
  getAllowedSourceNodeTypes,
} from "../../composables/useGraphSchema";
import ScopeAutocomplete from "./ScopeAutocomplete.vue";
import TagSelector from "../common/TagSelector.vue";
import { useLogging } from "../../composables/useLogging";

export default {
  components: {
    ScopeAutocomplete,
    TagSelector,
  },
  props: {
    node: Object,
  },
  // Use the setup() function solely to expose the meta config data.
  setup(props) {
    const { nodeTypes, load, defaultEdgeType, license, getLicenseUrl } =
      useConfig();
    // block here until both nodeTypes & edgeTypes are populated
    onBeforeMount(load);
    onMounted(loadGraphSchema);
    return { nodeTypes, defaultEdgeType, load, license, getLicenseUrl };
  },
  data() {
    const { debugLog, infoLog, warnLog, errorLog, DEBUG } =
      useLogging("NodeInfoEdit");

    let editedNode = _.cloneDeep(this.node);
    if (!Array.isArray(editedNode.tags)) {
      editedNode.tags = [];
    }
    return {
      editingField: null,
      editedNode: editedNode,
      tagEditRequest: null,
      tooltips,
      titleError: false,
      scopeError: false,
      isSubmitting: false,
      DEBUG,
      debugLog,
      infoLog,
      warnLog,
      errorLog,
      debouncedPreviewEmit: _.debounce((val) => {
        this.$emit("preview-node-update", val);
      }, 200),
    };
  },
  computed: {
    // Compute allowedFields reactively based on the current editable type.
    allowedFields() {
      if (!this.nodeTypes || !this.editedNode.node_type) {
        // Fallback: allow all properties from the node object.
        return Object.keys(this.node);
      }
      return this.nodeTypes[this.editedNode.node_type].properties || [];
    },
    allowedNodeTypes() {
      const fc = this.editedNode.fromConnection;
      if (!fc) {
        return Object.keys(this.nodeTypes);
      }
      const otherType = fc.node_type;
      return fc.handle_type === "source"
        ? getAllowedTargetNodeTypes(otherType)
        : getAllowedSourceNodeTypes(otherType);
    },
    actionLabel() {
      return this.editedNode.new ? "Create" : "Submit";
    },
    nodeTypeTooltip() {
      return this.tooltips.node[this.node.node_type] || this.tooltips.node.type;
    },
    hasLocalUnsavedChanges() {
      if (this.isSubmitting) return false;
      return JSON.stringify(this.node) !== JSON.stringify(this.editedNode);
    },
    // Check if this node is in draft status
    isDraft() {
      return this.editedNode.status === "draft";
    },
    // Check if the current user is an admin
    isCurrentUserAdmin() {
      const { hasAdminRights } = useAuth();
      return hasAdminRights.value || false;
    },
    // Determine if a field can be edited based on status
    canEditField() {
      return (fieldName) => {
        // If new node or in draft status, allow all field edits
        if (this.editedNode.new || this.isDraft) {
          return true;
        }
        // If node type doesn't have status field, allow all edits
        if (!this.nodeTypeHasStatus) {
          return true;
        }
        // If non-draft and node type has status, only admins can edit restricted fields
        const restrictedFields = ["title", "type", "scope"];
        if (restrictedFields.includes(fieldName)) {
          return this.isCurrentUserAdmin;
        }
        // Status field is always editable (but validation happens on backend for draft reversion)
        // Other fields can be edited by anyone
        return true;
      };
    },
    // Check if draft option should be disabled
    isDraftOptionDisabled() {
      // If the node is new or currently in draft status, allow selecting draft
      if (this.editedNode.new || this.isDraft) {
        return false;
      }
      // If node is not in draft status, disable the draft option
      return true;
    },
    // Check if the current node type has a status field
    nodeTypeHasStatus() {
      return this.allowedFields.includes("status");
    },
    nodeTypeHasDescription() {
      return this.allowedFields.includes("description");
    },
    shouldShowLicenseNotice() {
      return Boolean(this.license && this.nodeTypeHasDescription);
    },
  },
  methods: {
    // Use the computed allowedFields to check if a field is allowed.
    isAllowed(field) {
      const allowed = this.allowedFields; // ← allowedFields is already an Array
      return allowed.includes(field);
    },
    isTypeAllowed(type) {
      return this.allowedNodeTypes.includes(type);
    },
    capitalise(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    getFieldOrder() {
      // Define the logical order of fields for keyboard navigation
      const baseFields = [
        "title",
        "type",
        "scope",
        "status",
        "description",
        "tags",
      ];
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
    handleTagSelectorKeydown(event) {
      if (event.key === "Escape") {
        this.cancelEditing("tags");
      } else if (event.key === "Tab") {
        this.moveToNextField("tags");
      }
    },
    handleTagPreviewClick(tag, index) {
      if (!this.canEditField("tags")) {
        return;
      }
      this.tagEditRequest = {
        index,
        tag,
        nonce: Date.now(),
      };
      if (this.editingField !== "tags") {
        this.startEditing("tags");
      }
    },
    handleTagEditConsumed() {
      this.tagEditRequest = null;
    },
    cancelEditing(field) {
      // Restore original value and stop editing
      this.editedNode = _.cloneDeep(this.node);
      this.stopEditing(field);
    },
    startEditing(field) {
      this.editingField = field;
      this.$nextTick(() => {
        const refName = `${field}Input`;
        const ref = this.$refs[refName];
        if (Array.isArray(ref)) {
          ref[0].focus();
        } else if (ref) {
          // Handle component refs (like ScopeAutocomplete) vs native elements
          if (ref.focus && typeof ref.focus === "function") {
            ref.focus();
          } else if (ref.$el && ref.$el.focus) {
            ref.$el.focus();
          }
        }
      });
    },
    stopEditing(field) {
      if (this.editingField === field) {
        this.editingField = null;
      }
      if (field === "tags") {
        this.tagEditRequest = null;
      }
    },
    addReference() {
      this.editedNode.references.push("");
      this.$nextTick(() => {
        this.startEditing(`reference-${this.editedNode.references.length - 1}`);
      });
    },
    deleteReference(index) {
      this.editedNode.references.splice(index, 1);
    },
    cancelReferenceEdit(index) {
      // If it's an empty reference, remove it
      if (!this.editedNode.references[index].trim()) {
        this.deleteReference(index);
      }
      this.editingField = null;
    },
    addDescription() {
      this.editedNode.description = "";
      this.$nextTick(() => {
        this.startEditing("description");
      });
    },
    ensureNodeTypeIsAllowed() {
      if (!this.editedNode?.new) {
        return;
      }
      const permittedTypes = this.allowedNodeTypes || [];
      if (!permittedTypes.length) {
        return;
      }
      if (!this.isTypeAllowed(this.editedNode.node_type)) {
        this.editedNode.node_type = permittedTypes[0];
      }
    },
    async submit() {
      if (!window.confirm("Are you sure you want to submit your changes?")) {
        return;
      }
      const { getAccessToken } = useAuth();
      const token = getAccessToken();
      if (this.isAllowed("title")) {
        const trimmedTitle = this.editedNode.title.trim();
        this.editedNode.title = trimmedTitle;
        this.titleError = !trimmedTitle;
        if (this.titleError) return;
      }
      if (this.isAllowed("scope")) {
        const trimmedScope = this.editedNode.scope.trim();
        this.editedNode.scope = trimmedScope;
        this.scopeError = !trimmedScope;
        if (this.scopeError) return;
      }

      if (
        !this.editedNode.new &&
        this.editedNode.node_type !== this.node.node_type
      ) {
        const confirmChange = window.confirm(
          "Changing the node type may have unintended consequences. Are you sure you want to proceed?",
        );
        if (!confirmChange) {
          this.editedNode.node_type = this.node.node_type;
          return;
        }
      }
      // Cleanup tags, references, support.
      if (this.isAllowed("references")) {
        this.editedNode.references = this.editedNode.references.filter(
          (ref) => ref.trim() !== "",
        );
      }
      if (this.isAllowed("tags")) {
        this.editedNode.tags = this.editedNode.tags.filter(
          (tag) => tag.trim() !== "",
        );
      }
      if (this.isAllowed("status")) {
        this.editedNode.status = this.editedNode.status || null;
      }
      this.isSubmitting = true;
      const { setUnsaved } = useUnsaved();
      setUnsaved(false);

      if (this.editedNode.new) {
        try {
          const fromConnection = this.editedNode.fromConnection;
          delete this.editedNode.fromConnection;
          delete this.editedNode.new;
          delete this.editedNode.node_id;

          const response = await api.post(
            "/nodes",
            this.editedNode,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          const nodeReturned = response.data;
          const target = nodeReturned.node_id;
          nodeReturned.new = true;

          // If node is created *from* a connection, emit event to open edge creation panel
          if (fromConnection) {
            this.$emit("request-edge-creation", {
              fromConnection,
              newNodeId: target,
              newNode: nodeReturned,
            });
          }
          this.$emit("publish-node", nodeReturned);
          this.editedNode = _.cloneDeep(nodeReturned);
          if (!fromConnection) {
            this.$router.push({
              name: "NodeView",
              params: { id: target.toString() },
            });
          }
        } catch (error) {
          this.errorLog("Failed to create node:", error);
        }
      } else {
        try {
          const response = await api.put(`/nodes`, this.editedNode);
          this.$emit("publish-node", response.data);
          this.editedNode = _.cloneDeep(response.data);
        } catch (error) {
          this.errorLog("Failed to update node:", error);
        }
      }
    },
    onBeforeUnload(e) {
      if (this.hasLocalUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    },
  },
  beforeRouteLeave(to, from, next) {
    if (this.isSubmitting) {
      next();
      return;
    }
    if (this.hasLocalUnsavedChanges) {
      if (!confirm("You have unsaved edits. Leave without saving?")) {
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
    if (this.editedNode.new) {
      if (
        !confirm("This new node is not saved. Are you sure you want to leave?")
      ) {
        next(false);
        return;
      }
    } else if (this.hasLocalUnsavedChanges) {
      if (!confirm("You have unsaved edits. Leave without saving?")) {
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
  watch: {
    node: {
      handler(newNode) {
        this.editedNode = _.cloneDeep(newNode);
        if (!Array.isArray(this.editedNode.tags)) {
          this.editedNode.tags = [];
        }
        this.tagEditRequest = null;
        this.ensureNodeTypeIsAllowed();
      },
      deep: true,
    },
    hasLocalUnsavedChanges(newVal) {
      const { setUnsaved } = useUnsaved();
      setUnsaved(newVal);
    },
    editedNode: {
      handler(newVal) {
        // Emit preview updates for both new and existing nodes
        // Skip only when submitting to avoid duplicate updates
        if (!this.isSubmitting) {
          this.debouncedPreviewEmit(newVal);
        }
      },
      deep: true,
    },
    allowedNodeTypes: {
      handler() {
        this.ensureNodeTypeIsAllowed();
      },
      immediate: true,
    },
  },
};
</script>

<style scoped>
.error-input {
  border-color: red;
}
.error-text {
  color: red;
}

.field-disabled {
  opacity: 0.6;
  cursor: not-allowed;
  color: #999;
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

/* Additional spacing for field consistency - closer to view mode */
.field {
  margin: 5px 0;
}

/* Ensure tags preview aligns properly while keeping inline chips */
.tags-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  min-height: 20px;
  padding: 4px 6px;
  border: 1px solid var(--tag-surface-border, #ccc);
  border-radius: 4px;
  background: var(--tag-surface-bg, #fff);
  cursor: text;
}
.tags-preview span {
  width: auto;
}

/* Keep individual tags compact and inline */
.tags-preview .tag {
  flex-shrink: 0;
  min-height: 24px;
  display: inline-flex !important;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--tag-chip-bg, #edf2ff);
  border: 1px solid var(--tag-chip-border, #cfd8f3);
  color: var(--tag-chip-text, #273445);
  font-size: 0.85rem;
}

.tag-placeholder {
  color: var(--tag-placeholder-text, #777);
  font-size: 0.9rem;
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
