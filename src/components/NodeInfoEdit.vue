<template>
    <div>
      <label>Title: <input v-model="node.title" /></label><br />
      <label>Scope: <input v-model="node.scope" /></label><br />
      <label>Type: <input v-model="node.node_type" /></label><br />
      <label>Gradable: <input type="checkbox" v-model="node.gradable" /></label><br />
      <label>Proponents: <input v-model="proponents" /></label><br />
      <label>References: <textarea v-model="references"></textarea></label><br />
      <label>Description: <textarea v-model="node.description"></textarea></label><br />
      <button class="submit-button" @click="publish">Submit</button>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      node: Object,
    },
    data() {
      return {
        proponents: this.node.proponents ? this.node.proponents.join(', ') : '',
        references: this.node.references ? this.node.references.join('\n') : '',
      };
    },
    methods: {
      async publish() {
        this.node.proponents = this.proponents.split(',').map(p => p.trim());
        this.node.references = this.references.split('\n').map(r => r.trim());
        //TODO: Implement the following code
        // try {
        //   const response = await axios.put(`/api/nodes/${this.node.id}`, this.node);
        //   this.$emit('publish', response.data);
        // } catch (error) {
        //   console.error('Failed to update node:', error);
        // }
      },
    },
  };
  </script>
  
