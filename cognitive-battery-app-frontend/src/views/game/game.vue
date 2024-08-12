<template>
  <div class="game-wrapper">
    <div class="game-container">
      <!-- <iframe ref="gameIframe" class="game-iframe" frameborder="0" src="https://itch.io/embed-upload/8647397?color=333333" allowfullscreen=""><a href="https://tjgalcik.itch.io/fps-animations">Play FPS Animations on itch.io</a></iframe> -->
      <iframe ref="gameIframe" :src="gameUrl" frameborder="0" allowfullscreen class="game-iframe"></iframe>
    </div>
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
      switch (event.data.command) {
        case 'navigate':
          console.log('Update task:', event.data.task);
          window.api.send('toMain', { command: 'update-task', task: event.data.task});
          break;
        case 'enumeration':
          event.data.Userid = this.subjectId; //append subjectid
          // also need to append computer name

          delete event.data.command; // dont care about command (task) anymore since we are publishing to specific topics
          console.log('Enumeration results:', event.data);
          window.api.send('toMain', { command: 'send-iot-message', topic: 'sdk/test/js', message: event.data});
          break;
        case 'task-switching':
          event.data.Userid = this.subjectId;
          // also need to append computer name

          delete event.data.command;
          console.log('Task-switching results:', event.data);
          window.api.send('toMain', { command: 'send-iot-message', topic: 'sdk/test/js', message: event.data});
          break;
        case 'working-memory':
          event.data.Userid = this.subjectId;
          // also need to append computer name

          delete event.data.command;
          console.log('Working-memory results:', event.data);
          window.api.send('toMain', { command: 'send-iot-message', topic: 'sdk/test/js', message: event.data});
          break;
        default:
          break;
      }
    }
  }
};
</script>

<style scoped>

.game-iframe {
  margin-top: 60px;
  width: 100%;
  height: calc(100vh - 120px);
  border: none;
}
</style>
