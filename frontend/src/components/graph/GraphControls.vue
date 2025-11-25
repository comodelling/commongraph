<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
<template>
  <div class="graph-controls">
    <div class="control-group">
      <label
        for="depth-control"
        title="Choose how many levels deep the graph should go"
        >Depth:</label
      >
      <select
        id="depth-control"
        v-model="localDepth"
        @change="onDepthChange"
        title="Choose how many levels deep the graph should go"
      >
        <option :value="1">1</option>
        <option :value="2">2</option>
        <option :value="3">3</option>
        <option :value="4">4</option>
        <option :value="5">5</option>
      </select>
    </div>
    <div class="control-separator"></div>
    <div class="control-group">
      <label for="node-color-control" title="Choose how to color nodes"
        >Node colour:</label
      >
      <select
        id="node-color-control"
        v-model="localNodeColorBy"
        @change="onNodeColorChange"
        title="Choose how to color nodes"
      >
        <option
          v-for="option in nodeColorOptions"
          :key="`node-color-${option.value}`"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
    <div class="control-separator"></div>
    <div class="control-group">
      <label for="edge-color-control" title="Choose how to color edges"
        >Edge colour:</label
      >
      <select
        id="edge-color-control"
        v-model="localEdgeColorBy"
        @change="onEdgeColorChange"
        title="Choose how to color edges"
      >
        <option
          v-for="option in edgeColorOptions"
          :key="`edge-color-${option.value}`"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
    <template v-if="showInfoButton">
      <div class="control-separator"></div>
      <button
        :class="['info-button', { active: infoMode }]"
        @click="onInfoToggle"
        title="Toggle type labels"
      >
        <Icon name="info" />
      </button>
    </template>
  </div>
</template>

<script>
import { computed, ref, watch } from "vue";
import { useConfig } from "../../composables/useConfig";
import Icon from "../common/Icon.vue";
import {
  COLOR_MODE_TYPE,
  humanizeLabel,
  toPollColorValue,
  toPropertyColorValue,
} from "../../utils/graphColoring";

export default {
  name: "GraphControls",
  components: {
    Icon,
  },
  props: {
    depth: {
      type: Number,
      default: 1,
    },
    nodeColorBy: {
      type: String,
      default: COLOR_MODE_TYPE,
    },
    edgeColorBy: {
      type: String,
      default: COLOR_MODE_TYPE,
    },
    showInfoButton: {
      type: Boolean,
      default: false,
    },
    infoMode: {
      type: Boolean,
      default: false,
    },
  },
  emits: [
    "update:depth",
    "update:nodeColorBy",
    "update:edgeColorBy",
    "update:infoMode",
  ],
  setup(props, { emit }) {
    const { nodeTypes, edgeTypes, nodePollTypes, edgePollTypes, load } =
      useConfig();
    load();

    const localDepth = ref(props.depth);
    const localNodeColorBy = ref(props.nodeColorBy);
    const localEdgeColorBy = ref(props.edgeColorBy);

    const nodeColorOptions = computed(() =>
      buildColorOptions(nodePollTypes.value, nodeTypes.value),
    );
    const edgeColorOptions = computed(() =>
      buildColorOptions(edgePollTypes.value, edgeTypes.value),
    );

    watch(
      () => props.depth,
      (newDepth) => {
        localDepth.value = newDepth;
      },
    );
    watch(
      () => props.nodeColorBy,
      (newVal) => {
        localNodeColorBy.value = newVal;
      },
    );
    watch(
      () => props.edgeColorBy,
      (newVal) => {
        localEdgeColorBy.value = newVal;
      },
    );

    const onDepthChange = () => {
      emit("update:depth", Number(localDepth.value));
    };

    const onNodeColorChange = () => {
      const normalized = ensureSelectionIsSupported(
        localNodeColorBy.value,
        nodeColorOptions.value,
      );
      localNodeColorBy.value = normalized;
      emit("update:nodeColorBy", normalized);
    };

    const onEdgeColorChange = () => {
      const normalized = ensureSelectionIsSupported(
        localEdgeColorBy.value,
        edgeColorOptions.value,
      );
      localEdgeColorBy.value = normalized;
      emit("update:edgeColorBy", normalized);
    };

    const onInfoToggle = () => {
      emit("update:infoMode", !props.infoMode);
    };

    return {
      localDepth,
      localNodeColorBy,
      localEdgeColorBy,
      nodeColorOptions,
      edgeColorOptions,
      onDepthChange,
      onNodeColorChange,
      onEdgeColorChange,
      onInfoToggle,
    };
  },
};

function ensureSelectionIsSupported(value, options) {
  const allowedValues = options.map((option) => option.value);
  return allowedValues.includes(value) ? value : COLOR_MODE_TYPE;
}

function buildColorOptions(pollSource = {}, typeSource = {}) {
  const pollOptions = Object.entries(pollSource || {})
    .map(([pollLabel, pollConfig]) => ({
      value: toPollColorValue(pollLabel),
      label: humanizeLabel(pollLabel),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  const seenProperties = new Map();
  Object.values(typeSource || {}).forEach((typeDef = {}) => {
    const propertyOptions = typeDef.property_options || {};
    Object.entries(propertyOptions).forEach(([propertyName, config]) => {
      const optionKeys = Object.keys(config?.options || {});
      if (!optionKeys.length || seenProperties.has(propertyName)) {
        return;
      }
      seenProperties.set(propertyName, config);
    });
  });

  const propertyOptions = Array.from(seenProperties.entries())
    .map(([propertyName, config]) => ({
      value: toPropertyColorValue(propertyName),
      label: humanizeLabel(propertyName),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return [
    { value: COLOR_MODE_TYPE, label: "Type" },
    ...pollOptions,
    ...propertyOptions,
  ];
}
</script>

<style scoped>
.graph-controls {
  display: flex;
  flex-wrap: nowrap;
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
  padding: 3px 5px;
  font-size: 11px;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 20px;
  height: 24px;
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

.info-button {
  padding: 3px 6px;
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  min-width: 24px;
  min-height: 24px;
}

.info-button:hover {
  border-color: var(--text-color);
}

.info-button.active {
  font-weight: 600;
  border-color: var(--text-color);
  background-color: var(--border-color);
}

:global(body.dark) .info-button {
  background-color: #2a2a2a;
  color: #fff;
  border-color: #555;
}

:global(body.dark) .info-button:hover {
  border-color: #777;
}

:global(body.dark) .info-button.active {
  background-color: #444;
  border-color: #888;
}
</style>
