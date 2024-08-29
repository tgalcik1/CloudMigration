<template>
  <div class="game-wrapper">
    <transition name="fade">
      <div v-if="isSurveyVisible" class="survey-container">
        <div class="survey-content">
          <h1 style="text-align: center">Post-Survey</h1>
            <div class="navigation-buttons">
              <button type="button" @click="prevQuestion" :disabled="isFirstQuestion">Previous</button>
              <button type="button" @click="nextQuestion" :disabled="!canProceedToNext">Next</button>
              <button type="submit" :disabled="!canProceedToNext">Submit</button>
            </div>
        </div>
      </div>
    </transition>

    <div class="game-container">
      <iframe
        ref="gameIframe"
        :src="gameUrl"
        frameborder="0"
        allowfullscreen
        class="game-iframe"
        :style="{ pointerEvents: isSurveyVisible ? 'none' : 'auto' }"
      ></iframe>
    </div>
  </div>
</template>

<script>
import { mapState } from "vuex";

export default {
  name: "GameView",
  data() {
    return {
      isSurveyVisible: true,
      surveyAnswers: Array(5).fill(null),
      surveyQuestions: [],
      currentQuestionIndex: 0,
    };
  },
  computed: {
    ...mapState({
      subjectId: (state) => state.subjectId,
      selectedEcgDevice: (state) => state.selectedEcgDevice,
    }),
    gameUrl() {
      return `/cognitive-testbattery/index.html?userID=${this.subjectId}&selectedEcgDevice=${this.selectedEcgDevice}`;
    },
  },
  mounted() {
    this.$refs.gameIframe.addEventListener("load", () => {
      const message = {
        command: "start-data-collection",
        subjectId: this.subjectId,
        device: this.selectedEcgDevice,
        task: "baseline",
      };
      this.$refs.gameIframe.contentWindow.postMessage(message, "*");
    });

    window.addEventListener("message", this.handleIframeMessage);
  },
  beforeUnmount() {
    window.removeEventListener("message", this.handleIframeMessage);
  },
  methods: {
    handleIframeMessage(event) {
      switch (event.data.command) {
        case "navigate":
          console.log("Update task:", event.data.task);
          window.api.send("toMain", {
            command: "update-task",
            task: event.data.task,
          });
          break;
        case "enumeration":
          event.data.user_id = this.subjectId; // append subjectid
          event.data.computer_name = '';

          delete event.data.command; // don't care about command (task) anymore since we are publishing to specific topics
          console.log("Enumeration results:", event.data);
          window.api.send("toMain", {
            command: "send-iot-message",
            topic: "game/enumeration",
            message: event.data,
          });
          break;
        case "task-switching":
          event.data.user_id = this.subjectId;
          event.data.computer_name = '';

          delete event.data.command;
          console.log("Task-switching results:", event.data);
          window.api.send("toMain", {
            command: "send-iot-message",
            topic: "game/taskswitch",
            message: event.data,
          });
          break;
        case "working-memory":
          event.data.user_id = this.subjectId;
          event.data.computer_name = '';

          delete event.data.command;
          console.log("Working-memory results:", event.data);
          window.api.send("toMain", {
            command: "send-iot-message",
            topic: "game/workingmemory",
            message: event.data,
          });
          break;

        case "break-survey":
          console.log("Break survey will appear now");
          //TODO determine which survey to display
          //TODO fetch the difficulty from the game
          this.isSurveyVisible = true;
          break;

        case "end-survey":
          console.log("End survey will appear now");
          //TODO determine which survey to display
          this.isSurveyVisible = true;
          break;

        default:
          break;
      }
    },
  },
};
</script>

<style scoped>
.game-iframe {
  margin-top: 60px;
  width: 100%;
  height: calc(100vh - 120px);
  border: none;
}

.survey-container {
  position: fixed;
  display: flex;
  justify-content: center;
  align-items: center;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(20px);
  padding: 20px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  color: black;
}

.survey-content {
  width: 60%;
  max-width: 800px;
  background: white;
  padding: 16px;
  border-radius: 16px;
  transform: translateY(-20%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
