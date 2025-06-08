import { defineStore } from "pinia";
import { ref } from "vue";
import db from "../../../db.json";
import { instance } from "../api";

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
  const visibile = ref(false);
  const tradeMode = ref(false);

  function toggle() {
    visibile.value = !visibile.value;
  }

  function toggleTradeMode() {
    tradeMode.value = !tradeMode.value;
  }

  async function getSumaryBySettings(
    settings: Settings = { sectors: [], tickers: [], style: "temperate" }
  ) {
    const query = { agent: "test_news_analyzer_retriver" };

    const data = {
      messages: [
        {
          role: "content",
          content: `Я ${
            settings.style
          } инвестор, меня интересуют тикеры - ${settings.tickers.join(
            ","
          )} и следующие сектора эконимики ${settings.sectors.join(",")}`,
        },
      ],
    };

    try {
      const res = await instance.post(`${import.meta.env.VITE_API_URL}`, data, {
        params: query,
      });
      const result = JSON.parse(res.data.messages.at(-1).content);
      console.log(result);
      summary.value.body = result.body;
      summary.value.sources = [...db.summary.sources].splice(0, 3);
      summary.value.shortNews = db.summary.shortNews;
    } catch {
      summary.value.body = db.summary.body;
      summary.value.sources = [...db.summary.sources].splice(0, 3);
      summary.value.shortNews = db.summary.shortNews;
    }
  }

  return {
    summary,
    getSumaryBySettings,
    toggle,
    visibile,
    tradeMode,
    toggleTradeMode,
  };
});
