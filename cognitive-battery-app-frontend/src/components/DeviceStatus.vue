<template>
  <div class="status-container" v-if="isRouteInList(['Setup', 'Baseline Instructions', 'Baseline', 'Instructions', 'Game'])">
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
      statusMessageEye: 'Eye tracker disconnected',
      statusMessageECG: 'ECG disconnected'
    };
  },
  mounted() {
    if (window.api && window.api.receive) {
      window.api.receive('fromMain', (data) => {
        if (data.eyeStatus) {
          this.statusMessageEye = data.eyeStatus;
        } else if (data.eyeError) {
          this.statusMessageEye = `Error: ${data.eyeError}`;
        }
        else if (data.sensorStatus) {
          this.statusMessageECG = data.sensorStatus;
        }
        else if (data.sensorError) {
          this.statusMessageECG = `Error: ${data.sensorError}`;
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
