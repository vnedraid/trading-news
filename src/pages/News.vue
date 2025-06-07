<template>
  <div class="flex-auto bg-gray-50 p-6 w-full">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Main Content Container -->
      <div class="lg:col-span-3">
        <div class="bg-white border border-gray-300 rounded-xl p-6 space-y-6">
          <!-- Settings Button -->
          <div class="flex justify-end">
            <Button
              class="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              Настройки
            </Button>
          </div>

          <!-- Large Content Area -->
          <div
            class="bg-gray-50 border border-gray-200 rounded-xl p-8 min-h-[400px] flex items-center justify-center"
          >
            <div class="text-center text-gray-500">
              <div
                class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-lg flex items-center justify-center"
              >
                <svg
                  class="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <p class="text-lg font-medium">Основной контент</p>
              <p class="text-sm text-gray-400 mt-1">
                Здесь будет размещен основной контент
              </p>
            </div>
          </div>

          <!-- Three Bottom Content Areas -->
          <div class="bg-gray-50 border border-gray-200 rounded-xl p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                v-for="index in 3"
                :key="index"
                class="bg-white border border-gray-200 rounded-lg p-6 min-h-[120px] flex items-center justify-center hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div class="text-center text-gray-500">
                  <div
                    class="w-8 h-8 mx-auto mb-2 bg-gray-100 rounded flex items-center justify-center"
                  >
                    <svg
                      class="w-4 h-4 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <p class="text-sm font-medium">Контент {{ index }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- News Feed Sidebar -->
      <div class="lg:col-span-1">
        <div class="bg-white border border-gray-300 rounded-xl p-4 h-full">
          <h2 class="text-lg font-semibold text-gray-800 mb-4 text-center">
            Лента новостей
          </h2>
          <div class="space-y-3">
            <div
              v-for="index in 5"
              :key="index"
              class="border border-gray-200 rounded-lg p-4 min-h-[100px] flex items-center justify-center hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div class="text-center text-gray-500">
                <div
                  class="w-6 h-6 mx-auto mb-2 bg-gray-100 rounded flex items-center justify-center"
                >
                  <svg
                    class="w-3 h-3 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"
                    />
                  </svg>
                </div>
                <p class="text-xs font-medium">Новость {{ index }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button } from "@/components/ui/button";

// Component logic can be added here
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
