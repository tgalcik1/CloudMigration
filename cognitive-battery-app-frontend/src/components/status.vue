<template>
    <div>
      <h2>Status Updates</h2>
      <p>{{ statusMessage }}</p>
    </div>
  </template>
  
  <script>
  export default {
    data() {
      return {
        statusMessage: 'waiting...'
      };
    },
    mounted() {
      if (window.api && window.api.receive) {
        window.api.receive('fromMain', (data) => {
          if (data.status) {
            this.statusMessage = data.status;
          } else if (data.error) {
            this.statusMessage = `error: ${data.error}`;
          }
        });
      }
    }
  };
  </script>

  