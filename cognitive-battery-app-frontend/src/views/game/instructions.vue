<template>
  <div class="instructions-wrapper">
    <div class="instructions-container">
      <h1>Baseline Completed</h1>
      <div class="instructions">
        <p>Thank you for your patience. Next, you are going to play three rounds of three different games.</p>
        <p>You will be able to read the instructions for each game on the screen before starting. There will be a demo for each game that you can watch and repeat as many times as necessary until you understand how the game works.</p>
        <p>Some of the rounds will be more challenging than others. Please try your best and don’t give up.</p>
        <p>In between each round, a brief set of questions will appear on the screen asking about your experience playing the game. Please answer each question as honestly as you can.</p>
      </div>
      <router-link to="/game" class="game-button">Start</router-link>
      </div>
    </div>
  </template>
  
  <style scoped>
  .instructions-wrapper{
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
  }

  .instructions-container {
    margin-top: 5%;
    text-align: center;
    margin-bottom: 10%;
  }

  .instructions {
    width: 35vw;
    text-align: left;
  }
  
  .game-button {
  display: inline-block;
  padding: 10px 20px;
  background-color: #42b983;
  color: white;
  text-decoration: none;
  border-radius: 5px;
  transition: background-color 0.3s ease;
  }

  .game-button:hover {
    background-color: #339267;
  }
  </style>
  