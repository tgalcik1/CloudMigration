<template>
  <div v-if="isVisible" class="video-wrapper" ref="videoWrapper">
    <div class="baseline-container">
      <!-- <iframe class="video-frame"
        src="https://www.youtube.com/embed/h_lQ2tMgLVM?si=UwVMZhs95zvIJTvj&amp;start=7&amp;autoplay=1&amp;mute=1"
        allow="autoplay"
        frameborder="0"
        allowfullscreen
        >
      </iframe> -->
      <!-- <p>DEBUG: Time remaining: {{ formatTime(remainingTime) }}</p> -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'Video',
  data() {
    return {
      remainingTime: 10,
      isVisible: true,
      hueRotation: 0,
      isResetting: false
    };
  },
  mounted() {
    this.startTimer();
    this.$store.commit('collapseSidebar');

    // Fade out navbar and footer
    this.$emit('toggle-navbar-footer', false);

    // Delay the background color change to allow the initial style to apply
    setTimeout(() => {
      this.$refs.videoWrapper.style.backgroundColor = 'rgba(0, 0, 0, 0)';
    }, 10);

    this.startHueRotation();
  },
  methods: {
    startTimer() {
      this.interval = setInterval(() => {
        if (this.remainingTime > 0) {
          this.remainingTime--;
          if (this.remainingTime === 2) {
            this.fadeBack();
            // Fade in navbar and footer
            this.$emit('toggle-navbar-footer', true);
            this.startSmoothReset();
          }
        } else {
          clearInterval(this.interval);
          window.api.send('toMain', { command:'stop-baseline' });
          this.$router.push('/instructions');
        }
      }, 1000);
    },
    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
    },
    fadeBack() {
      this.$refs.videoWrapper.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    },
    startHueRotation() {
      this.hueInterval = setInterval(() => {
        if (!this.isResetting) {
          this.hueRotation = (this.hueRotation + 1) % 360;
          this.$refs.videoWrapper.style.backdropFilter = `hue-rotate(${this.hueRotation}deg)`;
        }
      }, 100);
    },
    startSmoothReset() {
      this.isResetting = true;
      const resetInterval = 20;
      const steps = 2000 / resetInterval;
      const decrement = this.hueRotation / steps;
      let currentStep = 0;
      this.resetInterval = setInterval(() => {
        if (currentStep < steps) {
          this.hueRotation -= decrement;
          this.$refs.videoWrapper.style.backdropFilter = `hue-rotate(${this.hueRotation}deg)`;
          currentStep++;
        } else {
          clearInterval(this.resetInterval);
          this.hueRotation = 0;
          this.$refs.videoWrapper.style.backdropFilter = `hue-rotate(0deg)`;
          this.isResetting = false;
        }
      }, resetInterval);
    }
  },
  beforeUnmount() {
    window.api.send('toMain', { command: 'stop-data-collection' });
    clearInterval(this.interval);
    clearInterval(this.hueInterval);
    clearInterval(this.resetInterval);
  }
};
</script>

<style scoped>
.video-wrapper {
  cursor: none;
  background-color: rgba(0, 0, 0, 0.5);
  height: 100%;
  transition: background-color 2s ease-in-out; /* Adjust the duration as needed */
}

.baseline-container {
  padding: 1em;
}

.video-frame {
  width: 100%;
  height: 80vh;
}
</style>
