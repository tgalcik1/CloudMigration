<template>
    <div class="instructions-container">
      <h1>Baseline Completed</h1>
      <p>Next, you are going to play three rounds of three different games.</p>
      <p>You will be able to read the instructions for each game on the screen and there will be a demo for each game that you can watch and repeat as many times as necessary until you understand how the game works.</p>
      <p>Some of the rounds will be more challenging than others. Please try your best and don’t give up.</p>
      <p>In between each round a brief set of questions will pop up on the screen that will ask you about how your experience playing the game. Just read the question and answer each one as honestly as you can.</p>
      <router-link to="/game" class="game-button">Start</router-link>
    </div>
  </template>
  
  <style scoped>
  .instructions-container {
    padding: 1em;
  }
  
  .game-button {
    display: inline-block;
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 5px;
  }
  
  .game-button:hover {
    background-color: #0056b3;
  }
  </style>
  