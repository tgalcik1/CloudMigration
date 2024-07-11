<template>
  <div class="baseline-container">
    <h1>Baseline</h1>
    <p>We will now record five minutes of resting activity. During this time, please sit comfortably and remain still. Ensure you sit up straight and avoid crossing your legs.</p>
    <router-link to="/video" class="baseline-button">Start</router-link>
  </div>
</template>

<style scoped>
.baseline-container {
  padding: 1em;
}

.baseline-button {
  display: inline-block;
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 5px;
}

.baseline-button:hover {
  background-color: #0056b3;
}
</style>
