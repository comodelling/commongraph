<template>
    <div>
      <div class="field">
        <strong>Title:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'title'" @click="startEditing('title')">{{ editedNode.title }}</span>
          <input v-else v-model="editedNode.title" @blur="stopEditing('title')" ref="titleInput" />
        </div>
      </div>
      <div class="field">
        <strong>Scope:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'scope'" @click="startEditing('scope')">{{ editedNode.scope }}</span>
          <input v-else v-model="editedNode.scope" @blur="stopEditing('scope')" ref="scopeInput" />
        </div>
      </div>
      <div class="field">
        <strong>Type:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'node_type'" @click="startEditing('node_type')">{{ editedNode.node_type }}</span>
          <input v-else v-model="editedNode.node_type" @blur="stopEditing('node_type')" ref="node_typeInput" />
        </div>
      </div>
      <div class="field">
        <strong>References:</strong>
        <ul>
          <li v-for="(reference, index) in editedNode.references" :key="index" :class="{'invalid-reference': !reference.trim()}" class="field-content">
            <span v-if="editingField !== `reference-${index}`" @click="startEditing(`reference-${index}`)">{{ reference }}</span>
            <input v-else v-model="editedNode.references[index]" @blur="stopEditing(`reference-${index}`)" :ref="`reference-${index}Input`" />
          </li>
        </ul>
        <button class="add-reference-button" @click="addReference">[Add Reference]</button>
      </div>
      <div class="field">
        <strong>Description:</strong>
        <div class="field-content">
          <span v-if="editingField !== 'description'" @click="startEditing('description')">{{ editedNode.description }}</span>
          <textarea v-else v-model="editedNode.description" @blur="stopEditing('description')" ref="descriptionInput"></textarea>
        </div>
      </div>
      <button class="submit-button" @click="publish">Submit</button>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    props: {
      node: Object,
    },
    data() {
      return {
        editingField: null,
        editedNode: { ...this.node },
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
        this.editedNode.references.push('');
        this.$nextTick(() => {
          this.startEditing(`reference-${this.editedNode.references.length - 1}`);
        });
      },
      async publish() {
        // Remove empty referencesw
        this.editedNode.references = this.editedNode.references.filter(ref => ref.trim() !== '');
        console.log('publishing ', this.editedNode);
        try {
          const response = await axios.put(`${import.meta.env.VITE_BACKEND_URL}/nodes`, this.editedNode);
          console.log('Updated nod returned:', response.data);
          this.$emit('publish', response.data);
        } catch (error) {
          console.error('Failed to update node:', error);
        }
      },
    },
    watch: {
      node: {
        handler(newNode) {
          this.editedNode = { ...newNode };
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
  
  .add-reference-button {
    display: block;
    margin: 10px auto;
    padding: 5px 10px;
    background: #f9f9f9;
    border: 1px solid #ccc;
    cursor: pointer;
  }
  
  .add-reference-button.invalid {
    background-color: lightorange;
  }
  
  .submit-button {
    margin-top: 20px;
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