<template>
  <div class="graph-controls">
    <div class="control-group">
      <label for="depth-control">Depth:</label>
      <select id="depth-control" v-model="localDepth" @change="onDepthChange">
        <option :value="1">1</option>
        <option :value="2">2</option>
        <option :value="3">3</option>
        <option :value="4">4</option>
        <option :value="5">5</option>
      </select>
    </div>
    <div class="control-separator"></div>
    <div class="control-group">
      <label for="color-control">Color:</label>
      <select
        id="color-control"
        v-model="localColorBy"
        @change="onColorByChange"
      >
        <option value="type">Type</option>
        <option value="rating">Rating</option>
      </select>
    </div>
  </div>
</template>

<script>
export default {
  name: "GraphControls",
  props: {
    depth: {
      type: Number,
      default: 1,
    },
    colorBy: {
      type: String,
      default: "type",
      validator: (value) => ["type", "rating"].includes(value),
    },
  },
  emits: ["update:depth", "update:colorBy"],
  data() {
    return {
      localDepth: this.depth,
      localColorBy: this.colorBy,
    };
  },
  watch: {
    depth(newVal) {
      this.localDepth = newVal;
    },
    colorBy(newVal) {
      this.localColorBy = newVal;
    },
  },
  methods: {
    onDepthChange() {
      this.$emit("update:depth", Number(this.localDepth));
    },
    onColorByChange() {
      this.$emit("update:colorBy", this.localColorBy);
    },
  },
};
</script>

<style scoped>
.graph-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 0;
  background-color: transparent;
  border: none;
  box-shadow: none;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 3px;
}

.control-separator {
  width: 1px;
  height: 20px;
  background-color: var(--border-color);
}

.control-group label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-color);
  white-space: nowrap;
}

.control-group select {
  padding: 4px 6px;
  font-size: 11px;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 20px;
}

.control-group select:hover {
  border-color: var(--text-color);
}

.control-group select:focus {
  outline: none;
  border-color: var(--primary-color, #007bff);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

:global(body.dark) .control-group select {
  background-color: #2a2a2a;
  border-color: #555;
  color: #fff;
}

:global(body.dark) .control-group select:hover {
  border-color: #777;
}
</style>
