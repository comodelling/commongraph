<template>
  <div class="demo-viewer">
    <!-- Demo Banner -->
    <div class="demo-banner">
      <div class="demo-banner-content">
        <div class="demo-info">
          <span class="demo-badge">📊 DEMO</span>
          <span class="demo-title">{{ demoMetadata?.title || demoId }}</span>
          <span class="demo-warning">⚠️ Changes won't be saved</span>
        </div>
      </div>
    </div>

    <!-- Main Demo Content -->
    <div class="demo-content" v-if="demoLoaded">
      <div class="focus">
        <div class="left-panel">
          <!-- Node or Edge Info Card -->
          <div class="card">
            <template v-if="isNode">
              <NodeInfo
                v-if="node"
                :node="node"
                :read-only="true"
                @update-node-from-editor="updateNodeFromEditor"
                @preview-node-update="previewNodeUpdate"
              />
              <div v-else class="info-placeholder">
                <p>👈 Click on a node in the graph to view its details</p>
              </div>
            </template>
            <template v-else-if="isEdge">
              <EdgeInfo
                v-if="edge"
                :edge="edge"
                :read-only="true"
                @update-edge-from-editor="updateEdgeFromEditor"
                @preview-edge-update="previewEdgeUpdate"
              />
              <div v-else class="info-placeholder">
                <p>👈 Click on an edge (arrow) to view its details</p>
              </div>
            </template>
            <template v-else>
              <div class="info-placeholder">
                <h3>{{ demoMetadata?.title }}</h3>
                <p>{{ demoMetadata?.description }}</p>
                <p style="margin-top: 20px">
                  <strong>Explore the graph:</strong>
                </p>
                <ul style="text-align: left; margin-left: 20px">
                  <li>Click nodes (boxes/circles) to view details</li>
                  <li>Click edges (arrows) to see relationships</li>
                  <li>Drag nodes to rearrange</li>
                  <li>Use compass to change layout direction</li>
                  <li>Zoom and pan to explore</li>
                </ul>
              </div>
            </template>
          </div>

          <!-- Polls (if configured and element selected) -->
          <template v-if="isNode && nodePollsCount && node && !node.new">
            <div
              class="card"
              v-for="(pollConfig, pollLabel) in nodePolls"
              :key="`node-${pollLabel}-${node.node_id}`"
            >
              <ElementPollPane
                :element="{ node_id: node.node_id }"
                :poll-label="pollLabel"
                :poll-config="pollConfig"
              />
            </div>
          </template>

          <template v-else-if="isEdge && edgePollsCount && edge && !edge.new">
            <div
              class="card"
              v-for="(pollConfig, pollLabel) in edgePolls"
              :key="`edge-${pollLabel}-${edge.source}-${edge.target}`"
            >
              <ElementPollPane
                :element="{
                  edge: { source: edge.source, target: edge.target },
                }"
                :poll-label="pollLabel"
                :poll-config="pollConfig"
              />
            </div>
          </template>
        </div>

        <div class="right-panel">
          <SubgraphRenderer
            style="width: 100%; height: 100%"
            :data="subgraphData"
            :read-only="true"
            @nodeClick="updateNodeFromBackend"
            @edgeClick="updateEdgeFromBackend"
            @newNodeCreated="openNewlyCreatedNode"
            @newEdgeCreated="openNewlyCreatedEdge"
            :updatedNode="updatedNode"
            :updatedEdge="updatedEdge"
          />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="demo-loading">
      <p>Loading demo: {{ demoId }}...</p>
    </div>

    <!-- Error State -->
    <div v-if="loadError" class="demo-error">
      <h3>Failed to load demo</h3>
      <p>{{ loadError }}</p>
      <router-link to="/demos">← Back to demos</router-link>
    </div>
  </div>
</template>

