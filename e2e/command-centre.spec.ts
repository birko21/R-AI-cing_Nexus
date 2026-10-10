import { expect, test } from '@playwright/test';

test('command centre filters codes and distinguishes data states', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today / Command Centre' })).toBeVisible();
  await expect(page.getByText('DEMO ONLY')).toBeVisible();
  await expect(page.getByText('SYNTHETIC_ONLY')).toBeVisible();
  await expect(page.getByText('Fictional Thoroughbred Park')).toBeVisible();
  await expect(page.getByText('Fictional Harness Circuit')).toBeVisible();
  await expect(page.getByText('Fictional Greyhound Track')).toBeVisible();

  await page.getByRole('button', { name: 'Greyhound' }).click();
  await expect(page.getByRole('region', { name: 'Today command cards' }).getByText('No racing')).toBeVisible();
  await expect(page.getByText('Fictional Greyhound Track')).toBeVisible();

  await page.getByRole('button', { name: 'All codes' }).click();
  await page.getByLabel('Data state').selectOption('NO_DATA');
  await expect(page.getByRole('region', { name: 'Today command cards' }).getByText('No data')).toBeVisible();
  await expect(page.getByText('No evidence is shown')).toBeVisible();

  await page.getByLabel('Data state').selectOption('ALL');
  await page.getByLabel('Show availability examples').uncheck();
  await expect(page.getByText('Fictional Thoroughbred Park')).toBeVisible();
  await expect(page.getByText('No racing')).not.toBeVisible();

  await page.screenshot({ path: 'docs/evidence/ril-017/command-centre-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'docs/evidence/ril-017/command-centre-mobile.png', fullPage: true });
});
