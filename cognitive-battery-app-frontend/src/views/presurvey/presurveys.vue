<template>
  <div class="presurvey-wrapper">
    <h1 style="text-align: center; cursor: pointer;">
      Surveys
    </h1>

    <p v-if="!this.currentSurvey">Please complete the following surveys.</p>

    <div class="survey-list" v-if="!this.currentSurvey">
      <div 
        class="survey-card" 
        v-for="survey in surveys" 
        :key="survey.survey_id"
        :class="{
          'survey-card--gray': !selectedSurveys.includes(survey.survey_id) && !completedSurveys.includes(survey),
          'survey-card--green': completedSurveys.includes(survey),
          'survey-card--white': selectedSurveys.includes(survey.survey_id) && !completedSurveys.includes(survey)
        }"
      >
        <div>
          <input 
            type="checkbox" 
            :id="`checkbox-${survey.survey_id}`" 
            :value="survey.survey_id" 
            v-model="selectedSurveys" 
            :disabled="completedSurveys.includes(survey)">
          <label :for="`checkbox-${survey.survey_id}`">{{ survey.title }}</label>
        </div>
        
        <button class="start-survey-button"
          style="margin-left: 16px; border-radius: 8px; border: none" 
          @click="startSurvey(survey)" 
          v-if="!completedSurveys.includes(survey) && selectedSurveys.includes(survey.survey_id)"
        >
          Start
        </button>
        
        <i 
          style="margin-left: 16px" 
          v-else-if="completedSurveys.includes(survey)" 
          class="fa-regular fa-circle-check"
          :class="{'icon--green': completedSurveys.includes(survey)}"
        ></i>
      </div>
    </div>

    <div v-else>
      <PreSurveyForm :survey="currentSurvey" :instructions="currentInstructions" @returnToSurveyList="handleReturnToSurveyList" @surveySubmitted="handleSurveySubmitted" />
    </div>

    <div v-if="!this.currentSurvey" class="survey-buttons">
      <button @click="performLogout" :disabled="!canContinue">Finish Study</button>
    </div>
  </div>
</template>


<script>
import axios from 'axios';
import { mapActions } from 'vuex';
import PreSurveyForm from './components/PreSurveyForm.vue';

export default {
  components: {
    PreSurveyForm
  },
  data() {
    return {
      surveys: [],
      completedSurveys: [],
      selectedSurveys: [],
      currentSurvey: null,
      currentInstructions: ''
    }
  },
  computed: {
    canContinue() {
      return this.selectedSurveys.every(surveyId => 
        this.completedSurveys.some(completedSurvey => completedSurvey.survey_id === surveyId)
      );
    }
  },
  methods: {
    ...mapActions(['logout']),
    performLogout() {
      this.logout();
    },
    async fetchAllSurveys() {
      try {
        const res = await axios.get(process.env.VUE_APP_SURVEY_API_URL + '/surveys');
        console.log(res.data);
        this.surveys = res.data.filter(survey => survey.active === true && survey.order === 'Pre-Assessment');
      } catch (error) {
        console.error(error);
        this.$message.error('Failed to fetch surveys');
      }
    },
    startSurvey(survey) {
      this.currentSurvey = survey.survey_id;
      this.currentInstructions = survey.instructions;
    },
    handleReturnToSurveyList() {
      this.currentSurvey = null;
      this.currentInstructions = '';
    },
    handleSurveySubmitted() {
      const completedSurvey = this.surveys.find(survey => survey.survey_id === this.currentSurvey);
      if (!this.completedSurveys.includes(completedSurvey)) {
        this.completedSurveys.push(completedSurvey);
      }
      this.currentSurvey = null;
      this.currentInstructions = '';
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
  background-color: #ddd;
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
  transition: all 0.3s ease;
}

.survey-card--gray {
  color: gray;
}

.survey-card--green {
  color: #42b983;
}

.survey-card--white {
  color: white;
}

.icon--green {
  color: #42b983;
}

.start-survey-button{
  transition: background-color 0.1s ease;
}

.start-survey-button:hover{
  cursor: pointer;
  background-color: rgb(200,200,200);
}
</style>
