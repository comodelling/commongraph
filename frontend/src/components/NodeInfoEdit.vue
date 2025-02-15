<template>
  <div>
    <div class="field">
      <strong :title="tooltips.node.type">Type:</strong>
      <div class="field-content">
        <select v-model="editedNode.node_type" ref="typeInput">
          <option value="objective" :title="tooltips.node.objective">
            Objective
          </option>
          <option value="action" :title="tooltips.node.action">Action</option>
          <option value="potentiality" :title="tooltips.node.potentiality">
            Potentiality
          </option>
        </select>
      </div>
    </div>
    <!-- <h2 :title="nodeTypeTooltip" v-else>
      {{ capitalise(editedNode.node_type) }}
    </h2> -->

    <div class="field">
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

    <div class="field">
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

    <div class="field">
      <strong :title="tooltips.node.status">Status:</strong>
      <div class="field-content">
        <select v-model="editedNode.status" ref="statusInput">
          <option
            value="unspecified"
            :title="tooltips.node.unspecified"
          ></option>
          <option value="draft" :title="tooltips.node.draft">Draft</option>
          <option value="live" :title="tooltips.node.live">Live</option>
          <option value="completed" :title="tooltips.node.completed">
            Completed
          </option>
          <option value="legacy" :title="tooltips.node.legacy">Legacy</option>
        </select>
      </div>
    </div>
    <div class="field">
      <strong :title="tooltips.node.tags">Tags:</strong>
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
    <strong :title="tooltips.node.references">References:</strong>
    <div class="field">
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
      </ul>
    </div>
    <div>
      <button class="add-reference-button" @click="addReference">
        + Reference
      </button>
    </div>
    <strong :title="tooltips.node.description">Description:</strong>
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
import tooltips from "../assets/tooltips.json";

export default {
  props: {
    node: Object,
  },
  data() {
    let editedNode = _.cloneDeep(this.node);
    return {
      editingField: null,
      editedNode: editedNode,
      tooltips,
      titleError: false,
      scopeError: false,
    };
  },
  computed: {
    nodeTypeTooltip() {
      return this.tooltips.node[this.node.node_type] || this.tooltips.node.type;
    },
  },
  methods: {
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
      console.log("Adding reference");
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
      const trimmedTitle = this.editedNode.title.trim();
      const trimmedScope = this.editedNode.scope.trim();
      this.editedNode.title = trimmedTitle;
      this.editedNode.scope = trimmedScope;
      this.titleError =
        trimmedTitle === "" ||
        trimmedTitle === null ||
        trimmedTitle === undefined;
      this.scopeError =
        trimmedScope === "" ||
        trimmedScope === null ||
        trimmedScope === undefined;
      if (this.titleError || this.scopeError) {
        return;
      }

      if (
        !this.editedNode.new &&
        this.editedNode.node_type !== this.node.node_type
      ) {
        const confirmChange = confirm(
          "Changing the node type may have unintended consequences. Are you sure you want to proceed?",
        );
        if (!confirmChange) {
          this.editedNode.node_type = this.node.node_type;
          return;
        }
      }

      console.log("current edited support:", this.editedNode.support);
      this.editedNode.support = this.editedNode.support || null;
      if (this.editedNode.support === "") {
        this.editedNode.support = null;
      }

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

          const token = localStorage.getItem("authToken");
          const response = await axios.post(
            `${import.meta.env.VITE_BACKEND_URL}/node`,
            this.editedNode,
            token ? { headers: { Authorization: `Bearer ${token}` } } : {},
          );
          const nodeReturned = response.data;
          const target = nodeReturned.node_id;

          nodeReturned.new = true;

          if (fromConnection) {
            // create edge if node was created from a connection
            try {
              const newEdge = {
                source:
                  fromConnection.edge_type === "imply"
                    ? parseInt(fromConnection.id)
                    : target,
                target:
                  fromConnection.edge_type === "imply"
                    ? target
                    : parseInt(fromConnection.id),
                edge_type: "imply",
              };
              console.log("Submitting edge for creation:", newEdge);
              await axios.post(
                `${import.meta.env.VITE_BACKEND_URL}/edge`,
                newEdge,
                token ? { headers: { Authorization: `Bearer ${token}` } } : {},
              );
            } catch (error) {
              console.error("Failed to create edge:", error);
            }
          }
          // window.location.href = `/node/${target}`;
          // this.$emit("new-node-submitted", response.data);
          // console.log("new node back from backend", response.data);
          // await

          this.$emit("publish-node", nodeReturned);
          this.$router.push({
            name: "NodeView",
            params: { id: target.toString() },
          });
          // console.log("Route push completed");

          // console.log("Event emitted");
        } catch (error) {
          console.error("Failed to create node:", error);
        }
      } else {
        try {
          const response = await axios.put(
            `${import.meta.env.VITE_BACKEND_URL}/node`,
            this.editedNode,
          );
          this.$emit("publish-node", response.data);
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
    // editedNode: {
    //   handler(newEditedNode, oldEditedNode) {
    //     // console.log("editedNode changed", newEditedNode, oldEditedNode);
    //     // if (newEditedNode.title !== oldEditedNode.title || newEditedNode.status !== oldEditedNode.status) {
    //     this.$emit("update-node-on-graph", newEditedNode);
    //     // console.log("emitted update-node-on-graph");
    //     // }
    //   },
    //   deep: true,
    // },
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
