<template>
  <div class="game-wrapper">
    <transition name="fade">
      <div v-if="isSurveyVisible" class="survey-container">
        <div class="survey-content">
          <h1 style="text-align: center">Post-Survey</h1>
          <p class="description">
            Rate your experience in the preceding task. Use the mouse to click the
            circle indicating your response. Please take your time and share your
            honest opinion.
          </p>
          <form @submit.prevent="submitSurvey">
            <div class="question">
              <label :for="'question' + currentQuestionIndex">
                {{ currentQuestion.text }}
              </label>
              <div class="rating">
                <div class="circles">
                  <span
                    v-for="i in 21"
                    :key="i"
                    :class="['circle', { selected: surveyAnswers[currentQuestionIndex] === i - 1 }]"
                    @click="selectAnswer(currentQuestionIndex, i - 1)"
                  >
                    {{ i - 1 }}
                  </span>
                </div>
                <div class="rating-labels">
                  <span class="label">{{ currentQuestion.labels[0] }}</span>
                  <span class="label">{{ currentQuestion.labels[1] }}</span>
                  <span class="label">{{ currentQuestion.labels[2] }}</span>
                </div>
              </div>
            </div>
            <div class="navigation-buttons">
              <button type="button" @click="prevQuestion" :disabled="isFirstQuestion">Previous</button>
              <button v-if="!isLastQuestion" type="button" @click="nextQuestion" :disabled="!canProceedToNext">Next</button>
              <button v-if="isLastQuestion" type="submit" :disabled="!canProceedToNext">Submit</button>
            </div>
          </form>
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
      isSurveyVisible: false,
      surveyAnswers: Array(5).fill(null),
      surveyQuestions: [
        {
          text: "How challenging was it? How hard did you have to work?",
          labels: ["Not Challenging", "Average", "Very Challenging"],
        },
        {
          text: "How successful were you in accomplishing the task goals?",
          labels: ["Not Successful", "Average", "Very Successful"],
        },
        {
          text: "How stressful, discouraging, and irritating was the task?",
          labels: ["Not Stressful", "Average", "Very Stressful"],
        },
        {
          text: "How mentally demanding was the task?",
          labels: ["Not Demanding", "Average", "Very Demanding"],
        },
        {
          text: "How hurried or rushed was the pace of the task?",
          labels: ["Not Hurried", "Average", "Very Hurried"],
        },
      ],
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
    currentQuestion() {
      return this.surveyQuestions[this.currentQuestionIndex];
    },
    isFirstQuestion() {
      return this.currentQuestionIndex === 0;
    },
    isLastQuestion() {
      return this.currentQuestionIndex === this.surveyQuestions.length - 1;
    },
    canProceedToNext() {
      return this.surveyAnswers[this.currentQuestionIndex] !== null;
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
          this.isSurveyVisible = true;
          break;

        case "end-survey":
          console.log("End survey will appear now");
          this.isSurveyVisible = true;
          break;

        default:
          break;
      }
    },
    selectAnswer(questionIndex, value) {
      this.surveyAnswers[questionIndex] = value;
    },
    nextQuestion() {
      if (!this.isLastQuestion && this.canProceedToNext) {
        this.currentQuestionIndex += 1;
      }
    },
    prevQuestion() {
      if (!this.isFirstQuestion) {
        this.currentQuestionIndex -= 1;
      }
    },
    submitSurvey() {
      console.log("Survey submitted with answers:", this.surveyAnswers);
      this.$message.success("Survey submitted successfully");
      this.isSurveyVisible = false;
      this.surveyAnswers = Array(5).fill(null);
      this.currentQuestionIndex = 0;
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

.description {
  margin-bottom: 20px;
  color: gray;
}

.question {
  margin-bottom: 30px;
}

.rating {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 10px;
}

.circles {
  display: flex;
  justify-content: space-between;
  width: 90%;
  overflow-x: auto;
  margin-bottom: 10px;
}

.circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #ddd;
  cursor: pointer;
  margin: 0 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #333;
  transition: background 0.3s;
}

.circle.selected {
  background: #007bff;
  color: #fff;
}

.rating-labels {
  display: flex;
  justify-content: space-between;
  width: 90%;
  text-align: center;
  font-size: 12px;
}

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px;
}
</style>
