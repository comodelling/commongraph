<template>
  <div>
    <h2 :title="edgeTypeTooltip">
      {{ edge.edge_type === "require" ? "Condition" : "Implication" }}
    </h2>
    <div class="field">
      <template v-if="edge.edge_type === 'require'">
        <strong :title="tooltips.edge.cprob_condition">
          Cond.Proba(condition|source)
        </strong>
      </template>
      <template v-if="edge.edge_type === 'imply'">
        <strong :title="tooltips.edge.cprob_implication">
          Cond.Proba(implication|source)
        </strong>
      </template>
      <div class="field-content">
        <span v-if="editingField !== 'cprob'" @click="startEditing('cprob')">
          {{ editedEdge.cprob }}%
        </span>
        <div v-else style="display: flex; align-items: center">
          <input
            type="number"
            v-model.number="editedEdge.cprob"
            @blur="stopEditing('cprob')"
            ref="cprobInput"
            min="0"
            max="100"
            style="width: 50px; margin-right: 5px"
          />
          <span>%</span>
        </div>
      </div>
    </div>
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
import axios from "axios";
import _ from "lodash";
import tooltips from "../assets/tooltips.json"; // Add this line

export default {
  props: {
    edge: Object,
  },
  data() {
    const editedEdge = _.cloneDeep(this.edge);
    editedEdge.cprob =
      this.edge.cprob !== undefined ? this.edge.cprob * 100 : undefined;
    return {
      editingField: null,
      editedEdge: editedEdge,
      tooltips,
    };
  },
  computed: {
    edgeTypeTooltip() {
      return this.tooltips.edge[this.edge.edge_type] || this.tooltips.edge.type;
    },
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
      this.editedEdge.references = this.editedEdge.references.filter(
        (ref) => ref.trim() !== "",
      );
      this.editedEdge.cprob = this.editedEdge.cprob / 100;
      console.log("submitting ", this.editedEdge);
      let response;
      try {
        if (this.editedEdge.new) {
          delete this.edge.new;
          response = await axios.post(
            `${import.meta.env.VITE_BACKEND_URL}/edges/`,
            this.editedEdge,
          );
          console.log("Created edge returned:", response.data);
        } else {
          response = await axios.put(
            `${import.meta.env.VITE_BACKEND_URL}/edges`,
            this.editedEdge,
          );
          console.log("Updated edge returned:", response.data);
        }
        this.$emit("publish-edge", response.data);
      } catch (error) {
        console.error("Failed to update edge:", error);
      }
    },
    addCprob() {
      this.editedEdge.cprob = "";
      this.startEditing("cprob"); // Ensure the input field is shown immediately
    },
  },
  watch: {
    edge: {
      handler(newEdge) {
        this.editedEdge = _.cloneDeep(newEdge);
      },
      deep: true,
    },
    // editedEdge: {
    //   handler(newEditedEdge) {
    //     this.$emit("update-edited-edge", newEditedEdge);  // not handled
    //   },
    //   deep: true,
    // },
  },
};
</script>
