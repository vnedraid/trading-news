<template>
  <div class="flex-auto bg-gray-50 p-6 w-full">
    <div class="flex gap-6 h-full w-full">
      <ResizablePanelGroup direction="horizontal" :key="key">
        <ResizablePanel
          :default-size="70"
          :min-size="defaultValuesForResize.left"
        >
          <!-- Main Content Container -->
          <Card class="lg:col-span-3 gap-4 mr-3 h-full">
            <CardHeader>
              <CardTitle class="text-4xl"> Сводка </CardTitle>
            </CardHeader>
            <CardContent class="space-y-6 h-full flex flex-col @container">
              <!-- Large Content Area -->
              <div
                class="p-8 min-h-[400px] flex items-center justify-center flex-auto relative overflow-auto border-0"
              >
                <div class="flex flex-col absolute top-0 left-0 w-full gap-4">
                  <Accordion type="multiple" class="w-full" collapsible>
                    <AccordionItem
                      v-for="(item, index) in summary.body"
                      :key="index"
                      :value="item.ticker"
                    >
                      <AccordionTrigger>
                        <div class="inline-flex items-start gap-2">
                          <span class="hidden @md:flex">
                            {{ item.summary }}
                          </span>
                          <Badge class="inline-flex" variant="outline">
                            {{ item.ticker }}
                          </Badge>
                          <Badge
                            class="inline-flex min-h-[22px]"
                            v-if="item.forecast !== FORECAST.NEUTRAl"
                            variant="outline"
                          >
                            <TrendingUp
                              v-if="item.forecast === FORECAST.POSITIVE"
                              class="inline-flex size-6"
                            />
                            <TrendingDown
                              v-if="item.forecast === FORECAST.NEGATIVE"
                              class="inline-flex size-6"
                            />
                          </Badge>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div class="@md:hidden">
                          {{ item.summary }}
                        </div>
                        <span class="text-muted-foreground">
                          {{ item.interpretation }}
                        </span>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              </div>

              <Separator />

              <!-- Three Bottom Content Areas -->
              <Card
                class="bg-gray-50 gap-4 hidden @md:flex"
                v-if="summary.sources.length > 0"
              >
                <CardHeader>
                  <CardTitle>Источники</CardTitle>
                </CardHeader>
                <CardContent class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card
                    v-for="(source, index) in summary.sources"
                    :key="index"
                    class="gap-2 bg-white flex flex-col hover:bg-gray-50 transition-colors cursor-pointer w-full"
                  >
                    <CardHeader class="w-full">
                      <CardTitle class="line-clamp-2">{{
                        source.title
                      }}</CardTitle>
                    </CardHeader>
                    <CardContent class="flex justify-start text-left">
                      <a
                        href="https://www.globenewswire.com/news-release/2021/08/30/2288355/0/en/Protagenic-Therapeutics-to-Host-Virtual-Science-Review-Wednesday-September-8th-at-10-AM-ET.html"
                        target="_blank"
                        class="text-xs opacity-60 max-w-40 truncate"
                      >
                        {{ source.link }}
                      </a>
                    </CardContent>
                  </Card>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </ResizablePanel>
        <ResizableHandle with-handle />
        <ResizablePanel
          :default-size="30"
          :min-size="defaultValuesForResize.right"
          ><!-- News Feed Sidebar -->
          <Card class="lg:col-span-1 min-h-[500px] ml-3 h-full">
            <CardContent class="h-full overflow-hidden">
              <h2 class="text-lg font-semibold text-gray-800 mb-4">Новости</h2>
              <div class="space-y-3 relative h-full overflow-auto">
                <div class="flex flex-col gap-4 absolute w-full">
                  <Card
                    v-for="(item, index) in summary.shortNews"
                    :key="index"
                    class="gap-2 bg-white flex flex-col hover:bg-gray-50 transition-colors cursor-pointer w-full"
                  >
                    <CardHeader class="w-full">
                      <CardTitle class="line-clamp-2">
                        {{ item.title }}</CardTitle
                      >
                      <CardDescription class="line-clamp-1">
                        {{ item.date }}
                      </CardDescription>
                      <CardDescription class="line-clamp-3">
                        {{ item.desciprion }}
                      </CardDescription>
                    </CardHeader>
                    <CardContent class="flex justify-start text-left">
                      <a
                        :href="item.link"
                        target="_blank"
                        class="text-xs opacity-60 max-w-40 truncate"
                      >
                        {{ item.link }}
                      </a>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card></ResizablePanel
        >
      </ResizablePanelGroup>

      <Card v-if="store.visibile" class="lg:col-span-1 min-h-[500px] gap-0">
        <CardHeader>
          <CardTitle class="pb-0"> Тепловая карта </CardTitle>
        </CardHeader>
        <CardContent class="h-full overflow-hidden">
          <VueApexCharts
            type="treemap"
            height="100%"
            :options="chartOptions"
            :series="series"
            class="h-full"
          ></VueApexCharts>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { onMounted, ref, watch } from "vue";
import { Badge } from "@/components/ui/badge";
import { TrendingDown, TrendingUp } from "lucide-vue-next";
import { Separator } from "@/components/ui/separator";
import { useSummaryStore, type Root } from "@/shared/store/app";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import VueApexCharts from "vue3-apexcharts";
import type { ApexOptions } from "apexcharts";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { storeToRefs } from "pinia";

enum FORECAST {
  POSITIVE = "positive",
  NEGATIVE = "negative",
  NEUTRAl = "neutral",
}

defineProps<{ summary: Root }>();

const defaultValuesForResize = ref({
  left: 70,
  right: 30,
});

const store = useSummaryStore();
const { tradeMode } = storeToRefs(store);
const key = ref(crypto.randomUUID());

watch(tradeMode, (newValue) => {
  if (newValue) {
    defaultValuesForResize.value.left = 20;
    defaultValuesForResize.value.right = 80;
  } else {
    defaultValuesForResize.value.left = 70;
    defaultValuesForResize.value.right = 30;
  }
  key.value = crypto.randomUUID();
});
const series = [
  {
    data: [
      {
        x: "INTC",
        y: 1.2,
      },
      {
        x: "GS",
        y: 0.4,
      },
      {
        x: "CVX",
        y: -1.4,
      },
      {
        x: "GE",
        y: 2.7,
      },
      {
        x: "CAT",
        y: -0.3,
      },
      {
        x: "RTX",
        y: 5.1,
      },
      {
        x: "CSCO",
        y: -2.3,
      },
      {
        x: "JNJ",
        y: 2.1,
      },
      {
        x: "PG",
        y: 0.3,
      },
      {
        x: "TRV",
        y: 0.12,
      },
      {
        x: "MMM",
        y: -2.31,
      },
      {
        x: "NKE",
        y: 3.98,
      },
      {
        x: "IYT",
        y: 1.67,
      },
    ],
  },
];

const chartOptions: ApexOptions = {
  legend: {
    show: false,
  },
  chart: {
    height: 1000,
    type: "treemap",
    toolbar: { show: false },
  },
  dataLabels: {
    enabled: true,
    style: {
      fontSize: "12px",
    },
    formatter: function (text, op) {
      return [text, op.value];
    },
    offsetY: -4,
  },
  plotOptions: {
    treemap: {
      enableShades: true,
      shadeIntensity: 0.5,
      reverseNegativeShade: true,
      colorScale: {
        ranges: [
          {
            from: -6,
            to: 0,
            color: "#CD363A",
          },
          {
            from: 0.001,
            to: 6,
            color: "#52B12C",
          },
        ],
      },
    },
  },
};

// Component logic can be added here
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
