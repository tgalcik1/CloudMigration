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
      isVisible: true
    };
  },
  mounted() {
    this.startTimer();
    // window.api.send('toMain', { command: 'update-task', task: 'baseline' });

    this.$store.commit('collapseSidebar');

    // Fade out navbar and footer
    this.$emit('toggle-navbar-footer', false);

    // Delay the background color change to allow the initial style to apply
    setTimeout(() => {
      this.$refs.videoWrapper.style.backgroundColor = 'rgba(0, 0, 0, 0)';
    }, 10);
  },
  methods: {
    startTimer() {
      this.interval = setInterval(() => {
        if (this.remainingTime > 0) {
          this.remainingTime--;
          if (this.remainingTime === 2) {
            this.fadeBack();
            // Fade in navbar and footer
            console.log('Emitting toggle-navbar-footer event with true');
            this.$emit('toggle-navbar-footer', true);
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
    }
  },
  beforeUnmount() {
    window.api.send('toMain', { command: 'stop-data-collection' });
    clearInterval(this.interval);
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
