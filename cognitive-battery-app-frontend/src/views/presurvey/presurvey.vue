<template>
  <div class="presurvey-wrapper">
    <div class="presurvey-container">
      <h1 @click="selectingSurveys = true" style="text-align: center; cursor: pointer;">
        Pre-Survey<span v-if="!selectingSurveys">: {{ currentSurvey.title }}</span>
      </h1>
      <div class="content">
        <div class="sidebar" v-if="selectingSurveys">
          <aside style="color: rgba(180, 180, 180, 1)">Select the surveys you would like to complete.</aside>
          <ul class="survey-list">
            <li v-for="(survey, index) in surveys" :key="index">
              <input type="checkbox" v-model="survey.selected" />
              {{ survey.title }}
            </li>
          </ul>
          <div class="navigation-buttons">
            <button @click="startSurveys" :disabled="!anySurveySelected">Start Surveys</button>
          </div>
        </div>
        <div class="survey-container" v-else>
          <div v-if="currentSurvey">
            <div v-if="currentQuestion">
              <p v-if="!isBubbleQuestion">{{ currentQuestion.text }}</p>
              <div v-if="currentQuestion.text === 'Age (years):'">
                <input type="text" v-model="responses[currentSurveyIndex][currentQuestionIndex].answer" placeholder="Enter your age" />
              </div>
              <div v-else-if="isBubbleQuestion">
                <div class="bubble-container">
                  <p style="color: rgba(180, 180, 180, 1)">Select the bubble indicating your response. Please take your time and share your honest opinion.</p>
                  <p>{{ currentQuestion.text }}</p>
                  <div class="bubbles">
                    <div 
                      v-for="n in bubbleRange" 
                      :key="n" 
                      :class="{ bubbleWrapper: true, selected: responses[currentSurveyIndex][currentQuestionIndex].answer == n }" 
                      @click="responses[currentSurveyIndex][currentQuestionIndex].answer = n"
                    >
                      <div class="bubble">{{ n }}</div>
                      <div class="bubble-label">{{ getBubbleLabel(n) }}</div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else>
                <div v-for="(option, oIndex) in currentQuestion.options" :key="oIndex">
                  <label>
                    <input
                      type="radio"
                      :name="'question' + currentQuestionIndex"
                      :value="option"
                      v-model="responses[currentSurveyIndex][currentQuestionIndex].answer"
                      @change="handleOptionChange(currentSurveyIndex, currentQuestionIndex, option)"
                    />
                    {{ option }}
                  </label>
                  <div v-if="showInputField(currentSurveyIndex, currentQuestionIndex, option)">
                    <input
                      v-if="option === 'Other'"
                      type="text"
                      v-model="responses[currentSurveyIndex][currentQuestionIndex].other"
                      placeholder="Please specify"
                    />
                  </div>
                </div>
              </div>
              <div v-if="showAdditionalQuestion(currentSurveyIndex, currentQuestionIndex, 'smoke')">
                <p>On average, how many times per day do you smoke cigarettes or use another form of tobacco/nicotine?</p>
                <input type="text" v-model="responses[currentSurveyIndex][currentQuestionIndex].frequency" placeholder="Enter frequency" />
              </div>
              <div v-if="showAdditionalQuestion(currentSurveyIndex, currentQuestionIndex, 'caffeine')">
                <p>On average, how many caffeinated beverages do you consume per day (number of cups)?</p>
                <input type="text" v-model="responses[currentSurveyIndex][currentQuestionIndex].cups" placeholder="Enter number of cups" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="navigation-buttons" v-if="!selectingSurveys">
        <button @click="previousQuestion">Previous</button>
        <button @click="nextStepOrQuestion">{{ nextButtonLabel }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  data() {
    return {
      selectingSurveys: true,
      currentSurveyIndex: 0,
      currentQuestionIndex: 0,
      responses: [],
      surveys: [
        {
          title: 'Demographic Inventory',
          questions: [
            { text: 'Age (years):', options: [] },
            { text: 'Gender:', options: ['Male', 'Female', 'Non-binary', 'Prefer not to say'] },
            { text: 'Race:', options: ['Asian', 'Black', 'Hispanic/Latino', 'Native American', 'White/Caucasian', 'Other', 'Prefer not to say'] },
            { text: 'Education level completed:', options: ['Less than high school', 'High school diploma/GED', 'Some college/Associate\'s degree', 'Bachelor\'s degree', 'Master\'s degree', 'Doctorate degree', 'Prefer not to say'] },
            { text: 'On average, how frequently do you smoke cigarettes or use another form of tobacco/nicotine? (Choose only one option)', options: ['Never', 'Rarely', 'A few times per month', 'A few times per week', 'Every day'] },
            { text: 'On average, how frequently do you consume caffeinated beverages? (Choose only one)', options: ['Never', 'Rarely', 'A few times per month', 'A few times per week', 'Every day'] },
          ],
          selected: false
        },
        {
          title: 'Interpersonal Trust Scale Questionnaire',
          questions: [
            { text: '1.   Hypocrisy is on the increase in our society.', options: [] },
            { text: '2.   In dealing with strangers one is better off to be cautious until they have provided evidence that they are trustworthy.', options: [] },
            { text: '3.   This country has a dark future unless we can attract better people into politics.', options: [] },
            { text: '4.   Fear and social disgrace or punishment rather than conscience prevents most people from breaking the law.', options: [] },
            { text: '5. 	Using the honor system of not having a teacher present during exams would probably result in increased cheating.', options: [] },
            { text: '6. 	Parents usually can be relied on to keep their promises.', options: [] },
            { text: '7. 	The United Nations will never be an effective force in keeping world peace.', options: [] },
            { text: '8. 	The judiciary is a place where we can all get unbiased treatment.', options: [] },
            { text: '9. 	Most people will be horrified if they knew how much news that the public hears and sees is distorted.', options: [] },
            { text: '10. It is safe to believe that in spite of what people say most people are primarily interested in their  own welfare.', options: [] },
            { text: '11. Even though we have reports in newspapers, radio, and TV, it is hard to get objective accounts of public events.', options: [] },
            { text: '12.  The future seems very promising.', options: [] },
            { text: '13. If we really knew what was going on in international politics, the public would have no reason to be more frightened than they now seem to be.', options: [] },
            { text: '14. Most elected officials are really sincere in their campaign promises.', options: [] },
            { text: '15. Many major national sports contests are fixed in one way or another.', options: [] },
            { text: '16. Most experts can be relied upon to tell the truth about the limits of their knowledge.', options: [] },
            { text: '17. Most parents can be relied upon to carry out their threats of punishments.', options: [] },
            { text: '18. Most people can be counted on to do what they say they will do.', options: [] },
            { text: '19. In these competitive times one has to be alert or someone is likely to take advantage of you.', options: [] },
            { text: '20. Most idealists are sincere and usually practice what they preach.', options: [] },
            { text: '21. Most salesmen are honest in describing their products.', options: [] },
            { text: '22. Most students in school would not cheat if they were sure of getting away with it.', options: [] },
            { text: '23. Most repairmen will not overcharge even if they think you are ignorant of their specialty.', options: [] },
            { text: '24. A large share of accident claims filed against insurance companies are phony.', options: [] },
            { text: '25. Most people answer public opinion polls honestly.', options: [] }
          ],
          selected: false
        },
        {
          title: 'Shooting Game Experience Questionnaire',
          questions: [
            { text: '1. How long have you played games?', options: ['Never played', '6 months', '1 year', '2-5 years', '5-10 years', '10 or more years'] },
            { text: '2. On average, how often do you currently play video games?', options: ['Never', 'Less than once a month', '1-3 times a month', 'Once or twice a week', 'Almost every day'] },
            { text: '3. During the average week, how many hours do you currently spend playing video games?', options: ['Less than 2 hours', '2-5 hours', '8-10 hours', '10-15 hours', 'More than 20 hours'] },
            { text: '4. On a typical day, when you play video games how many hours do you usually spend playing?', options: ['Less than 2 hours', '2-5 hours', '8-10 hours', '10-15 hours', 'More than 20 hours'] },
            { text: '5. How skilled do you feel you are at playing video games?', options: ['No skill', 'Not very skilled', 'Moderately skilled', 'Very skilled'] },
            { text: '6. Please rate your experience playing video games on a scale of 1 (very inexperienced) to 7 (very experienced).', options: [] },
            { text: '7. Please rate each of the following game genres based on your preference, on a scale from 1 (Least Preferred) to 5 (Most Preferred).', options: [] },
          ],
          selected: false
        },
        {
          title: 'The State-Trait Anxiety Inventory',
          questions: [
            { text: 'I feel fine.', options: [] },
            { text: 'I tire quickly.', options: [] },
            { text: 'I feel like crying.', options: [] },
            { text: 'I wish I could be as happy as others seem to be.', options: [] },
            { text: 'I am losing opportunities because I cannot make decisions fast.', options: [] },
            { text: 'I feel rested.', options: [] },
            { text: 'I am calm.', options: [] },
            { text: 'I feel that difficulties are piling up in such a way that I cannot overcome them.', options: [] },
            { text: 'I worry too much about things that do not really matter.', options: [] },
            { text: 'I am happy.', options: [] },
            { text: 'I am inclined to take things hard.', options: [] },
            { text: 'I lack self-confidence.', options: [] },
            { text: 'I feel secure.', options: [] },
            { text: 'I try to avoid facing a crisis or difficulty.', options: [] },
            { text: 'I feel blue.', options: [] },
            { text: 'I feel content.', options: [] },
            { text: 'Some unimportant thoughts run through my mind and bother me.', options: [] },
            { text: 'I take disappointments so keenly that I cannot get them out of my head.', options: [] },
            { text: 'I am a steady person.', options: [] },
            { text: 'I become tense and upset when I think about my current concerns.', options: [] },
          ],
          selected: false,
          nextRoute: '/setup'
        }
      ]
    };
  },
  computed: {
    ...mapState({
      subjectId: state => state.subjectId
    }),
    selectedSurveys() {
      return this.surveys.filter(survey => survey.selected);
    },
    currentSurvey() {
      return this.selectedSurveys[this.currentSurveyIndex];
    },
    currentQuestion() {
      return this.currentSurvey.questions[this.currentQuestionIndex];
    },
    anySurveySelected() {
      return this.surveys.some(survey => survey.selected);
    },
    isLastQuestion() {
      return this.currentQuestionIndex === this.currentSurvey.questions.length - 1;
    },
    isLastSurvey() {
      return this.currentSurveyIndex === this.selectedSurveys.length - 1;
    },
    isBubbleQuestion() {
      return this.currentSurvey.title === 'Interpersonal Trust Scale Questionnaire' || this.currentSurvey.title === 'The State-Trait Anxiety Inventory' || this.currentSurvey.title === 'Shooting Game Experience Questionnaire';
    },
    bubbleRange() {
      if (this.currentSurvey.title === 'Interpersonal Trust Scale Questionnaire') return 7;
      if (this.currentSurvey.title === 'Shooting Game Experience Questionnaire') return 5;
      if (this.currentSurvey.title === 'The State-Trait Anxiety Inventory') return 4;
      return 7;
    },
    nextButtonLabel() {
      if (this.isLastSurvey && this.isLastQuestion) {
        return 'Continue';
      }
      return this.isLastQuestion ? 'Next Survey' : 'Next';
    }
  },
  methods: {
    openSurvey(index) {
      this.currentSurveyIndex = index;
      this.currentQuestionIndex = 0;
    },
    nextQuestion() {
      if (this.currentQuestionIndex < this.currentSurvey.questions.length - 1) {
        this.currentQuestionIndex += 1;
      }
    },
    previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex -= 1;
      } else if (this.currentQuestionIndex === 0 && this.currentSurveyIndex === 0) {
        this.selectingSurveys = true;
      }
    },
    nextStepOrQuestion() {
      if (this.isLastQuestion) {
        this.nextSurvey();
      } else {
        this.nextQuestion();
      }
    },
    nextSurvey() {
      if (this.currentSurveyIndex < this.selectedSurveys.length - 1) {
        this.currentSurveyIndex += 1;
        this.currentQuestionIndex = 0;
      } else {
        this.submitSurveys();
      }
    },
    startSurveys() {
      if (this.anySurveySelected) {
        this.responses = this.selectedSurveys.map(survey => survey.questions.map(question => ({ question: question.text, answer: '' })));
        this.selectingSurveys = false;
        this.openSurvey(0);
      }
    },
    submitSurveys() {
      window.api.send('survey', JSON.stringify({ responses: this.responses }));
      this.$router.push(this.selectedSurveys[this.currentSurveyIndex].nextRoute || '/setup');
    },
    handleOptionChange(surveyIndex, questionIndex, option) {
      if (option !== 'Other') {
        this.responses[surveyIndex][questionIndex].other = '';
      }
      if (option !== 'Every day') {
        if (this.responses[surveyIndex][questionIndex].hasOwnProperty.call('frequency')) {
          delete this.responses[surveyIndex][questionIndex].frequency;
        }
        if (this.responses[surveyIndex][questionIndex].hasOwnProperty.call('cups')) {
          delete this.responses[surveyIndex][questionIndex].cups;
        }
      }
    },
    showInputField(surveyIndex, questionIndex, option) {
      return option === 'Other' && this.responses[surveyIndex][questionIndex].answer === option;
    },
    showAdditionalQuestion(surveyIndex, questionIndex, type) {
      const question = this.selectedSurveys[surveyIndex].questions[questionIndex];
      if (type === 'smoke') {
        return question.text.includes('how frequently do you smoke') && this.responses[surveyIndex][questionIndex].answer === 'Every day';
      }
      if (type === 'caffeine') {
        return question.text.includes('how frequently do you consume caffeinated beverages') && this.responses[surveyIndex][questionIndex].answer === 'Every day';
      }
      return false;
    },
    getBubbleLabel(n) {
      const interpersonalTrustLabels = {
        1: 'Strongly Disagree',
        2: 'Disagree',
        3: 'Somewhat Disagree',
        4: 'Neutral',
        5: 'Somewhat Agree',
        6: 'Agree',
        7: 'Strongly Agree',
      };
      const shootingGameLabels = {
        1: 'Strongly do not prefer',
        2: 'Do not prefer',
        3: 'Indifferent',
        4: 'Prefer',
        5: 'Strongly Prefer',
      };
      const stateTraitAnxietyLabels = {
        1: 'Almost Never',
        2: 'Sometimes',
        3: 'Often',
        4: 'Almost Always',
      };

      if (this.currentSurvey.title === 'Interpersonal Trust Scale Questionnaire') {
        return interpersonalTrustLabels[n] || '';
      }
      if (this.currentSurvey.title === 'Shooting Game Experience Questionnaire') {
        return shootingGameLabels[n] || '';
      }
      if (this.currentSurvey.title === 'The State-Trait Anxiety Inventory') {
        return stateTraitAnxietyLabels[n] || '';
      }
      return '';
    },
  },
  mounted() {
    this.openSurvey(0);
  }
};
</script>

