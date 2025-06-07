<template>
  <div class="flex flex-1 flex-col gap-4 p-4">
    <div class="chart-container h-full">
      <div class="grid grid-cols-4 grid-rows-7 gap-4 h-full">
        <Card class="col-span-4 row-span-3 col-start-1 row-start-2">
          <CardHeader>
            <CardTitle> Total Visitors </CardTitle>
            <CardDescription>
              <span className="hidden @[540px]/card:block">
                Total for the last 3 months
              </span>
              <span className="@[540px]/card:hidden">Last 3 months</span>
            </CardDescription>
          </CardHeader>
          <CardContent class="h-full">
            <LWChart
              :type="chartType"
              :data="data"
              autosize
              :chart-options="chartOptions"
              :series-options="seriesOptions"
              ref="lwChart"
              class="h-auto"
            />
          </CardContent>
          <CardContent>
            <CardAction class="flex gap-2">
              <Button type="button" @click="changeColors">
                Set Random Colors
              </Button>
              <Button type="button" @click="changeType">
                Change Chart Type
              </Button>
              <Button type="button" @click="changeData">Change Data</Button>
            </CardAction>
          </CardContent>
        </Card>
        <Card class="col-span-2 row-span-2 col-start-1 row-start-5">3</Card>
        <Card class="col-span-2 row-span-2 col-start-3 row-start-5">4</Card>
        <Card class="col-start-1 row-start-1">5</Card>
        <Card class="col-start-2 row-start-1">6</Card>
        <Card class="col-start-3 row-start-1">7</Card>
        <Card class="col-start-4 row-start-1">8</Card>
        <Card class="col-span-4 row-span-2 row-start-7">9</Card>
      </div>
    </div>
  </div>
</template>
<style scoped>
.chart-container {
  height: calc(100% - 3.2em);
}
</style>

<script setup>
import { ref } from "vue";
import LWChar from "@/components/LWChart.vue";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import LWChart from "@/components/LWChart.vue";

/**
 * Generates sample data for the Lightweight Charts™ example
 * @param  {Boolean} ohlc Whether generated dat should include open, high, low, and close values
 * @returns {Array} sample data
 */
function generateSampleData(ohlc) {
  const randomFactor = 25 + Math.random() * 25;
  function samplePoint(i) {
    return (
      i *
        (0.5 +
          Math.sin(i / 10) * 0.2 +
          Math.sin(i / 20) * 0.4 +
          Math.sin(i / randomFactor) * 0.8 +
          Math.sin(i / 500) * 0.5) +
      200
    );
  }

  const res = [];
  let date = new Date(Date.UTC(2018, 0, 1, 0, 0, 0, 0));
  const numberOfPoints = ohlc ? 100 : 500;
  for (var i = 0; i < numberOfPoints; ++i) {
    const time = date.getTime() / 1000;
    const value = samplePoint(i);
    if (ohlc) {
      const randomRanges = [
        -1 * Math.random(),
        Math.random(),
        Math.random(),
      ].map((i) => i * 10);
      const sign = Math.sin(Math.random() - 0.5);
      res.push({
        time,
        low: value + randomRanges[0],
        high: value + randomRanges[1],
        open: value + sign * randomRanges[2],
        close: samplePoint(i + 1),
      });
    } else {
      res.push({
        time,
        value,
      });
    }

    date.setUTCDate(date.getUTCDate() + 1);
  }

  return res;
}

const chartOptions = ref({});
const data = ref(generateSampleData(false));
const seriesOptions = ref({
  color: "rgb(45, 77, 205)",
});
const chartType = ref("line");
const lwChart = ref();

function randomShade() {
  return Math.round(Math.random() * 255);
}

const randomColor = (alpha = 1) => {
  return `rgba(${randomShade()}, ${randomShade()}, ${randomShade()}, ${alpha})`;
};

const colorsTypeMap = {
  area: [
    ["topColor", 0.4],
    ["bottomColor", 0],
    ["lineColor", 1],
  ],
  bar: [
    ["upColor", 1],
    ["downColor", 1],
  ],
  baseline: [
    ["topFillColor1", 0.28],
    ["topFillColor2", 0.05],
    ["topLineColor", 1],
    ["bottomFillColor1", 0.28],
    ["bottomFillColor2", 0.05],
    ["bottomLineColor", 1],
  ],
  candlestick: [
    ["upColor", 1],
    ["downColor", 1],
    ["borderUpColor", 1],
    ["borderDownColor", 1],
    ["wickUpColor", 1],
    ["wickDownColor", 1],
  ],
  histogram: [["color", 1]],
  line: [["color", 1]],
};

// Set a random colour for the series as an example of how
// to apply new options to series. A similar appraoch will work on the
// option properties.
const changeColors = () => {
  const options = {};
  const colorsToSet = colorsTypeMap[chartType.value];
  colorsToSet.forEach((c) => {
    options[c[0]] = randomColor(c[1]);
  });
  seriesOptions.value = options;
};

const changeData = () => {
  const candlestickTypeData = ["candlestick", "bar"].includes(chartType.value);
  const newData = generateSampleData(candlestickTypeData);
  data.value = newData;
  if (chartType.value === "baseline") {
    const average =
      newData.reduce((s, c) => {
        return s + c.value;
      }, 0) / newData.length;
    seriesOptions.value = { baseValue: { type: "price", price: average } };
  }
};

const changeType = () => {
  const types = [
    "line",
    "area",
    "baseline",
    "histogram",
    "candlestick",
    "bar",
  ].filter((t) => t !== chartType.value);
  const randIndex = Math.round(Math.random() * (types.length - 1));
  chartType.value = types[randIndex];
  changeData();

  // call a method on the component.
  lwChart.value.fitContent();
};
</script>
