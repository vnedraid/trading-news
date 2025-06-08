<script setup lang="ts">
import { useFilter } from "reka-ui";
import { computed, ref, type PropType } from "vue";
import {
  Combobox,
  ComboboxAnchor,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import {
  TagsInput,
  TagsInputInput,
  TagsInputItem,
  TagsInputItemDelete,
  TagsInputItemText,
} from "@/components/ui/tags-input";

const open = ref(false);
const searchTerm = ref("");
const props = defineProps({
  placeholder: String,
  options: Array as PropType<{ label: string; value: string }[]>,
});
const emits = defineEmits(["change"]);
const model = defineModel<string[]>({ default: [] });

const { contains } = useFilter({ sensitivity: "base" });
const filteredOptions = computed(() => {
  const options = props.options.filter((i) => !model.value.includes(i.label));
  return searchTerm.value
    ? options.filter((option) => contains(option.label, searchTerm.value))
    : options;
});
</script>

<template>
  <Combobox v-model="model" v-model:open="open" :ignore-filter="true">
    <ComboboxAnchor as-child>
      <TagsInput v-model="model" class="px-2 gap-2 w-80">
        <div class="flex gap-2 flex-wrap items-center">
          <TagsInputItem v-for="item in model" :key="item" :value="item">
            <TagsInputItemText />
            <TagsInputItemDelete />
          </TagsInputItem>
        </div>

        <ComboboxInput v-model="searchTerm" as-child>
          <TagsInputInput
            :placeholder
            class="w-full p-0 border-none focus-visible:ring-0 h-auto"
            @click="open = true"
          />
        </ComboboxInput>
      </TagsInput>

      <ComboboxList class="w-[--reka-popper-anchor-width]">
        <ComboboxEmpty />
        <ComboboxGroup>
          <ComboboxItem
            v-for="framework in filteredOptions"
            :key="framework.value"
            :value="framework.label"
            @select.prevent="
              (ev) => {
                if (typeof ev.detail.value === 'string') {
                  searchTerm = '';
                  model.push(ev.detail.value);
                  console.log(model);
                }
              }
            "
          >
            {{ framework.label }}
          </ComboboxItem>
        </ComboboxGroup>
      </ComboboxList>
    </ComboboxAnchor>
  </Combobox>
</template>
