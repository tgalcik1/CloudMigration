<template>
  <div class="status-container" v-if="isRouteInList(['Setup', 'Baseline', 'Video', 'Instructions', 'Game'])">
    <i class="fa-solid fa-heart-circle-xmark"></i>
    <p class="status-text">{{ statusMessageECG }}</p>
    <i class="fa-solid fa-eye-low-vision"></i>
    <p class="status-text">{{ statusMessageEye }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      statusMessageEye: 'Eye Tracker Disconnected',
      statusMessageECG: 'ECG Disconnected'
    };
  },
  mounted() {
    if (window.api && window.api.receive) {
      window.api.receive('fromMain', (data) => {
        if (data.status) {
          this.statusMessage = data.status;
        } else if (data.error) {
          this.statusMessage = `Error: ${data.error}`;
        }
      });
    }
  },
  methods: {
    isRouteInList(routeList) {
      return routeList.includes(this.$route.name);
    }
  }
};
</script>

<style scoped>
.status-container {
  display: flex;
  align-items: center;
}

.status-text {
  margin-left: 8px;
  margin-right: 16px;
}
</style>
