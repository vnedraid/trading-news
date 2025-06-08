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

        <div class="flex ml-auto gap-3">
          <div className="flex items-center space-x-2">
            <Switch
              @update:model-value="handleToggle"
              :model-value="store.tradeMode"
              id="airplane-mode"
            />
            <Label htmlFor="airplane-mode">Trade Mode</Label>
          </div>
          <Button @click="openMap" variant="outline" size="icon">
            <Flame />
          </Button>
          <SettingsDialog />
        </div>
      </div>
    </div>
  </header>
  <slot />
</template>

<script setup>
import SettingsDialog from "@/components/SettingsDialog.vue";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useSummaryStore } from "@/shared/store/app";
import { Flame, GalleryVerticalEnd } from "lucide-vue-next";

const store = useSummaryStore();

const openMap = () => {
  store.toggle();
};

const handleToggle = () => {
  store.toggleTradeMode();
};
</script>
