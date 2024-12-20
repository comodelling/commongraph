<template>
  <div>
    <div class="field">
      <strong>Title:</strong>
      <div class="field-content">
        <span v-if="editingField !== 'title'" @click="startEditing('title')">{{
          editedNode.title
        }}</span>
        <input
          v-else
          v-model="editedNode.title"
          @blur="stopEditing('title')"
          ref="titleInput"
        />
      </div>
    </div>
    <div class="field">
      <strong>Type:</strong>
      <div class="field-content">
        <select
          v-model="editedNode.node_type"
          ref="typeInput"
          :disabled="!editedNode.new"
        >
          <option value="potentiality">Potentiality</option>
          <option value="objective">Objective</option>
          <option value="action">Action</option>
        </select>
      </div>
    </div>
    <div class="field">
      <strong>Scope:</strong>
      <div class="field-content">
        <span v-if="editingField !== 'scope'" @click="startEditing('scope')">{{
          editedNode.scope || "Click to edit scope"
        }}</span>
        <input
          v-else
          v-model="editedNode.scope"
          @blur="stopEditing('scope')"
          ref="scopeInput"
        />
      </div>
    </div>
    <div class="field">
      <strong>Status:</strong>
      <div class="field-content">
        <select v-model="editedNode.status" ref="statusInput">
          <option value="unspecified"></option>
          <option value="draft">Draft</option>
          <option value="live">Live</option>
          <option value="completed">Completed</option>
          <option value="legacy">Legacy</option>
        </select>
      </div>
    </div>
    <div class="field">
      <strong>Tags:</strong>
      <div class="tags-container">
        <span v-for="(tag, index) in editedNode.tags" :key="index" class="tag">
          <span
            v-if="editingField !== `tag-${index}`"
            @click="startEditing(`tag-${index}`)"
            >{{ tag }}</span
          >
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
    <div class="field">
      <strong>References:</strong>
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
            >{{ reference || "Click to edit" }}</span
          >
          <input
            v-else
            v-model="editedNode.references[index]"
            @blur="stopEditing(`reference-${index}`)"
            :ref="`reference-${index}Input`"
          />
        </li>
        <button class="add-reference-button" @click="addReference">
          + Reference
        </button>
      </ul>
    </div>
    <strong>Description:</strong>
    <div
      class="field"
      v-if="editedNode.description || editingField === 'description'"
    >
      <div class="field-content">
        <span
          v-if="editingField !== 'description'"
          @click="startEditing('description')"
          >{{ editedNode.description }}</span
        >
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
    <button class="submit-button" @click="submit">Submit</button>
  </div>
</template>

<script>
import axios from "axios";
import _ from "lodash";

export default {
  props: {
    node: Object,
  },
  data() {
    let editedNode = _.cloneDeep(this.node);
    editedNode.tags = editedNode.tags || [];
    return {
      editingField: null,
      editedNode: editedNode,
    };
  },
  methods: {
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
      // Remove empty references or tags
      this.editedNode.references = this.editedNode.references.filter(
        (ref) => ref.trim() !== "",
      );
      this.editedNode.tags = this.editedNode.tags.filter(
        (tag) => tag.trim() !== "",
      );
      this.editedNode.status = this.editedNode.status || null;
      if (this.editedNode.new) {
        try {
          const fromConnection = this.editedNode.fromConnection;
          delete this.editedNode.fromConnection;
          delete this.editedNode.new;
          delete this.editedNode.node_id;
          console.log("Submitting node for creation:", this.editedNode);
          const response = await axios.post(
            `${import.meta.env.VITE_BACKEND_URL}/nodes`,
            this.editedNode,
          );
          const target = response.data.node_id;

          if (fromConnection) {
            // create edge if node was created from a connection
            try {
              const newEdge = {
                source: parseInt(fromConnection.id),
                target: target,
                edge_type: fromConnection.edge_type,
              };
              console.log("Submitting edge for creation:", newEdge);
              const response = await axios.post(
                `${import.meta.env.VITE_BACKEND_URL}/edges`,
                newEdge,
              );
            } catch (error) {
              console.error("Failed to create edge:", error);
            }
          }
          window.location.href = `/node/${target}`;
        } catch (error) {
          console.error("Failed to create node:", error);
        }
      } else {
        try {
          const response = await axios.put(
            `${import.meta.env.VITE_BACKEND_URL}/nodes`,
            this.editedNode,
          );
          this.$emit("publish", response.data);
        } catch (error) {
          console.error("Failed to update node:", error);
        }
      }
    },
  },
  watch: {
    node: {
      handler(newNode) {
        this.editedNode = _.cloneDeep(newNode);
      },
      deep: true,
    },
    editedNode: {
      handler(newEditedNode) {
        this.$emit("update-edited-node", newEditedNode);
      },
      deep: true,
    },
  },
};
</script>
