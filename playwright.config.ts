import { defineConfig } from '@playwright/test';

const port = Number(process.env.WEB_PORT ?? 5173);

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    browserName: 'chromium',
    headless: true,
  },
  webServer: {
    command: `pnpm --filter @racing-intelligence/web dev --host 127.0.0.1 --port ${port}`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: process.env.PLAYWRIGHT_REUSE_SERVER !== 'false',
    timeout: 60_000,
  },
});
