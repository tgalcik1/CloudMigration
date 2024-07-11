<template>
  <div id="app">
    <Navbar v-if="$route.name !== 'signin'" />

    <router-view></router-view>
  </div>
</template>

<script>
import Navbar from './components/navbar.vue';

export default {
  name: 'App',
  components: {
    Navbar,
  }
};
</script>

<style>

</style>
