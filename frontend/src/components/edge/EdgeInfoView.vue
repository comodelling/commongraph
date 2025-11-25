<!--
SPDX-FileCopyrightText: 2025 CommonGraph contributors: https://github.com/comodelling/commongraph/CONTRIBUTORS.md

SPDX-License-Identifier: AGPL-3.0-or-later
-->
<template>
  <div class="edge-info-view">
    <!-- Type -->
    <div class="field-row">
      <strong :title="edgeTypeTooltip">Type:</strong>
      <span class="field-value">{{ edge.edge_type }}</span>
    </div>
    <!-- References -->
    <div
      class="field-row"
      v-if="
        isAllowed('references') &&
        localEdge.references &&
        localEdge.references.length
      "
    >
      <strong :title="tooltips.edge.references">References:</strong>
      <div class="field-value">
        <ul class="references-list">
          <li
            v-for="reference in localEdge.references.filter((ref: any) =>
              ref.trim(),
            )"
            :key="reference"
          >
            {{ reference.trim() }}
          </li>
        </ul>
      </div>
    </div>
    <!-- Description -->
    <div
      class="field-row"
      v-if="isAllowed('description') && localEdge.description"
    >
      <strong :title="tooltips.edge.description">Description:</strong>
      <span class="field-value">{{ localEdge.description }}</span>
    </div>
    <!-- Tags -->
    <div class="field-row" v-if="isAllowed('tags') && edge.tags?.length">
      <strong :title="tooltips.node.tags">Tags:</strong>
      <div class="field-value tags-container">
        <span v-for="tag in edge.tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
    <!-- Custom option-based properties -->
    <template
      v-for="customProp in customPropertyEntries"
      :key="customProp.name"
    >
      <div class="field-row" v-if="hasCustomValue(customProp.name)">
        <strong :title="customProp.config.question || customProp.name">
          {{ capitalise(customProp.name) }}:
        </strong>
        <span class="field-value">
          {{
            getCustomPropertyDisplay(
              customProp.config,
              getCustomValue(customProp.name),
            )
          }}
        </span>
      </div>
    </template>
    <!-- License Notice -->
    <p class="license-notice" v-if="shouldShowLicenseNotice">
      Edge descriptions are available under the
      <a
        :href="getLicenseUrl(license)"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ license }}
      </a>
      license.
    </p>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from "vue";
import { useConfig } from "../../composables/useConfig";
import tooltips from "../../assets/tooltips.json";

type CustomPropertyEntry = {
  name: string;
  config: Record<string, any>;
};

export default defineComponent({
  name: "EdgeInfoView",
  props: {
    edge: {
      type: Object,
      required: true,
    },
    sourceId: Number,
    targetId: Number,
  },
  emits: ["publish-edge"],
  setup(props) {
    const { edgeTypes, load, license, getLicenseUrl } = useConfig();
    onMounted(load);

    const allowed = computed(() => {
      // Ensure edgeTypes are loaded and the edge has a type.
      if (!edgeTypes.value || !props.edge.edge_type)
        return Object.keys(props.edge);
      return (
        edgeTypes.value[props.edge.edge_type].properties ||
        Object.keys(props.edge)
      );
    });

    function isAllowed(prop: string): boolean {
      return allowed.value.includes(prop);
    }

    const edgeTypeTooltip = computed(() => {
      return (tooltips.edge as any)[props.edge.edge_type] || tooltips.edge.type;
    });

    const descriptionAllowed = computed(() => {
      if (!edgeTypes.value || !props.edge.edge_type) return false;
      const propsList = edgeTypes.value[props.edge.edge_type].properties || [];
      return propsList.includes("description");
    });

    const hasDescriptionValue = computed(() => {
      const desc = props.edge.description;
      return typeof desc === "string" && desc.trim().length > 0;
    });

    const shouldShowLicenseNotice = computed(() => {
      return Boolean(
        license.value && descriptionAllowed.value && hasDescriptionValue.value,
      );
    });

    const customPropertyEntries = computed<CustomPropertyEntry[]>(() => {
      if (!edgeTypes.value || !props.edge.edge_type) return [];
      const typeDef = edgeTypes.value[props.edge.edge_type] || {};
      const propertyOptions: Record<string, any> =
        typeDef.property_options || {};
      return Object.entries(propertyOptions)
        .filter(([name, config]) => {
          const optionMap = (config as Record<string, any>)?.options || {};
          return (
            allowed.value.includes(name) && Object.keys(optionMap).length > 0
          );
        })
        .map(([name, config]) => ({
          name,
          config: config as Record<string, any>,
        }));
    });

    // formatCustomPropertyLabel removed: label now always uses property name

    function getCustomValue(propName: string): any {
      return (props.edge as Record<string, any>)[propName];
    }

    function hasCustomValue(propName: string): boolean {
      const value = getCustomValue(propName);
      if (value === undefined || value === null) {
        return false;
      }
      if (typeof value === "string") {
        return value.trim().length > 0;
      }
      return true;
    }

    function getCustomPropertyDisplay(
      config: Record<string, any>,
      value: any,
    ): string {
      if (value === undefined || value === null) {
        return "";
      }
      const options = config?.options || {};
      const key = typeof value === "string" ? value : String(value);
      return options[key] ?? String(value);
    }

    function capitalise(str: string) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
    return {
      isAllowed,
      edgeTypeTooltip,
      license,
      getLicenseUrl,
      shouldShowLicenseNotice,
      customPropertyEntries,
      getCustomPropertyDisplay,
      getCustomValue,
      hasCustomValue,
      capitalise,
    };
  },
  data() {
    return {
      // localEdge is used so that modifications from watchers are applied.
      localEdge: this.edge,
      tooltips,
    };
  },
  computed: {
    sourceLink(): string {
      return ""; // your implementation here
    },
    targetLink(): string {
      return `/node/${this.localEdge.target}`;
    },
  },
  watch: {
    edge: {
      handler(newEdge) {
        this.localEdge = newEdge;
      },
      deep: true,
    },
  },
});
</script>

<style scoped>
.field-row {
  display: flex;
  align-items: flex-start;
  margin: 8px 0;
  gap: 10px;
}

.field-row strong {
  min-width: 80px;
  flex-shrink: 0;
}

.field-value {
  flex: 1;
}

/* License notice styling */
.license-notice {
  font-size: 0.75rem;
  color: #999;
  margin-top: 12px;
  line-height: 1.3;
}

.license-notice a {
  color: #0066cc;
  text-decoration: none;
  font-weight: 500;
}

.license-notice a:hover {
  text-decoration: underline;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
</style>
