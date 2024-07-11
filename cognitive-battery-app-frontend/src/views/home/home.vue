<template>
  <div class="home-container">
    <h1>Home Page</h1>
    <ul>
      <li v-for="route in filteredRoutes" :key="route.path">
        <router-link :to="route.path">{{ route.name || route.path }}</router-link>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  data() {
    return {
      routes: []
    };
  },
  computed: {
    filteredRoutes() {
      return this.routes.filter(route => !route.meta.hidden);
    }
  },
  mounted() {
    this.routes = this.$router.getRoutes().filter(route => route.name);
  }
};
</script>

<style scoped>
.home-container {
  padding: 1em;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  margin: 0.5em 0;
}

a {
  text-decoration: none;
  color: #42b983;
}
</style>
