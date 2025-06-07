import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";

import type { Component } from "vue";
import HomeLayout from "./layouts/HomeLayout.vue";
import NewsLayout from "./layouts/NewsLayout.vue";

declare module "vue-router" {
  interface RouteMeta {
    layout?: Component;
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/home",
  },
  {
    path: "/home",
    name: "home",
    component: () => import("@/pages/Home.vue"),
    meta: { layout: HomeLayout },
  },
  {
    path: "/news",
    name: "news",
    component: () => import("@/pages/News.vue"),
    meta: { layout: NewsLayout },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
