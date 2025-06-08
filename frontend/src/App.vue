<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import DefaultLayout from "./app/layouts/DefaultLayout.vue";
import { useSummaryStore } from "./shared/store/app";

const route = useRoute();

const layout = computed(() => route.meta.layout ?? DefaultLayout);

const { getSumaryBySettings } = useSummaryStore();

onMounted(() => {
  getSumaryBySettings();
});
</script>

<template>
  <div class="app-wrapper">
    <main class="flex flex-col flex-auto">
      <component :is="layout">
        <RouterView />
      </component>
    </main>
  </div>
</template>

<style>
.app-wrapper {
  display: flex;
  min-height: 100vh;
  width: 100%;
}
</style>
