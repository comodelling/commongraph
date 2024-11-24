<template>
    <div class="side-menu">
        <div class="title">Menu</div>
        <router-link to="/">Main Page</router-link><br />
        <router-link to="/about">About ObjectiveNet</router-link>
    </div>
  </template>
  
  <script>
  export default {};
  </script>
  
  <style scoped>
  .side-menu {
    width: 175px;
    min-width: 150px;
    height: 90vh;
    border: 1px solid #ccc;
    padding: 10px;
    font-size: 12px;
    /* margin-top: 50px; */
    margin-left: 10px;
    margin-top: 20px;
  }
  .side-menu .title {
    font-size: 20px;
    font-weight: bold;
}
  </style>