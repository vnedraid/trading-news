import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";

import ChatLayout from "./layouts/ChatLayout.vue";
import type { Component } from "vue";

declare module "vue-router" {
  interface RouteMeta {
    layout?: Component;
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("@/pages/Main.vue"),
    meta: { layout: ChatLayout },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