<script>
import { useConfig } from "../composables/useConfig";
import NodeInfo from "../components/node/NodeInfo.vue";
import EdgeInfo from "../components/edge/EdgeInfo.vue";
import ElementPollPane from "../components/poll/ElementPollPane.vue";
import SubgraphRenderer from "../components/graph/FlowEditor.vue";
import {
  formatFlowEdgeProps,
  formatFlowNodeProps,
} from "../composables/formatFlowComponents";

export default {
  components: {
    NodeInfo,
    EdgeInfo,
    ElementPollPane,
    SubgraphRenderer,
  },
  props: {
    demoId: {
      type: String,
      required: true,
    },
  },
  setup() {
    // Load config for the demo
    const { load: loadConfig, polls } = useConfig();
    return { loadConfig, polls };
  },
  data() {
    return {
      demoData: null,
      demoMetadata: null,
      demoLoaded: false,
      loadError: null,
      subgraphData: { nodes: [], edges: [] },
      node: null,
      edge: null,
      updatedNode: null,
      updatedEdge: null,
    };
  },
  computed: {
    isNode() {
      return this.$route.params.id && !this.$route.params.source_id;
    },
    isEdge() {
      return this.$route.params.source_id && this.$route.params.target_id;
    },
    nodePolls() {
      if (!this.polls) return {};
      return Object.fromEntries(
        Object.entries(this.polls).filter(([_, config]) =>
          config.node_types?.includes(this.node?.node_type),
        ),
      );
    },
    edgePolls() {
      if (!this.polls) return {};
      return Object.fromEntries(
        Object.entries(this.polls).filter(([_, config]) =>
          config.edge_types?.includes(this.edge?.edge_type),
        ),
      );
    },
    nodePollsCount() {
      return Object.keys(this.nodePolls).length;
    },
    edgePollsCount() {
      return Object.keys(this.edgePolls).length;
    },
  },
  async mounted() {
    console.log("DemoViewer mounted with demoId:", this.demoId);
    // Load config first
    await this.loadConfig();
    await this.loadDemo();
    await this.loadInitialElement();
  },
  watch: {
    "$route.params": {
      handler() {
        this.loadInitialElement();
      },
      deep: true,
    },
  },
  methods: {
    async loadDemo() {
      try {
        console.log("Loading demo:", this.demoId);
        // Load demo data from static JSON file
        const response = await fetch(`/data/demos/${this.demoId}.json`);
        console.log("Fetch response:", response);
        if (!response.ok) {
          throw new Error(
            `Demo not found: ${this.demoId} (status: ${response.status})`,
          );
        }

        this.demoData = await response.json();
        console.log("Demo data loaded:", this.demoData);
        this.demoMetadata = this.demoData.metadata;

        // Format nodes and edges for FlowEditor
        const formattedNodes = this.demoData.nodes.map((node) =>
          formatFlowNodeProps(node),
        );
        const formattedEdges = this.demoData.edges.map((edge) =>
          formatFlowEdgeProps(edge),
        );

        console.log(
          "Formatted nodes:",
          formattedNodes.length,
          "edges:",
          formattedEdges.length,
        );

        this.subgraphData = {
          nodes: formattedNodes,
          edges: formattedEdges,
        };

        this.demoLoaded = true;
        console.log("Demo loaded successfully");

        // Force a re-render by updating the subgraphData reference
        this.$nextTick(() => {
          this.subgraphData = { ...this.subgraphData };
        });
      } catch (error) {
        console.error("Failed to load demo:", error);
        this.loadError = error.message;
      }
    },

    async loadInitialElement() {
      if (!this.demoLoaded) return;

      if (this.$route.params.id) {
        this.updateNodeFromBackend(this.$route.params.id);
      } else if (this.$route.params.source_id && this.$route.params.target_id) {
        this.updateEdgeFromBackend(
          this.$route.params.source_id,
          this.$route.params.target_id,
        );
      } else {
        // No element selected - show intro
        this.node = null;
        this.edge = null;
      }
    },

    updateNodeFromBackend(nodeId) {
      const nodeData = this.demoData.nodes.find(
        (n) => n.node_id.toString() === nodeId.toString(),
      );
      if (nodeData) {
        this.node = nodeData;
        this.edge = null;
        this.$router.push({
          name: "DemoNode",
          params: { demoId: this.demoId, id: nodeId },
        });
      }
    },

    updateEdgeFromBackend(sourceId, targetId) {
      const edgeData = this.demoData.edges.find(
        (e) =>
          e.source.toString() === sourceId.toString() &&
          e.target.toString() === targetId.toString(),
      );
      if (edgeData) {
        this.edge = edgeData;
        this.node = null;
        this.$router.push({
          name: "DemoEdge",
          params: {
            demoId: this.demoId,
            source_id: sourceId,
            target_id: targetId,
          },
        });
      }
    },

    updateNodeFromEditor(updatedNode) {
      console.log("Node updated in demo (not saved):", updatedNode);
      this.node = updatedNode;
      this.updatedNode = updatedNode;
      // In demo mode, we don't actually save to backend
      // Just update local state for UI responsiveness
    },

    previewNodeUpdate(previewNode) {
      // In demo mode, show preview updates reactively
      this.updatedNode = { ...previewNode };
    },

    updateEdgeFromEditor(updatedEdge) {
      console.log("Edge updated in demo (not saved):", updatedEdge);
      this.edge = updatedEdge;
      this.updatedEdge = updatedEdge;
      // In demo mode, we don't actually save to backend
    },

    previewEdgeUpdate(previewEdge) {
      // In demo mode, show preview updates reactively
      this.updatedEdge = { ...previewEdge };
    },

    openNewlyCreatedNode(nodeData) {
      console.log("New node created in demo (not saved):", nodeData);
      // In demo mode, we acknowledge but don't persist
      alert(
        "⚠️ Demo Mode: New nodes won't be saved. This is just for exploration!",
      );
    },

    openNewlyCreatedEdge(edgeData) {
      console.log("New edge created in demo (not saved):", edgeData);
      // In demo mode, we acknowledge but don't persist
      alert(
        "⚠️ Demo Mode: New edges won't be saved. This is just for exploration!",
      );
    },
  },
};
</script>

