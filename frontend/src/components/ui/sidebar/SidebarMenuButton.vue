<script setup lang="ts">
import type { Component } from "vue";
import { reactiveOmit } from "@vueuse/core";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import SidebarMenuButtonChild, {
  type SidebarMenuButtonProps,
} from "./SidebarMenuButtonChild.vue";
import { useSidebar } from "./utils";
import type { AsTag } from "reka-ui";

defineOptions({
  inheritAttrs: false,
});

const props = withDefaults(
  defineProps<
    SidebarMenuButtonProps & {
      tooltip?: string | Component;
      as?: AsTag | Component;
    }
  >(),
  {
    as: "button",
    variant: "default",
    size: "default",
  }
);

const { isMobile, state } = useSidebar();

const delegatedProps = reactiveOmit(props, "tooltip");
</script>

<template>
  <SidebarMenuButtonChild
    v-if="!tooltip"
    v-bind="{ ...delegatedProps, ...$attrs }"
    as="button"
  >
    <slot />
  </SidebarMenuButtonChild>

  <Tooltip v-else>
    <TooltipTrigger as-child>
      <SidebarMenuButtonChild
        v-bind="{ ...delegatedProps, ...$attrs }"
        as="button"
      >
        <slot />
      </SidebarMenuButtonChild>
    </TooltipTrigger>
    <TooltipContent
      side="right"
      align="center"
      :hidden="state !== 'collapsed' || isMobile"
    >
      <template v-if="typeof tooltip === 'string'">
        {{ tooltip }}
      </template>
      <component :is="tooltip" v-else />
    </TooltipContent>
  </Tooltip>
</template>
