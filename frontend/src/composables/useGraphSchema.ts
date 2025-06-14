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
  target?: string
): string[] {
  if (!loaded.value) return [];

  // both ends known
  if (source && target) {
    return schema.value.edge_types
      .filter(e => e.source_type === source && e.target_type === target)
      .map(e => e.label);
  }
  // only source known → any edge *from* that source
  if (source && !target) {
    return Array.from(
      new Set(
        schema.value.edge_types
          .filter(e => e.source_type === source)
          .map(e => e.label)
      )
    );
  }
  // only target known → any edge *to* that target
  if (!source && target) {
    return Array.from(
      new Set(
        schema.value.edge_types
          .filter(e => e.target_type === target)
          .map(e => e.label)
      )
    );
  }
  // neither known → all edge types
  return Array.from(new Set(schema.value.edge_types.map(e => e.label)));
}

export function getAllowedTargetNodeTypes(
  source: string
): string[] {
  if (!loaded.value) return [];
  // all target types you can connect _from_ this source
  return Array.from(
    new Set(
      schema.value.edge_types
        .filter((e) => e.source_type === source)
        .map((e) => e.target_type)
    )
  );
}

export function getAllowedSourceNodeTypes(
  target: string
): string[] {
  if (!loaded.value) return [];
  return Array.from(
    new Set(
      schema.value.edge_types
        .filter((e) => e.target_type === target)
        .map((e) => e.source_type)
    )
  );
}