<template>
  <Card class="divide-y divide-border p-0">
    <CardContent class="p-0">
      <div
        v-for="(item, index) in items"
        :key="index"
        class="cursor-pointer hover:bg-accent hover:bg-opacity-10 transition-colors duration-200 p-2"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="font-medium">{{ item.title }}</div>
            <div class="text-sm text-muted-foreground">{{ item.subtitle }}</div>
          </div>
          <div class="text-xs text-muted-foreground">{{ item.caption }}</div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card } from "@/components/ui/card";
import CardContent from "./ui/card/CardContent.vue";

interface ListItem {
  title: string;
  subtitle: string;
  caption: string;
}

const items: ListItem[] = [
  {
    title: "Title",
    subtitle: "subtitle",
    caption: "caption",
  },
  {
    title: "Title",
    subtitle: "subtitle",
    caption: "caption",
  },
  {
    title: "Title",
    subtitle: "subtitle",
    caption: "caption",
  },
];
</script>
