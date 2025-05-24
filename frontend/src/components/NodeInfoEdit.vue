<template>
  <div>
    <!-- Title Field -->
    <div class="field" v-if="isAllowed('title')">
      <strong :title="tooltips.node.title">Title:</strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'title'"
          @click="startEditing('title')"
          :class="{ 'error-text': titleError }"
        >
          {{ editedNode.title || "Click to add a title" }}
        </span>
        <input
          v-else
          v-model="editedNode.title"
          @blur="stopEditing('title')"
          ref="titleInput"
          :class="{ 'error-input': titleError }"
        />
      </div>
    </div>
    <!-- Type Field (always allowed) -->
    <div class="field">
      <strong :title="tooltips.node.type">Type:</strong>
      <div class="field-content">
         <select v-model="editedNode.node_type" ref="typeInput">
           <option
             v-for="(props, type) in nodeTypes"
             :key="type"
             :value="type"
             :title="tooltips.node[type] || tooltips.node.type"
           >
             {{ capitalise(type) }}
           </option>
         </select>
      </div>
    </div>
    <!-- Scope Field -->
    <div class="field" v-if="isAllowed('scope')">
      <strong :title="tooltips.node.scope">Scope:</strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'scope'"
          @click="startEditing('scope')"
          :class="{ 'error-text': scopeError }"
        >
          {{ editedNode.scope || "Click to add a scope" }}
        </span>
        <input
          v-else
          v-model="editedNode.scope"
          @blur="stopEditing('scope')"
          ref="scopeInput"
          :class="{ 'error-input': scopeError }"
        />
      </div>
    </div>
    <!-- Status Field -->
    <div class="field" v-if="isAllowed('status')">
      <strong :title="tooltips.node.status">Status:</strong>
      <div class="field-content">
        <select v-model="editedNode.status" ref="statusInput">
          <option value="unspecified" :title="tooltips.node.unspecified"></option>
          <option value="draft" :title="tooltips.node.draft">Draft</option>
          <option value="live" :title="tooltips.node.live">Live</option>
          <option value="completed" :title="tooltips.node.completed">Completed</option>
          <option value="legacy" :title="tooltips.node.legacy">Legacy</option>
        </select>
      </div>
    </div>
    <!-- Tags Field -->
    <div class="field" v-if="isAllowed('tags')">
      <strong :title="tooltips.node.tags">Tags:</strong>
      <div class="tags-container">
        <span v-for="(tag, index) in editedNode.tags" :key="index" class="tag">
          <span
            v-if="editingField !== `tag-${index}`"
            @click="startEditing(`tag-${index}`)"
          >
            {{ tag }}
          </span>
          <input
            v-else
            v-model="editedNode.tags[index]"
            @blur="stopEditing(`tag-${index}`)"
            :ref="`tag-${index}Input`"
            class="tag-input"
            :style="{ width: `${tag.length * 8 + 20}px` }"
          />
          <button class="delete-tag-button" @click="deleteTag(index)">x</button>
        </span>
        <button class="add-tag-button" @click="addTag">+ Tag</button>
      </div>
    </div>
    <!-- References Field -->
    <div class="field" v-if="isAllowed('references')">
      <strong :title="tooltips.node.references">References:</strong>
      <ul>
        <li
          v-for="(reference, index) in editedNode.references"
          :key="index"
          :class="{ 'invalid-reference': !reference.trim() }"
          class="field-content"
        >
          <span
            v-if="editingField !== `reference-${index}`"
            @click="startEditing(`reference-${index}`)"
          >
            {{ reference || "Click to edit" }}
          </span>
          <input
            v-else
            v-model="editedNode.references[index]"
            @blur="stopEditing(`reference-${index}`)"
            :ref="`reference-${index}Input`"
          />
        </li>
      </ul>
      <button class="add-reference-button" @click="addReference">
        + Reference
      </button>
    </div>
    <!-- Description Field -->
    <div v-if="isAllowed('description')">
      <strong :title="tooltips.node.description">Description:</strong>
      <div
        class="field"
        v-if="editedNode.description || editingField === 'description'"
      >
        <div class="field-content">
          <span
            v-if="editingField !== 'description'"
            @click="startEditing('description')"
          >
            {{ editedNode.description }}
          </span>
          <textarea
            v-else
            v-model="editedNode.description"
            @blur="stopEditing('description')"
            ref="descriptionInput"
          ></textarea>
        </div>
      </div>
      <button
        v-if="!editedNode.description"
        class="add-description-button"
        @click="addDescription"
      >
        + Description
      </button>
    </div>
    <button class="submit-button" @click="submit">{{ actionLabel }}</button>
  </div>
