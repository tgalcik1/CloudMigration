<template>
  <div class="presurvey-wrapper">
    <h1 style="text-align: center; cursor: pointer;">
      Pre-Survey
    </h1>

    <p v-if="!this.currentSurvey">Please complete the following surveys prior to beginning the experiment.</p>

    <div class="survey-list" v-if="!this.currentSurvey">
      <div class="survey-card" v-for="survey in this.surveys" :key="survey.survey_id">
        {{ survey.survey_id }}
        <button style="margin-left: 16px" @click="this.currentSurvey = survey.survey_id" v-if="!completedSurveys.includes(survey)">Start</button>
        <i style="margin-left: 16px" v-else class="fa-regular fa-circle-check"></i>
      </div>
    </div>

    <div v-else>
      <PreSurveyForm :survey="currentSurvey" @returnToSurveyList="handleReturnToSurveyList" @surveySubmitted="handleSurveySubmitted" />
    </div>

    <div v-if="!this.currentSurvey" class="survey-buttons">
      <button @click="$router.push('/setup')" v-if="surveys.every(survey => completedSurveys.includes(survey))">Continue to Setup</button>
      <button v-else disabled>Continue to Setup</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import PreSurveyForm from './components/PreSurveyForm.vue';

export default {
  components: {
    PreSurveyForm
  },
  data() {
    return {
      surveys: [],
      completedSurveys: [],
      currentSurvey: null
    }
  },
  methods: {
    async fetchAllSurveys() {
      try {
        const res = await axios.get(process.env.VUE_APP_SURVEY_API_URL + '/surveys');
        this.surveys = res.data.filter(survey => survey.active === true);
      } catch (error) {
        console.error(error);
        this.$message.error('Failed to fetch surveys');
      }
    },
    handleReturnToSurveyList() {
      this.currentSurvey = null;
    },
    handleSurveySubmitted() {
      this.completedSurveys.push(this.surveys.find(survey => survey.survey_id === this.currentSurvey));
      this.currentSurvey = null;
    }
  },
  async mounted() {
    await this.fetchAllSurveys();
  }
};
</script>

<style scoped>
.presurvey-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.survey-buttons button {
  margin: 5px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  cursor: pointer;
  text-align: center;
  font-family: "Monda", sans-serif;
  transition: background-color 0.3s ease;
}

.survey-buttons button:disabled {
  cursor: not-allowed;
}

button {
  font-family: "Monda", sans-serif;
}

.survey-list {
  max-width: 30vw;
  background-color: rgba(0,0,0,0.2);
  padding: 16px;
  border-radius: 16px;
  margin: 16px;
}

.survey-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8px 0;
}
</style>
