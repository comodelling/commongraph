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
      <strong>Type:</strong>
      <div class="field-content">
        <select v-model="editedNode.node_type" ref="typeInput">
          <option value="action">Action</option>
          <option value="objective">Objective</option>
          <option value="potentiality">Potentiality</option>
          <!-- <option value="change">Change</option>
          <option value="proposal">Proposal</option> -->
        </select>
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
      <strong>Status:</strong>
      <div class="field-content">
        <select v-model="editedNode.status" ref="statusInput">
          <option value="unspecified">Unspecified</option>
          <option value="draft">Draft</option>
          <option value="live">Live</option>
          <option value="completed">Completed</option>
          <option value="legacy">Legacy</option>
        </select>
      </div>
    </div>
    <div class="field">
      <strong>References:</strong>
      <ul>
        <li v-for="(reference, index) in editedNode.references" :key="index" :class="{'invalid-reference': !reference.trim()}" class="field-content">
          <span v-if="editingField !== `reference-${index}`" @click="startEditing(`reference-${index}`)">{{ reference || 'Click to edit' }}</span>
          <input v-else v-model="editedNode.references[index]" @blur="stopEditing(`reference-${index}`)" :ref="`reference-${index}Input`" />
        </li>
        <!-- Added button to add a reference -->
        <button class="add-reference-button" @click="addReference">+ Reference</button>
      </ul>
    </div>
    <div class="field" v-if="editedNode.description || editingField === 'description'">
      <strong>Description:</strong>
      <div class="field-content">
        <span v-if="editingField !== 'description'" @click="startEditing('description')">{{ editedNode.description }}</span>
        <textarea v-else v-model="editedNode.description" @blur="stopEditing('description')" ref="descriptionInput"></textarea>
      </div>
    </div>
    <button v-if="!editedNode.description" class="add-description-button" @click="addDescription">+ Description</button>
    <button class="submit-button" @click="submit">Submit</button>
  </div>
</template>

<script>
import axios from 'axios';
import _ from 'lodash';

export default {
  props: {
    node: Object,
  },
  data() {
    return {
      editingField: null,
      editedNode: _.cloneDeep(this.node),
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
      // Modified to not add an empty reference by default
      this.editedNode.references.push('');
      this.$nextTick(() => {
        this.startEditing(`reference-${this.editedNode.references.length - 1}`);
      });
  },
  addDescription() {
    this.editedNode.description = '';
    this.$nextTick(() => {
      this.startEditing('description');
    });
  },
  async submit() {
    // Remove empty references
    this.editedNode.references = this.editedNode.references.filter(ref => ref.trim() !== '');
    this.editedNode.status = this.editedNode.status || null;
    console.log('number of references:', this.editedNode.references.length);
    if (this.editedNode.new) {
      try {
        const fromConnection = this.editedNode.fromConnection;
        //delete fromConnection from editedNode;
        delete this.editedNode.fromConnection;
        delete this.editedNode.new;
        delete this.editedNode.node_id;
        console.log('Submitting node for creation:', this.editedNode);
        const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/nodes`, this.editedNode);
        // console.log('Created node returned:', response.data);
        // this.$emit('publish', response.data);
        const target = response.data.node_id;

        if (fromConnection) // create edge if node was created from a connection
        {
          try {
            
            const newEdge = {
              source: parseInt(fromConnection.id),
              target: target,
              edge_type: fromConnection.edge_type,
            };
            console.log('Submitting edge for creation:', newEdge);
            const response = await axios.post(`${import.meta.env.VITE_BACKEND_URL}/edges`, newEdge);
            // console.log('Created edge returned:', response.data);
            // this.$emit('publish', response.data);
          } catch (error) {
            console.error('Failed to create edge:', error);
        }
        
      }
      window.location.href = `/node/${target}`;

      }
     catch (error) {
      console.error('Failed to create node:', error);
    }}
    else {
      try {
        // if node id starts by 'temp-node', create the node instead
        console.log('Submitting node for update:', this.editedNode);
        const response = await axios.put(`${import.meta.env.VITE_BACKEND_URL}/nodes`, this.editedNode);
        console.log('Updated node returned:', response.data);
        this.$emit('publish', response.data);
      } catch (error) {
        console.error('Failed to update node:', error);
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
        this.$emit('update-edited-node', newEditedNode);
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
  margin: 0 auto;
  display: block;
  width: 30%;
  text-align: center;
  font-size: 12px
}

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

.add-reference-button.invalid {
  background-color: lightorange;
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