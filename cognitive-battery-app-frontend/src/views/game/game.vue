<template>
  <div class="game-wrapper">
    <transition name="fade">
      <div v-if="isSurveyVisible" class="survey-container">
        <div class="survey-content">
          <h1 style="text-align: center">Post-Survey</h1>
          <div v-if="currentQuestion">
            <p>{{ currentQuestion.question_text }}</p>
            <div v-if="currentQuestion.question_type === 'multiple_choice'" class="radio-group">
              <div v-for="option in currentQuestion.options" :key="option" class="radio-container">
                <label>
                  <input
                    type="radio"
                    :value="option"
                    v-model="responses[currentQuestion.question_id]"
                  />
                  <div class="radio-label">{{ option }}</div>
                </label>
              </div>
            </div>
          </div>
          <div class="navigation-buttons">
            <button type="button" @click="prevQuestion" :disabled="isFirstQuestion">
              Previous
            </button>
            <button
              v-if="!isLastQuestion"
              type="button"
              @click="nextQuestion"
              :disabled="!canProceedToNext"
            >
              Next
            </button>
            <button
              v-if="isLastQuestion"
              type="submit"
              :disabled="!canProceedToNext || !allQuestionsAnswered"
              @click="submitSurvey"
            >
              Submit
            </button>
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
import axios from "axios";

export default {
  name: "GameView",
  data() {
    return {
      isSurveyVisible: false,
      lastTaskDifficulty: null,
      surveyQuestions: [],
      currentQuestionIndex: 0,
      responses: {}
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
      return this.surveyQuestions[this.currentQuestionIndex] || null;
    },
    isFirstQuestion() {
      return this.currentQuestionIndex === 0;
    },
    isLastQuestion() {
      return this.currentQuestionIndex === this.surveyQuestions.length - 1;
    },
    canProceedToNext() {
      return this.currentQuestion && !!this.responses[this.currentQuestion.question_id];
    },
    allQuestionsAnswered() {
      return this.surveyQuestions.every(question => this.responses[question.question_id]);
    }
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
          
          this.lastTaskDifficulty = event.data.difficulty;
          console.log("Last task difficulty:", this.lastTaskDifficulty);
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
          
          this.lastTaskDifficulty = event.data.difficulty;
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

          this.lastTaskDifficulty = event.data.difficulty;
          break;

        case "break-survey":
          this.fetchSurveyQuestions(event.data.task);
          this.isSurveyVisible = true;
          break;

        case "end-survey":
          this.fetchSurveyQuestions(event.data.task);
          this.isSurveyVisible = true;
          break;

        default:
          break;
      }
    },
    async fetchSurveyQuestions(task) {
      try {
        const res = await axios.get(process.env.VUE_APP_SURVEY_API_URL + '/surveys/' + task + '/questions');
        console.log(res.data);
        this.surveyQuestions = res.data
          .filter(question => question.active === true)
          .sort((a, b) => a.order - b.order);
      } catch (error) {
        console.error(error);
        this.$message.error('Failed to fetch survey questions');
      }
    },
    async submitSurvey() {
      console.log('Submitting survey');
      try {
        const answers = Object.keys(this.responses).map(questionId => ({
          question_id: questionId,
          answer: this.responses[questionId]
        }));

        const requestPayload = {
          user_id: this.subjectId,
          answers,
          difficulty_level: this.lastTaskDifficulty
        };

        console.log(requestPayload)

        const res = await axios.post(`${process.env.VUE_APP_SURVEY_API_URL}/surveys/${this.survey}/responses`, requestPayload);
        this.$message.success('Survey submitted successfully');
        console.log(res);
        this.resetSurvey();
        this.$emit('surveySubmitted');
      } catch (error) {
        console.error(error);
        this.$message.error('Failed to submit survey');
      }
    },
    resetSurvey() {
      this.surveyQuestions = [];
      this.currentQuestionIndex = 0;
      this.responses = {};
      this.isSurveyVisible = false;
    },
    prevQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--;
      }
    },
    nextQuestion() {
      if (this.currentQuestionIndex < this.surveyQuestions.length - 1) {
        this.currentQuestionIndex++;
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
  width: 65%;
  max-width: 900px;
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

.radio-group {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.radio-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.radio-label {
  margin-top: 4px;
  margin-bottom: 16px;
  text-align: center;
}

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  margin-left: 12px;
  margin-right: 12px;
}

button {
  margin: 5px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  cursor: pointer;
  text-align: center;
  font-family: "Monda", sans-serif;
  transition: background-color 0.1s ease;
}

button:hover:not(:disabled) {
  background-color: rgb(200, 200, 200);
}

button:disabled{
  cursor: not-allowed;
}

</style>
