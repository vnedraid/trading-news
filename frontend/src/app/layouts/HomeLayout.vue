<template>
  <header class="border-b bg-background sticky top-0 z-50 w-full">
    <div class="container-wrapper 3xl:fixed:px-0 px-6">
      <!-- Left: Logo + Navigation -->
      <div
        class="3xl:fixed:container flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:!h-4"
      >
        <!-- Logo -->
        <div
          class="3xl:fixed:container flex h-(--header-height) items-center gap-2 **:data-[slot=separator]:!h-4"
        >
          <RouterLink to="/">
            <div
              class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
            >
              <GalleryVerticalEnd class="size-4" />
            </div>
          </RouterLink>
        </div>

        <!-- Navigation Links -->
        <nav class="items-center gap-0.5 hidden lg:flex">
          <RouterLink
            v-for="(link, index) in navLinks"
            :key="index"
            :to="link.href"
            class="inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50 h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5 text-primary"
          >
            {{ link.label }}
          </RouterLink>
        </nav>

        <div class="flex ml-auto">
          <SettingsDialog />
        </div>
      </div>
    </div>
  </header>
  <slot />
</template>

<script setup>
import SettingsDialog from "@/components/SettingsDialog.vue";
import { GalleryVerticalEnd, Icon, Link, SettingsIcon } from "lucide-vue-next";
import { useRoute } from "vue-router";

const route = useRoute();

// Normalize paths to compare them reliably
const isActive = (href) => {
  return route.path.replace(/\/+$/, "") === href.replace(/\/+$/, "");
};

const navLinks = [
  { label: "Home", href: "/" },
  // { label: "News", href: "/news" },
];
</script>
