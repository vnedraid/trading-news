import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { instance } from "../api";
import db from "../../../db.json";

export interface Root {
  body: Summary[];
  sources: Source[];
  shortNews: ShortNew[];
}

export interface Summary {
  ticker: string;
  summary: string;
  interpretation: string;
  sector: string;
  forecast: string;
  sources: string[];
}

export interface Source {
  id: string;
  title: string;
  link: string;
}

export interface ShortNew {
  id: string;
  title: string;
  desciprion: string;
  date: string;
  link: string;
}

export interface Settings {
  sectors: string[];
  tickers: string[];
  style: string;
}

export const useSummaryStore = defineStore("summary", () => {
  const summary = ref<Root>({ body: [], sources: [], shortNews: [] });

  async function getSumaryBySettings(
    settings: Settings = { sectors: [], tickers: [], style: "temperate" }
  ) {
    console.log(settings);
    const res = await instance.get("settings");
    console.log(res);
    summary.value.body = db.summary.body;
    summary.value.sources = [...db.summary.sources].splice(0, 3);
    summary.value.shortNews = db.summary.shortNews;
  }

  return { summary, getSumaryBySettings };
});
