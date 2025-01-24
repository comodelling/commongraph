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

    <div class="field">
      <strong :title="tooltips.edge.causal_strength_rating"
        >Causal Strength:</strong
      >
      <div class="field-content">
        <select v-model="editedEdge.causal_strength_rating" ref="causalInput">
          <option value="" :title="tooltips.edge.unrated"></option>
          <option value="A" :title="tooltips.edge.A">
            A ({{ tooltips.edge.A }})
          </option>
          <option value="B" :title="tooltips.edge.B">
            B ({{ tooltips.edge.B }})
          </option>
          <option value="C" :title="tooltips.edge.C">
            C ({{ tooltips.edge.C }})
          </option>
          <option value="D" :title="tooltips.edge.D">
            D ({{ tooltips.edge.D }})
          </option>
          <option value="E" :title="tooltips.edge.E">
            E ({{ tooltips.edge.E }})
          </option>
        </select>
      </div>
    </div>

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
  emits: ["publish-edge"],
  data() {
    const editedEdge = _.cloneDeep(this.edge);
    // editedEdge.cprob =
    //   this.edge.cprob !== undefined && this.edge.cprob !== null
    //     ? this.edge.cprob * 100
    //     : undefined;
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
        // if (
        // field === "cprob" &&
        // (this.editedEdge.cprob < 0 || this.editedEdge.cprob > 100)
        // ) {
        // this.editedEdge.cprob = undefined;
        // }
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
      // this.editedEdge.cprob = this.editedEdge.cprob / 100;
      console.log("submitting ", this.editedEdge);

      console.log(
        "current edited support:",
        this.editedEdge.causal_strength_rating,
      );
      this.editedEdge.causal_strength_rating =
        this.editedEdge.causal_strength_rating || null;
      if (this.editedEdge.causal_strength_rating === "") {
        this.editedEdge.causal_strength_rating = null;
      }

      let response;
      try {
        if (this.editedEdge.new) {
          delete this.edge.new;
          response = await axios.post(
            `${import.meta.env.VITE_BACKEND_URL}/edge/`,
            this.editedEdge,
          );
          console.log("Created edge returned:", response.data);
        } else {
          response = await axios.put(
            `${import.meta.env.VITE_BACKEND_URL}/edge`,
            this.editedEdge,
          );
          console.log("Updated edge returned:", response.data);
        }
        this.$emit("publish-edge", response.data);
      } catch (error) {
        console.error("Failed to update edge:", error);
      }
    },
    // addCprob() {
    // this.editedEdge.cprob = 0;
    // this.startEditing("cprob"); // Ensure the input field is shown immediately
    // },
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
