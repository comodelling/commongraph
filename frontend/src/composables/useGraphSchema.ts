import { ref } from "vue";
import api from "../api/axios";

type RawSchema = {
  node_types: string[];
  edge_types: Array<{
    source_type: string;
    target_type: string;
    label: string;
  }>;
};

const schema = ref<RawSchema>({ node_types: [], edge_types: [] });
const loaded = ref(false);

export async function loadGraphSchema() {
  if (loaded.value) return;
  const { data } = await api.get<RawSchema>("/graph/schema");
  schema.value = data;
  loaded.value = true;
}

export function getAllowedEdgeTypes(
  source?: string,
  target?: string,
): string[] {
  if (!loaded.value) return [];

  // both ends known
  if (source && target) {
    return schema.value.edge_types
      .filter((e) => e.source_type === source && e.target_type === target)
      .map((e) => e.label);
  }
  // only source known → any edge *from* that source
  if (source && !target) {
    return Array.from(
      new Set(
        schema.value.edge_types
          .filter((e) => e.source_type === source)
          .map((e) => e.label),
      ),
    );
  }
  // only target known → any edge *to* that target
  if (!source && target) {
    return Array.from(
      new Set(
        schema.value.edge_types
          .filter((e) => e.target_type === target)
          .map((e) => e.label),
      ),
    );
  }
  // neither known → all edge types
  return Array.from(new Set(schema.value.edge_types.map((e) => e.label)));
}

export function getAllowedTargetNodeTypes(source: string): string[] {
  if (!loaded.value) return [];
  // If no source type is known, show all node types (so user can pick).
  if (!source) {
    return schema.value.node_types;
  }
  // If we have no edge types at all, something's wrong - return all node types as fallback
  if (!schema.value.edge_types || schema.value.edge_types.length === 0) {
    return schema.value.node_types;
  }
  // Otherwise, show only the node types that have a valid edge from 'source'.
  const targets = Array.from(
    new Set(
      schema.value.edge_types
        .filter((e) => e.source_type === source)
        .map((e) => e.target_type),
    ),
  );
  // If no edges found for this source but schema is loaded, return all node types
  // (this handles the case where an edge type has no "between" constraint)
  if (targets.length === 0 && schema.value.edge_types.length > 0) {
    return schema.value.node_types;
  }
  return targets;
}

export function getAllowedSourceNodeTypes(target: string): string[] {
  if (!loaded.value) return [];
  if (!target) {
    return schema.value.node_types;
  }
  // If we have no edge types at all, something's wrong - return all node types as fallback
  if (!schema.value.edge_types || schema.value.edge_types.length === 0) {
    return schema.value.node_types;
  }
  const sources = Array.from(
    new Set(
      schema.value.edge_types
        .filter((e) => e.target_type === target)
        .map((e) => e.source_type),
    ),
  );
  // If no edges found for this target but schema is loaded, return all node types
  // (this handles the case where an edge type has no "between" constraint)
  if (sources.length === 0 && schema.value.edge_types.length > 0) {
    return schema.value.node_types;
  }
  return sources;
}

export function isGraphSchemaLoaded(): boolean {
  return loaded.value;
}
