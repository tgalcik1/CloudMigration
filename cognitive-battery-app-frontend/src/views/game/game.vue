<template>
  <div class="game-container">
    <iframe ref="gameIframe" :src="gameUrl" frameborder="0" class="game-iframe"></iframe>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'GameView',
  computed: {
    ...mapState({
      subjectId: state => state.subjectId,
      selectedEcgDevice: state => state.selectedEcgDevice
    }),
    gameUrl() {
      return `/cognitive-testbattery/index.html?userID=${this.subjectId}&selectedEcgDevice=${this.selectedEcgDevice}`;
    }
  },
  mounted() {
    this.$refs.gameIframe.addEventListener('load', () => {
      const message = {
        command: 'start-data-collection',
        subjectId: this.subjectId,
        device: this.selectedEcgDevice,
        task: 'baseline'
      };
      this.$refs.gameIframe.contentWindow.postMessage(message, '*');
    });
    
    window.addEventListener('message', this.handleIframeMessage);
  },
  beforeUnmount() {
    window.removeEventListener('message', this.handleIframeMessage);
  },
  methods: {
    handleIframeMessage(event) {
      if (event.data.command === 'navigate') {
        console.log('Update task:', event.data.task);
        window.api.send('toMain', { command: 'update-task', task: event.data.task});
      }
    }
  }
};
</script>

<style scoped>
.game-iframe {
  width: 100%;
  height: 88vh;
  border: none;
}
</style>
