import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir:"./tests", timeout:30000, fullyParallel:true, workers:2,
  use:{baseURL:"http://127.0.0.1:4175", browserName:"chromium", channel:"msedge", headless:true, screenshot:"only-on-failure"},
  webServer:{command:"npm run dev -- --host 127.0.0.1 --port 4175 --strictPort", url:"http://127.0.0.1:4175", reuseExistingServer:false, timeout:30000},
});
