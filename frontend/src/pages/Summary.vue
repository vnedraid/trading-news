<script setup lang="ts">
import { useSummaryStore } from "@/shared/store/app";
import Home from "./Home.vue";

const store = useSummaryStore();
</script>

<template>
  <Home :summary="store.summary" />
</template>
