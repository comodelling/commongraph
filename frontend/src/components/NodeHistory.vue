<template>
  <div>
    <h2>Node History</h2>
    <ul>
      <li v-for="event in history" :key="event.event_id">
        {{ formatTimestamp(event.timestamp) }}:
        {{ formatState(event.state) }} by user {{ event.username }}.
      </li>
    </ul>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: {
    nodeId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      history: [],
    };
  },
  async created() {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_BACKEND_URL}/node/${this.nodeId}/history`,
      );
      this.history = response.data.reverse(); // Reverse the order to show the most recent first
    } catch (error) {
      console.error("Failed to fetch node history:", error);
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
  },
};
</script>
