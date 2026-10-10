import { expect, test } from '@playwright/test';

test('command centre filters codes and distinguishes data states', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today / Command Centre' })).toBeVisible();
  await expect(page.getByText('DEMO ONLY')).toBeVisible();
  await expect(page.getByText('SYNTHETIC_ONLY')).toBeVisible();
  await expect(page.getByText('Fictional Thoroughbred Park')).toBeVisible();
  await expect(page.getByText('Fictional Harness Circuit')).toBeVisible();
  await expect(page.getByText('Fictional Greyhound Track')).toBeVisible();

  await page.getByRole('button', { name: 'Open research view' }).first().click();
  await expect(page.getByRole('region', { name: 'Race research view' })).toBeVisible();
  await expect(page.getByText('field-r2', { exact: true })).toBeVisible();
  await expect(page.getByRole('table')).toBeVisible();
  await expect(page.getByText('SCRATCHED')).toBeVisible();
  await page.getByRole('tab', { name: 'Forecast archive' }).click();
  await expect(page.getByText('INVALIDATED BY FIELD REVISION')).toBeVisible();
  await page.getByRole('tab', { name: 'Provenance' }).click();
  await expect(page.getByText('Receipt verified')).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/ril-018/race-research-view.png', fullPage: true });
  await page.getByRole('button', { name: 'Close view' }).click();

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
