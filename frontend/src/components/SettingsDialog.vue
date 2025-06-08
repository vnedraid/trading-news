<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { SettingsIcon } from "lucide-vue-next";
import MultiSelect from "./MultiSelect.vue";
import { ref, watch } from "vue";
import { useSummaryStore } from "@/shared/store/app";
import { useLocalStorage } from "@vueuse/core";
import { tickerOptions } from "@/shared/lib/const";

const localSotrage = useLocalStorage("settings", {
  sectors: [],
  tickers: [],
  style: "aggresive",
});

const sellingStyles = [
  { label: "Агрессивный", value: "aggresive" },
  { label: "Умеренный", value: "temperate" },
  { label: "Пассивный", value: "passive" },
];

const open = ref(false);
const store = useSummaryStore();
const handleChangeSector = (value: string[]) => {
  localSotrage.value.sectors = value;
};

const handleChangeTicker = (value: string[]) => {
  localSotrage.value.tickers = value;
};

const radioValue = ref(sellingStyles[0].value);
watch(radioValue, (newValue) => (localSotrage.value.style = newValue));

const sectorsOptions = [
  "Защита потребителей",
  "Здравоохранение",
  "Информационные технологии",
  "Коммунальные услуги",
  "Коммуникационные услуги",
  "Материалы",
  "Недвижимость",
  "Потребительские товары длительного пользования",
  "Потребительские товары не длительного пользования",
  "Промышленность",
  "Финансы",
  "Энергетика",
];

const handleSubmit = async () => {
  console.log(localSotrage.value);
  await store.getSumaryBySettings(localSotrage.value);
  open.value = false;
};
</script>

<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button variant="outline" size="icon">
        <SettingsIcon />
      </Button>
    </DialogTrigger>
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Настройки</DialogTitle>
      </DialogHeader>
      <div class="grid gap-4 py-4">
        <Label> Секторы </Label>
        <div class="grid grid-cols-4 items-center gap-4">
          <MultiSelect
            v-model="localSotrage.sectors"
            @change="handleChangeSector"
            :options="sectorsOptions"
          />
        </div>
        <Label> Тикеры </Label>
        <div class="grid grid-cols-4 items-center gap-4">
          <MultiSelect
            v-model="localSotrage.tickers"
            @change="handleChangeTicker"
            :options="tickerOptions"
          />
        </div>
        <Label> Стиль торговли </Label>
        <RadioGroup
          v-model="radioValue"
          :default-value="sellingStyles[0].value"
          :orientation="'vertical'"
        >
          <div
            v-for="item in sellingStyles"
            :key="item.value"
            class="flex items-center space-x-2"
          >
            <RadioGroupItem id="r1" :value="item.value" />
            <Label for="r1">{{ item.label }}</Label>
          </div>
        </RadioGroup>
      </div>
      <DialogFooter>
        <Button @click="handleSubmit"> Сохранить </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
