<template>
    <div>
      <label>Type: <input v-model="edge.edge_type" /></label><br />
      <label>Gradable: <input type="checkbox" v-model="edge.gradable" /></label><br />
      <label>Proponents: <input v-model="proponents" /></label><br />
      <label>References: <textarea v-model="references"></textarea></label><br />
      <label>Description: <textarea v-model="edge.description"></textarea></label><br />
      <button @click="publish">Publish</button>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      edge: Object,
    },
    data() {
      return {
        proponents: this.edge.proponents ? this.edge.proponents.join(', ') : '',
        references: this.edge.references ? this.edge.references.join('\n') : '',
      };
    },
    methods: {
      publish() {
        this.edge.proponents = this.proponents.split(',').map(p => p.trim());
        this.edge.references = this.references.split('\n').map(r => r.trim());
        this.$emit('publish', this.edge);
      },
    },
  };
  </script>