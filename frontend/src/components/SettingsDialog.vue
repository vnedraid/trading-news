<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
const sellingStyles = [
  { label: "Агрессивный", value: "aggresive" },
  { label: "Умеренный", value: "temperate" },
  { label: "Пассивный", value: "passive" },
];
const sectors = ref([]);

const handleChangeSector = (value: string[]) => {
  sectors.value = value;
};

const tickers = ref([]);
const handleChangeTicker = (value: string[]) => {
  tickers.value = value;
};

const radioValue = ref("");
watch(radioValue, (newValue) => console.log(newValue));

const handleSubmit = () => {
  console.log({
    sectors: sectors.value,
    tickers: tickers.value,
    style: radioValue.value,
  });
};
</script>

<template>
  <Dialog>
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
          <MultiSelect @change="handleChangeSector" />
        </div>
        <Label> Тикеры </Label>
        <div class="grid grid-cols-4 items-center gap-4">
          <MultiSelect @change="handleChangeTicker" />
        </div>
        <Label> Стиль торговли </Label>
        <RadioGroup
          v-model="radioValue"
          :default-value="sellingStyles[1].value"
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
