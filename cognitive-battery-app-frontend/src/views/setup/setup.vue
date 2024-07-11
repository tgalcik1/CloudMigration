<template>
    <div class="setup-container">
      <h1>Setup</h1>
      <div class="content">
        <div class="sidebar">
          <aside>Follow these steps to complete the setup.</aside>
          <ul class="step-list">
            <li :class="{ active: currentStepIndex === 0 }">
              <a href="#" @click.prevent="openStep(0)">1. ECG Setup</a>
            </li>
            <li :class="{ active: currentStepIndex === 1 }">
              <a href="#" @click.prevent="openStep(1)">2. Signal Quality Check</a>
            </li>
            <li :class="{ active: currentStepIndex === 2 }">
              <a href="#" @click.prevent="openStep(2)">3. Eye Tracking Calibration</a>
            </li>
          </ul>
          <div class="navigation-buttons">
            <button @click="previousStep" :disabled="currentStepIndex === 0">Previous</button>
            <button @click="nextStepOrComplete">{{ currentStepIndex === steps.length - 1 ? 'Complete Setup' : 'Next' }}</button>
          </div>
        </div>
        <div class="step-content" v-if="currentStep">
          <!-- Step 1: ECG device selection -->
          <div v-if="currentStepIndex === 0" class="device-instructions">
            <div :class="['device', { 'grayed-out': selectedEcgDevice !== 'arduino' }]">
              <button @click="selectEcgDevice('arduino')" :class="{ active: selectedEcgDevice === 'arduino' }">3-Lead ECG</button>
              <img src="images/ecg-diagram.png" alt="3-Lead ECG Device Setup" class="step-image">
              <p>Attach the three electrodes as shown in the diagram.</p>
            </div>
            <div :class="['device', { 'grayed-out': selectedEcgDevice !== 'movesense' }]">
              <button @click="selectEcgDevice('movesense')" :class="{ active: selectedEcgDevice === 'movesense' }">Movesense ECG</button>
              <img src="images/movesense.jpg" alt="Movesense ECG Device Setup" class="step-image">
              <p>Wrap the strap around your chest, ensuring the electrodes make firm contact with your skin.</p>
            </div>
            <div :class="['device', { 'grayed-out': selectedEcgDevice !== 'ecg3' }]">
              <button @click="selectEcgDevice('ecg3')" :class="{ active: selectedEcgDevice === 'ecg3' }">ECG Device 3</button>
              <img src="path/to/ecg-image-3.jpg" alt="ECG Device 3" class="step-image">
              <p>(insert directions for ECG device here)</p>
            </div>
          </div>

          <!-- Step 2: signal quality check -->
          <div v-else-if="currentStepIndex === 1">
            <button @click="signalQualityCheck()">Check Signal Quality</button>
            <p>Please wait while a research assistant checks the signal quality.</p>
          </div>

          <!-- other steps -->
          <div v-else>
            <p>{{ currentStep.instructions }}</p>
            <div v-if="currentStep.image">
              <img :src="currentStep.image" alt="Step Image" class="step-image">
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { mapState, mapActions } from 'vuex';
  
  export default {
    data() {
      return {
        currentStepIndex: 0,
        steps: [
          {
            title: 'ECG Setup',
            instructions: ''
          },
          {
            title: 'Signal Quality Check',
            image: '',
            instructions: 'Please wait while a research assistant checks the signal quality.'
          },
          {
            title: 'Eye Tracking Calibration',
            image: '',
            instructions: 'A research assistant will guide you through the eye tracking calibration process.'
          }
        ]
      };
    },
    computed: {
      ...mapState({
        subjectId: state => state.subjectId,
        selectedEcgDevice: state => state.selectedEcgDevice
      }),
      currentStep() {
        return this.steps[this.currentStepIndex];
      }
    },
    methods: {
      ...mapActions(['selectEcgDevice']),
      openStep(index) {
        this.currentStepIndex = index;
      },
      nextStep() {
        if (this.currentStepIndex < this.steps.length - 1) {
          this.currentStepIndex += 1;
        }
      },
      previousStep() {
        if (this.currentStepIndex > 0) {
          this.currentStepIndex -= 1;
        }
      },
      nextStepOrComplete() {
        if (this.currentStepIndex === this.steps.length - 1) {
          this.completeSetup();
        } else {
          this.nextStep();
        }
      },
      completeSetup() {
        this.$router.push('/baseline');
      },
      async signalQualityCheck() {
        const selectedEcgDevice = this.$store.state.selectedEcgDevice;
        const subjectId = this.$store.state.subjectId;
        // send a msg to main process to start processes
        window.api.send('toMain', { command: 'start-data-collection', subjectId: subjectId, device: selectedEcgDevice, task: 'signal-quality-check' });

        // receive data from main - maybe some sort of indication of signal quality if possible?
        await window.api.receive('fromMain', (data) => {
          console.log(data);
        });
      }
    },
    mounted() {
      this.openStep(0);
    }
  };
  </script>
  
  <style scoped>
  html, body, #app {
    height: 100%;
    margin: 0;
    padding: 0;
  }
  
  .setup-container {
    padding: 1em;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .content {
    display: flex;
    flex-grow: 1;
    margin-bottom: 20px;
  }
  
  .sidebar {
    width: 300px;
    background-color: #454545;
    color: white;
    padding: 1em;
    border-radius: 5px;
  }
  
  .step-list {
    list-style-type: none;
    padding: 0;
  }
  
  .step-list li {
    margin: 0.5em 0;
  }
  
  .step-list a {
    text-decoration: none;
    color: #42b983;
  }
  
  .step-list li.active a {
    color: #fff;
  }
  
  .navigation-buttons {
    margin-top: 20px;
  }
  
  .navigation-buttons button {
    margin: 5px;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    cursor: pointer;
    width: 45%;
    text-align: center;
  }
  
  .step-content {
    flex-grow: 1;
    margin-left: 20px;
    width: 500px;
  }
  
  .device-instructions {
    display: flex;
    justify-content: space-around;
    gap: 20px;
  }
  
  .device {
    flex: 1;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    text-align: center;
    background: white;
  }
  
  .device button {
    margin-bottom: 10px;
    padding: 10px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    width: 100%;
  }
  
  .device button.active {
    background-color: #42b983;
    color: white;
  }
  
  .grayed-out {
    opacity: 0.35;
    filter: grayscale(100%);
  }
  
  .step-image {
    max-width: 100%;
    height: auto;
  }
  </style>
  