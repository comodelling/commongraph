<template>
    <div>
      <div class="field">
        <strong>Type:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'edge_type'" @click="startEditing('edge_type')">{{ editedEdge.edge_type }}</span>
          <input v-else v-model="editedEdge.edge_type" @blur="stopEditing('edge_type')" ref="edge_typeInput" />
        </div>
      </div>
      <div class="field">
        <strong>CProb:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'cprob' && editedEdge.cprob" @click="startEditing('cprob')">{{ editedEdge.cprob }}</span>
          <input v-else-if="editingField === 'cprob'" v-model="editedEdge.cprob" @blur="stopEditing('cprob')" ref="cprobInput" />
          <button v-if="!editedEdge.cprob && editingField !== 'cprob'" @click="addCprob">Add</button> <!-- Modified button visibility condition -->
        </div>
      </div>
      <!-- <div class="field">
        <strong>Gradable:</strong>
        <div class="field-content">
          <input type="checkbox" v-model="editedEdge.gradable" />
        </div>
      </div> -->
      <!-- <div class="field">
      <strong>Proponents:</strong>
      <ul>
        <li v-for="(proponent, index) in editedEdge.proponents" :key="index" :class="{'invalid-proponent': !proponent.trim()}" class="field-content">
          <span v-if="editingField !== `proponent-${index}`" @click="startEditing(`proponent-${index}`)">{{ proponent || 'Click to edit' }}</span>
          <input v-else v-model="editedEdge.proponents[index]" @blur="stopEditing(`proponent-${index}`)" :ref="`proponent-${index}Input`" />
        </li>
      </ul>
    </div>
    <button class="add-proponent-button" @click="addProponent">+ Proponent</button> -->
      <div class="field">
        <strong>References:</strong>
        <ul>
          <li v-for="(reference, index) in editedEdge.references" :key="index" :class="{'invalid-reference': !reference.trim()}" class="field-content">
            <span v-if="editingField !== `reference-${index}`" @click="startEditing(`reference-${index}`)">{{ reference || 'Click to edit' }}</span>
            <input v-else v-model="editedEdge.references[index]" @blur="stopEditing(`reference-${index}`)" :ref="`reference-${index}Input`" />
          </li>
          <button class="add-reference-button" @click="addReference">+ Reference</button>
        </ul>
      </div>
      <div class="field" v-if="editedEdge.description || editingField === 'description'">
        <strong>Description:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'description'" @click="startEditing('description')">{{ editedEdge.description }}</span>
          <textarea v-else v-model="editedEdge.description" @blur="stopEditing('description')" ref="descriptionInput"></textarea>
        </div>
      </div>
      <button v-if="!editedEdge.description" class="add-description-button" @click="addDescription">+ Description</button>
      <button class="submit-button" @click="submit">Submit</button>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  import _ from 'lodash';
  
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
    //   addProponent() {
    //     if (this.editingField === null || !this.editingField.startsWith('proponent-')) {
    //       this.editedEdge.proponents.push('');
    //       this.$nextTick(() => {
    //         this.startEditing(`proponent-${this.editedEdge.proponents.length - 1}`);
    //       });
    //     }
    //   },
      addReference() {
        if (this.editingField === null || !this.editingField.startsWith('reference-')) {
          this.editedEdge.references.push('');
          this.$nextTick(() => {
            this.startEditing(`reference-${this.editedEdge.references.length - 1}`);
          });
        }
      },
      addDescription() {
        this.editedEdge.description = '';
        this.$nextTick(() => {
          this.startEditing('description');
        });
      },
      async submit() {
        this.editedEdge.references = this.editedEdge.references.filter(ref => ref.trim() !== '');
        console.log('submitting ', this.editedEdge);
        let response;
        try {
          if (this.editedEdge.new) {
            delete this.edge.new;
            response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/edges/`, this.editedEdge);
            console.log('Created edge returned:', response.data);
          } else {
            response = await axios.put(`${import.meta.env.VITE_BACKEND_URL}/edges`, this.editedEdge);
            console.log('Updated edge returned:', response.data);
          }
          this.$emit('publish', response.data);
          this.$emit('update-edge', response.data); // Emit an event to update the parent component's edge prop

          // window.location.href = `/edge/`;
        } catch (error) {
          console.error('Failed to update edge:', error);
        }
      },
      addCprob() {
        this.editedEdge.cprob = '';
        this.startEditing('cprob'); // Ensure the input field is shown immediately
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
          this.$emit('update-edited-edge', newEditedEdge);
        },
        deep: true,
      },
    },
  };
  </script>
  
  <style scoped>
  .field {
    display: flex;
    flex-direction: column;
    margin: 5px 0;
  }
  
  .field-content {
    flex: 1;
    margin-left: 10px;
    border: 1px solid #ccc;
    padding: 5px;
    border-radius: 4px;
  }
  
  .field-content span {
    display: inline-block;
    width: 100%;
    cursor: pointer;
  }
  
  .field-content input,
  .field-content textarea {
    width: 100%;
    box-sizing: border-box;
    resize: vertical;
    border: 1px solid #007bff;
    outline: none;
  }
  
  .invalid-proponent input,
  .invalid-reference input {
    border-color: lightcoral;
    background-color: #fff3e0;
  }
  
  button {
    background: #f9f9f9;
    border: 1px solid #ccc;
    cursor: pointer;
    padding: 5px;
    margin: 5px 0;
    display: block;
    width: 100%;
    text-align: left;
  }
  
  button.editing {
    background: #e9e9e9;
  }
  
  .add-proponent-button,
  .add-reference-button {
  display: block;
  margin: 10px auto;
  padding: 5px 10px;
  background: #f9f9f9;
  border: 1px solid #ccc;
  cursor: pointer;
  margin: 0 auto;
  display: block;
  width: 30%;
  text-align: center;
  font-size: 12px
}

/* TODO: share with NodeInfoEdit.vue */
  .add-description-button {  
    display: block;
    margin: 10px auto;
    padding: 5px 10px;
    background: #f9f9f9;
    border: 1px solid #ccc;
    cursor: pointer;
    margin: 0 auto;
    display: block;
    width: 30%;
    text-align: center;
  }
  
  .submit-button {
    margin-top: 20px;
    margin: 0 auto;
    display: block;
    width: 30%;
    text-align: center;
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    border: none;
    cursor: pointer;
    font-size: 16px;
  }
  
  .submit-button:hover {
    background-color: #0056b3;
  }
  </style>