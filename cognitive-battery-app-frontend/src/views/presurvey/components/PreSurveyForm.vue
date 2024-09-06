<template>
  <div class="survey-wrapper">
    <p style="display: flex; justify-content: center; align-items: center; text-align:justify; max-width: 30vw">{{ instructions }}</p>
    <div style="display: flex; flex-direction: column; justify-content: center; align-items: center;" v-if="currentQuestion">
      <div class="survey-card">
        <p>{{ currentQuestion.question_text }}</p>
        <div v-if="currentQuestion.question_type === 'multiple_choice'">
          <div v-for="(option, index) in currentQuestion.options" :key="index">
            <label>
              <input
                type="radio"
                :name="`question_${currentQuestion.question_id}`"
                :value="option"
                v-model="response"
              />
              {{ option }}
            </label>
          </div>
        </div>
        <div v-else-if="currentQuestion.question_type === 'textbox'">
          <input
            type="text"
            placeholder="Response"
            v-model="response"
          />
        </div>
      </div>
      <div class="navigation-buttons">
        <button style="width: 100px" @click="handleNext" :disabled="!response || loading">
          <i v-if="loading" class="fas fa-spinner fa-pulse"></i>
          <span v-else>{{ isLast ? 'Submit' : 'Next' }}</span>
        </button>
      </div>
    </div>
    <div v-else>
      <p>Loading question...</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { mapState } from "vuex";

export default {
  data() {
    return {
      currentQuestion: null,
      response: null,
      isLast: false,
      loading: false,
    };
  },
  props: {
    survey: String,
    instructions: String,
  },
  computed: {
    ...mapState({
      subjectId: (state) => state.subjectId,
    }),
  },
  methods: {
    // POST to start survey and get first question
    async postFirstResponse() {
      try {
        this.loading = true; // disable button while loading
        const surveyUrl = process.env.VUE_APP_SURVEY_API_URL + `/surveys/${this.survey}/responses`;
        const res = await axios.post(surveyUrl, {
          user_id: this.subjectId
        });
        this.currentQuestion = res.data.question;
        this.isLast = res.data.completed || false;
        this.response = null;
      } catch (error) {
        console.error('Failed to fetch the first question', error);
      } finally {
        this.loading = false; // re-enable button after loading
      }
    },

    // PUT to submit answer and fetch next question
    async putNextResponse() {
      try {
        this.loading = true; // disable button while loading
        const surveyUrl = process.env.VUE_APP_SURVEY_API_URL + `/surveys/${this.survey}/responses`;
        const res = await axios.put(surveyUrl, {
          user_id: this.subjectId,
          question_id: this.currentQuestion.question_id,
          answer: this.response
        });
        this.currentQuestion = res.data.question;
        this.isLast = res.data.completed || false;
        this.response = null;
      } catch (error) {
        console.error('Failed to submit response and fetch the next question', error);
      } finally {
        this.loading = false; // re-enable button after loading
      }
    },

    async handleNext() {
      if (this.response && !this.loading) {
        // POST for first question
        if (!this.currentQuestion.question_id) {
          await this.postFirstResponse();
        } else {
          // PUT for following questions
          await this.putNextResponse();
        }

        // check for last question
        if (this.isLast) {
          this.$message.success('Survey submitted successfully');
          this.$emit('surveySubmitted');
        }
      }
    },
  },
  async mounted() {
    await this.postFirstResponse();
  },
};
</script>
  
<style scoped>
  .survey-wrapper {
    margin: 20px;
  }

  .survey-card {
    width: 15vw;
    background-color: rgba(0,0,0,0.2);
    padding: 16px 32px 32px 32px;
    border-radius: 16px;
    margin: 16px;
  }

  .navigation-buttons {
    display: flex;
    justify-content: center;
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
  