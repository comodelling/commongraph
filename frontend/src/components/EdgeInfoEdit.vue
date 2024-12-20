<template>
  <div>
    <div class="field">
      <strong>CProb:</strong>
      <div class="field-content">
        <span
          v-if="editingField !== 'cprob' && editedEdge.cprob"
          @click="startEditing('cprob')"
          >{{ editedEdge.cprob }}</span
        >
        <input
          v-else-if="editingField === 'cprob'"
          v-model="editedEdge.cprob"
          @blur="stopEditing('cprob')"
          ref="cprobInput"
        />
        <button
          v-if="!editedEdge.cprob && editingField !== 'cprob'"
          @click="addCprob"
        >
          Add
        </button>
        <!-- Modified button visibility condition -->
      </div>
    </div>
    <div class="field">
      <strong>References:</strong>
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
        <button class="add-reference-button" @click="addReference">
          + Reference
        </button>
      </ul>
    </div>
    <strong>Description:</strong>
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

export default {
  props: {
    edge: Object,
  },
  data() {
    return {
      editingField: null,
      editedEdge: _.cloneDeep(this.edge),
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
        this.$emit("publish", response.data);
        this.$emit("update-edge", response.data); // Emit an event to update the parent component's edge prop
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
    editedEdge: {
      handler(newEditedEdge) {
        this.$emit("update-edited-edge", newEditedEdge);
      },
      deep: true,
    },
  },
};
</script>
