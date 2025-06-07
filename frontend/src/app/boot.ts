import { createApp } from "vue";
import App from "../App.vue";
import { router } from "./router";

export const bootstrap = async () => {
  createApp(App).use(router).mount("#app");
};
