<template>
    <div class="baseline-container">
      <iframe class="video-frame"
        src="https://www.youtube.com/embed/h_lQ2tMgLVM?si=UwVMZhs95zvIJTvj&amp;start=7&amp;autoplay=1&amp;mute=1"
        allow="autoplay"
        frameborder="0"
        allowfullscreen
        >
      </iframe>
      <!-- <p>DEBUG: Time remaining: {{ formatTime(remainingTime) }}</p> -->
    </div>
  </template>
  
  <script>
  export default {
    name: 'Video',
    data() {
      return {
        remainingTime: 5 * 60
      };
    },
    mounted() {
      this.startTimer();
      window.api.send('toMain', { command: 'update-task', task: 'baseline'});
    },
    methods: {
      startTimer() {
        this.interval = setInterval(() => {
          if (this.remainingTime > 0) {
            this.remainingTime--;
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
      }
    },
    beforeUnmount() {
      window.api.send('toMain', { command: 'stop-data-collection' });
      clearInterval(this.interval);
    }
  };
  </script>
  
  <style scoped>
  .baseline-container {
    padding: 1em;
  }
  
  .video-frame {
    width: 100%;
    height: 80vh;
  }
  </style>
  