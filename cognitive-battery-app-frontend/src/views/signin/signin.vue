<template>
    <div class="signin-container">
      <h1>Sign In</h1>
      <p>Enter your subject ID.</p>
      <input v-model="subjectId" type="text" id="subject-id" placeholder="Subject ID">
      <button @click="signIn" id="signin-button">Sign In</button>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
  </template>
  
  <script>
  import { mapActions } from 'vuex';
  
  export default {
    data() {
      return {
        subjectId: '',
        errorMessage: ''
      };
    },
    methods: {
      ...mapActions(['login']),
      signIn() {
        if (this.subjectId.trim() === '') {
          this.errorMessage = 'Subject ID cannot be empty';
        } else {
          this.errorMessage = '';
          this.login(this.subjectId);
          this.$router.push('/');
        }
      }
    }
  };
  </script>
  
  <style>
  .error {
    color: red;
  }
  </style>
  