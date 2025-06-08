<template>
  <div class="flex-auto bg-gray-50 p-6 w-full">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      <!-- Main Content Container -->
      <Card class="lg:col-span-3 gap-4">
        <CardHeader>
          <CardTitle class="text-4xl"> Сводка </CardTitle>
        </CardHeader>
        <CardContent class="space-y-6 h-full flex flex-col">
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
                      {{ item.summary }}
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
                    <span class="text-muted-foreground">
                      {{ item.interpretation }}
                    </span>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
              <!-- <Card
                v-for="(summaryItem, index) in summary.body"
                :key="index"
                class="gap-2 bg-white flex flex-col hover:bg-gray-50 transition-colors w-full p-4 px-0"
              >
                <CardHeader class="w-full">
                  <CardTitle class="line-clamp-2 flex gap-4 text-xl">
                    {{ summaryItem.ticker }}

                    <Badge
                      v-if="summaryItem.forecast !== FORECAST.NEUTRAl"
                      variant="outline"
                    >
                      <TrendingUp
                        v-if="summaryItem.forecast === FORECAST.POSITIVE"
                        class="inline-flex size-6"
                      />
                      <TrendingDown
                        v-if="summaryItem.forecast === FORECAST.NEGATIVE"
                        class="inline-flex size-6"
                      />
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <a :href="summaryItem.sources[0]" target="_blank">
                    <div class="flex gap-2 font-medium">
                      {{ summaryItem.summary }}
                    </div>
                  </a>
                  <CardDescription>
                    {{ summaryItem.interpretation }}
                  </CardDescription>
                </CardContent>
                <CardFooter v-if="summaryItem.sources[0]"> </CardFooter>
              </Card> -->
            </div>
          </div>

          <Separator />

          <!-- Three Bottom Content Areas -->
          <Card class="bg-gray-50 gap-4" v-if="summary.sources.length > 0">
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
                  <CardTitle class="line-clamp-2">{{ source.title }}</CardTitle>
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

      <!-- News Feed Sidebar -->
      <Card class="lg:col-span-1 min-h-[500px]">
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
                  <CardTitle class="line-clamp-2"> {{ item.title }}</CardTitle>
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
import { onMounted } from "vue";
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

enum FORECAST {
  POSITIVE = "positive",
  NEGATIVE = "negative",
  NEUTRAl = "neutral",
}

defineProps<{ summary: Root }>();

// Component logic can be added here
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
