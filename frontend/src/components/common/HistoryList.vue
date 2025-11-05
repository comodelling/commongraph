<template>
  <div>
    <ul>
      <li v-for="(event, index) in history" :key="event.event_id">
        {{ formatTimestamp(event.timestamp) }}:
        {{ formatState(event.state) }} by {{ event.username }}.
        <span
          v-if="event.state === 'updated' || event.state === 'created'"
          class="diff-link"
          @click="toggleDiff(event, index)"
        >
          ({{ diffVisible[event.event_id] ? "Hide" : "Diff" }})
        </span>
        <div v-if="diffVisible[event.event_id]" class="diff">
          <ul>
            <li v-for="diff in diffData[event.event_id]" :key="diff.field">
              <strong>{{ diff.field }}</strong
              >: {{ diff.from }} -> {{ diff.to }}
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </div>
</template>

<script>
import api from "../../api/axios";

export default {
  props: {
    // For nodes: pass nodeId
    nodeId: {
      type: Number,
      required: false,
    },
    // For edges: pass sourceId and targetId
    sourceId: {
      type: Number,
      required: false,
    },
    targetId: {
      type: Number,
      required: false,
    },
  },
  data() {
    return {
      history: [],
      diffVisible: {},
      diffData: {},
    };
  },
  computed: {
    apiEndpoint() {
      if (this.nodeId) {
        return `/nodes/${this.nodeId}/history`;
      } else if (this.sourceId && this.targetId) {
        return `/edges/${this.sourceId}/${this.targetId}/history`;
      }
      return null;
    },
  },
  async created() {
    if (!this.apiEndpoint) {
      console.error(
        "HistoryList: Invalid props - provide either nodeId or sourceId+targetId",
      );
      return;
    }

    try {
      const response = await api.get(this.apiEndpoint);
      this.history = response.data.reverse(); // Reverse the order to show the most recent first
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  },
  methods: {
    formatTimestamp(timestamp) {
      const date = new Date(timestamp);
      const dateString = date.toLocaleDateString("en-UK", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
      const timeString = date.toLocaleTimeString("en-UK", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      return `${dateString}, ${timeString}`;
    },
    formatState(state) {
      switch (state) {
        case "created":
          return "creation";
        case "updated":
          return "update";
        case "deleted":
          return "deletion";
        default:
          return state;
      }
    },
    toggleDiff(event, index) {
      const id = event.event_id;
      // Compute diff once
      if (!(id in this.diffData)) {
        const current = event.payload || {};
        const previous = this.history[index + 1]?.payload || {};
        const diffs = this.comparePayloads(previous, current);
        this.diffData[id] = diffs;
      }
      this.diffVisible[id] = !this.diffVisible[id];
    },
    comparePayloads(oldObj, newObj) {
      const diffs = [];
      const keys = new Set([...Object.keys(oldObj), ...Object.keys(newObj)]);
      keys.forEach((key) => {
        const oldVal = oldObj[key];
        const newVal = newObj[key];
        if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
          diffs.push({ field: key, from: oldVal, to: newVal });
        }
      });
      return diffs;
    },
  },
};
</script>

<style>
.diff-link {
  color: #42b983;
  cursor: pointer;
  margin-left: 1px;
}

/* Remove default ul padding and margin */
ul {
  padding-top: 20px;
  padding-left: 15px;
  /* margin: 0; */
}
</style>
