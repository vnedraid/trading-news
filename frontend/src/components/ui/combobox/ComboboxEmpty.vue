<script setup lang="ts">
import type { ComboboxEmptyProps } from "reka-ui";
import type { HTMLAttributes } from "vue";
import { reactiveOmit } from "@vueuse/core";
import { ComboboxEmpty } from "reka-ui";
import { cn } from "@/shared/lib/utils";

const props = defineProps<
  ComboboxEmptyProps & { class?: HTMLAttributes["class"] }
>();

const delegatedProps = reactiveOmit(props, "class");
</script>

<template>
  <ComboboxEmpty
    data-slot="combobox-empty"
    v-bind="delegatedProps"
    :class="cn('px-2 py-1.5 text-center text-sm', props.class)"
  >
    <slot />
  </ComboboxEmpty>
</template>
