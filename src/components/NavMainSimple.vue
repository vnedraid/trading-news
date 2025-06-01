<script setup lang="ts">
import type { LucideIcon } from "lucide-vue-next";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { RouterLink, type RouteRecordNameGeneric } from "vue-router";

defineProps<{
  items: {
    title: string;
    url: string;
    icon: LucideIcon;
    isActive?: boolean;
    routeName?: RouteRecordNameGeneric;
  }[];
}>();
</script>

<template>
  <SidebarGroup>
    <SidebarMenu>
      <SidebarMenuItem v-for="item in items" :key="item.title">
        <SidebarMenuButton as-child :is-active="item.isActive">
          <RouterLink :to="{ name: item.routeName }">
            <component :is="item.icon" />
            <span>{{ item.title }}</span>
          </RouterLink>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  </SidebarGroup>
</template>