</template>

<script>
import api from "../axios";
import _ from "lodash";
import tooltips from "../assets/tooltips.json";
import { useAuth } from "../composables/useAuth";
import { useUnsaved } from "../composables/useUnsaved";
// Import the meta config composable
import { useConfig } from "../composables/useConfig";
import { onBeforeMount } from "vue";

export default {
  props: {
    node: Object,
  },
  // Use the setup() function solely to expose the meta config data.
   setup(props) {
     const { nodeTypes, load, defaultEdgeType } = useConfig();
     // block here until both nodeTypes & edgeTypes are populated
     onBeforeMount(load);
     return { nodeTypes, defaultEdgeType, load };
   },
  data() {
    let editedNode = _.cloneDeep(this.node);
    return {
      editingField: null,
      editedNode: editedNode,
      tooltips,
      titleError: false,
      scopeError: false,
      isSubmitting: false,
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
  },
  methods: {
    // Use the computed allowedFields to check if a field is allowed.
    isAllowed(field) {
      const allowed = this.allowedFields;       // ← allowedFields is already an Array
      return allowed.includes(field);
    },
    capitalise(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
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
    addTag() {
      this.editedNode.tags.push("");
      this.$nextTick(() => {
        this.startEditing(`tag-${this.editedNode.tags.length - 1}`);
      });
    },
    deleteTag(index) {
      this.editedNode.tags.splice(index, 1);
    },
    addReference() {
      this.editedNode.references.push("");
      this.$nextTick(() => {
        this.startEditing(`reference-${this.editedNode.references.length - 1}`);
      });
    },
    addDescription() {
      this.editedNode.description = "";
      this.$nextTick(() => {
        this.startEditing("description");
      });
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
          "Changing the node type may have unintended consequences. Are you sure you want to proceed?"
        );
        if (!confirmChange) {
          this.editedNode.node_type = this.node.node_type;
          return;
        }
      }
      // Cleanup tags, references, support.
      if (this.isAllowed("references")) {
        this.editedNode.references = this.editedNode.references.filter(
          (ref) => ref.trim() !== ""
        );
      }
      if (this.isAllowed("tags")) {
        this.editedNode.tags = this.editedNode.tags.filter(
          (tag) => tag.trim() !== ""
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
            `${import.meta.env.VITE_BACKEND_URL}/node`,
            this.editedNode,
            token
              ? { headers: { Authorization: `Bearer ${token}` } }
              : {}
          );
          const nodeReturned = response.data;
          const target = nodeReturned.node_id;
          nodeReturned.new = true;
          if (fromConnection) {
            try {
              const newEdge = {
                source:
                  fromConnection.handle_type === "source"
                    ? parseInt(fromConnection.id)
                    : target,
                target:
                  fromConnection.handle_type === "source"
                    ? target
                    : parseInt(fromConnection.id),
                edge_type: this.defaultEdgeType.value,
              };
              console.log("Creating edge (as connection to created target):", newEdge);
              await api.post(
                `${import.meta.env.VITE_BACKEND_URL}/edge`,
                newEdge,
                token
                  ? { headers: { Authorization: `Bearer ${token}` } }
                  : {}
              );
            } catch (error) {
              console.error("Failed to create edge:", error);
            }
          }
          this.$emit("publish-node", nodeReturned);
          this.editedNode = _.cloneDeep(nodeReturned);
          this.$router.push({ name: "NodeView", params: { id: target.toString() } });
        } catch (error) {
          console.error("Failed to create node:", error);
        }
      } else {
        try {
          const response = await api.put(
            `${import.meta.env.VITE_BACKEND_URL}/node`,
            this.editedNode
          );
          this.$emit("publish-node", response.data);
          this.editedNode = _.cloneDeep(response.data);
        } catch (error) {
          console.error("Failed to update node:", error);
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
      if (!confirm("This new node is not saved. Are you sure you want to leave?")) {
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

<style>
.error-input {
  border-color: red;
}
.error-text {
  color: red;
}
</style>