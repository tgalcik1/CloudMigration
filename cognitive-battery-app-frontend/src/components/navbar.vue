<template>
    <div id="navbar" v-if="subjectId">
      
      <span>Subject ID: <strong>{{ subjectId }}</strong></span>

      <Status></Status>

      <button @click="goToHome" id="home-button">
        <i class="fas fa-house"></i>
      </button>
      <button @click="performLogout" id="logout-button">
        <i class="fas fa-sign-out-alt"></i>
      </button>
    </div>
  </template>
  
  <script>
  import { mapState, mapActions } from 'vuex';
  import Status from './status.vue'
  import '@fortawesome/fontawesome-free/css/all.css';
  
  export default {
    components: {
      Status
    },
    computed: {
      ...mapState(['subjectId', 'steps', 'currentStepIndex']),
      isFirstStep() {
        return this.currentStepIndex === 0;
      },
      isLastStep() {
        return false; //return this.currentStepIndex === this.steps.length - 1;
      }
    },
    methods: {
      ...mapActions(['logout', 'nextStep', 'previousStep', 'goToHome']),
      performLogout() {
        this.logout();
      },
      goToHome() {
        this.$router.push('/');
      }
    }
  };
  </script>
  
  <style>
  #navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1em;
    background-color: #f8f8f8;
    border-bottom: 1px solid #ddd;
    font-size: 10px;
  }
  
  #logout-button, #home-button {
    padding: 0.5em 1em;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin: 0 0.5em;
  }

  #home-button {
    background-color: #42b983;
  }
  
  #logout-button {
    background-color: #f44336;
  }

  #home-button:hover {
    background-color: #358a6e;
  }
  
  #logout-button:hover {
    background-color: #d32f2f;
  }
  
  span {
    margin-right: auto;
    padding-right: 20px;
  }
  </style>
  