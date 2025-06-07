import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";

import ChatLayout from "./layouts/ChatLayout.vue";
import type { Component } from "vue";
import DashboardLayout from "./layouts/DashboardLayout.vue";

declare module "vue-router" {
  interface RouteMeta {
    layout?: Component;
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/chat",
  },
  {
    path: "/chat",
    name: "chat",
    component: () => import("@/pages/Chat.vue"),
    meta: { layout: ChatLayout },
  },
  {
    path: "/dashboard",
    name: "dashboard",
    component: () => import("@/pages/Dashboard.vue"),
    meta: { layout: DashboardLayout },
  },
  {
    path: "/documentation",
    name: "documentation",
    component: () => import("@/pages/News.vue"),
    meta: { layout: DashboardLayout },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