<style scoped>
.demo-viewer {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.demo-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.demo-banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.demo-info {
  flex: 1;
  min-width: 300px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.demo-badge {
  background: rgba(255, 255, 255, 0.3);
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: bold;
  letter-spacing: 0.5px;
}

.demo-title {
  font-size: 16px;
  font-weight: 600;
}

.demo-description {
  margin: 0;
  font-size: 14px;
  opacity: 0.95;
  line-height: 1.4;
}

.demo-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.demo-warning {
  font-size: 11px;
  opacity: 0.95;
  background: rgba(255, 193, 7, 0.3);
  padding: 3px 10px;
  border-radius: 10px;
}

.demo-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.focus {
  display: flex;
  height: 100%;
  gap: 10px;
  padding: 10px;
  background-color: var(--background-color);
  overflow: hidden;
}

.left-panel {
  width: 30%;
  min-width: 300px;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  display: flex;
  min-width: 0;
  min-height: 500px;
  height: 100%;
}

.card {
  background-color: var(--card-background);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.info-placeholder {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.info-placeholder h3 {
  margin-top: 0;
  color: var(--text-color);
}

.info-placeholder p {
  margin: 10px 0;
  line-height: 1.6;
}

.info-placeholder ul {
  margin-top: 10px;
}

.info-placeholder li {
  margin: 8px 0;
  line-height: 1.5;
}

.demo-loading,
.demo-error {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}

.demo-error {
  color: var(--error-color);
}

.demo-error h3 {
  margin-bottom: 10px;
}

.demo-error a {
  margin-top: 20px;
  color: var(--primary-color);
  text-decoration: none;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .focus {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    max-width: none;
    min-height: 300px;
  }

  .demo-banner-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .demo-actions {
    align-items: flex-start;
    width: 100%;
  }
}
</style>
