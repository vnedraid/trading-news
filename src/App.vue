<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import DefaultLayout from "./app/layouts/DefaultLayout.vue";

const route = useRoute();

const layout = computed(() => route.meta.layout ?? DefaultLayout);
</script>

<template>
  <div class="app-wrapper">
    <main>
      <component :is="layout">
        <RouterView />
      </component>
    </main>
  </div>
</template>

<style>
.app-wrapper {
  min-height: 100vh;
  width: 100%;
}
</style>
