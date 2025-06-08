<template>
  <div class="flex-auto bg-gray-50 p-6 w-full">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      <Card class="lg:col-span-1">
        <CardContent class="h-full">
          <h2 class="text-lg font-semibold text-gray-800 mb-4 text-center">
            Short summary
          </h2>
          <div class="space-y-3">
            <div
              v-for="index in 5"
              :key="index"
              class="border border-gray-200 rounded-lg p-4 min-h-[100px] flex items-center justify-center hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div class="text-center">
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
        </CardContent>
      </Card>
      <!-- Main Content Container -->
      <Card class="lg:col-span-3">
        <CardContent class="space-y-6 h-full flex flex-col">
          <!-- Large Content Area -->
          <Card
            class="bg-gray-50 p-8 min-h-[400px] flex items-center justify-center flex-auto relative overflow-auto"
          >
            <CardContent class="text-center absolute top-0 left-0">
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
              <p class="text-sm text-gray-400 mt-1">
                Здесь будет размещен основной контент
              </p>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { Card, CardContent } from "@/components/ui/card";

// Component logic can be added here
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
