import { createApp } from "vue";
import App from "../App.vue";
import { createPinia } from "pinia";
import { router } from "./router";

export const bootstrap = async () => {
  const pinia = createPinia();

  createApp(App).use(pinia).use(router).mount("#app");
};
