<template>
    <div class="status-container">
      <i 
        v-if="iotStatus === 'IoT connected'" 
        :style="{ color: signalColor }" 
        class="fa-solid fa-signal">
      </i>
      <p :style="{ color: signalColor }" class="status-text">{{ signalStrength }} dB</p>
    </div>
  </template>
  
  <script>
  import { mapState } from 'vuex';
  
  export default {
    data() {
      return {
        signalStrength: -90,
        increasing: true,
      };
    },
    computed: {
      ...mapState(['iotStatus']),
      signalColor() {
        return this.interpolateColor(this.signalStrength);
      }
    },
    mounted() {
      this.animateSignalStrength();
    },
    methods: {
      animateSignalStrength() {
        const updateFrequency = 50;
        const changeAmount = 1;
  
        if (this.increasing) {
          this.signalStrength += changeAmount;
          if (this.signalStrength >= 0) {
            this.increasing = false;
          }
        } else {
          this.signalStrength -= changeAmount;
          if (this.signalStrength <= -100) {
            this.increasing = true;
          }
        }
  
        setTimeout(this.animateSignalStrength, updateFrequency);
      },
      interpolateColor(signalStrength) {
        const startColor = { r: 255, g: 0, b: 0 };
        const endColor = { r: 0, g: 255, b: 0 };
  
        const minStrength = -100;
        const maxStrength = 0;
  
        const ratio = (signalStrength - minStrength) / (maxStrength - minStrength);
        const clampedRatio = Math.max(0, Math.min(ratio, 1));
  
        const r = Math.round(startColor.r + clampedRatio * (endColor.r - startColor.r));
        const g = Math.round(startColor.g + clampedRatio * (endColor.g - startColor.g));
        const b = Math.round(startColor.b + clampedRatio * (endColor.b - startColor.b));
  
        return `rgb(${r},${g},${b})`;
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
  
  i {
    font-size: 18px;
  }
  </style>
  