<style scoped>
.presurvey-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.presurvey-container {
  margin-bottom: 10%;
}

.presurvey-container {
  padding: 1em;
}

.content {
  display: flex;
  height: 100%;
}

.sidebar {
  text-align: center;
  width: 30vw;
  color: rgba(215,215,215,1);
  padding: 16px;
  border-radius: 8px;
  order: 1;
}

.survey-container {
  width: 5vw;
  flex-grow: 1;
  order: 2;
  background-color: rgba(0,0,0,0.2);
  backdrop-filter: blur(50px);
  color: rgba(215,215,215,1);
  padding: 0px 32px 32px 32px;
  border-radius: 8px;
}

  button:hover:not(.connect-button) {
    background-color: #a3a3a3;
  }

  button:disabled{
    background-color: rgba(255,255,255,0.3);
  }

  button:disabled:hover{
    cursor: not-allowed;
    background-color: rgba(255,255,255,0.3);
  }

.survey-list {
  list-style-type: none;
  padding: 0;
  text-align: left;
  margin-left: 70px;
}

.survey-list li {
  margin: 0.5em 0;
  display: flex;
  align-items: center;
}

.survey-list a {
  text-decoration: none;
  color: #42b983;
  margin-left: 0.5em;
  margin-right: 0.5em;
}

.survey-list li.active a {
  color: #fff;
}

.navigation-buttons {
  margin-top: 20px;
  text-align: center;
}

.navigation-buttons button {
  margin: 5px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  cursor: pointer;
  width: 120px;
  text-align: center;
  font-family: "Monda", sans-serif;
  transition: background-color 0.3s ease;
}

.bubble-container {
  margin-top: 1em;
}

.bubbles {
  display: flex;
  justify-content: center;
  margin: 1em 0;
  color: gray;
}

.bubbleWrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 15%;
}

.bubbleWrapper.selected .bubble {
  background-color: #42b983;
  color: white;
}

.bubble {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #ddd;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.bubble-label {
  margin-top: 0.5em;
  text-align: center;
  font-size: 10px;
  color: rgba(215,215,215,1);
  width:120px;
}

input {
  font-family: "Monda", sans-serif;
  background-color: rgba(0,0,0,0.1);
  color: rgba(215,215,215,1);
  outline: none;
  border: none;
  height: 28px;
  padding: 8px;
  border-radius: 8px;
}
</style>
