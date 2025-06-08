<script setup lang="ts">
import Calendars from "@/components/Calendars.vue";
import DatePicker from "@/components/DatePicker.vue";
import NavUser from "@/components/NavUser.vue";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  type SidebarProps,
  SidebarSeparator,
} from "@/components/ui/sidebar";

const props = withDefaults(defineProps<SidebarProps>(), {
  collapsible: "none",
});

// This is sample data.
const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },
  calendars: [
    {
      name: "Recently viewed",
      items: ["Travel", "Reminders", "Deadlines"],
    },
  ],
};
</script>

<template>
  <Sidebar class="sticky hidden lg:flex top-0 h-svh border-l" v-bind="props">
    <SidebarHeader class="h-16 border-b border-sidebar-border">
      <NavUser :user="data.user" />
    </SidebarHeader>
    <SidebarContent>
      <DatePicker />
      <SidebarSeparator class="mx-0" />
      <Calendars :calendars="data.calendars" />
    </SidebarContent>
    <SidebarFooter> </SidebarFooter>
  </Sidebar>
</template>
