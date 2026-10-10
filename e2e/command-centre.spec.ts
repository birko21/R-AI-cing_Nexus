import AxeBuilder from '@axe-core/playwright';
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
  await expect(page.getByRole('table', { name: 'Fictional entries and field state' })).toBeVisible();
  await expect(page.getByText('SCRATCHED', { exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Runner compare' })).toBeVisible();
  await expect(page.getByText('Compare 2 runners')).toBeVisible();
  await page.getByRole('checkbox', { name: /Runner 4/ }).check();
  await expect(page.getByText('Compare 3 runners')).toBeVisible();
  await expect(page.getByText('Thoroughbred panel · pace and class')).toBeVisible();
  await expect(page.getByText('No value is invented for the comparison.')).toBeVisible();
  await page.getByRole('tab', { name: 'Forecast archive' }).click();
  await expect(page.getByText('INVALIDATED BY FIELD REVISION')).toBeVisible();
  await page.getByRole('tab', { name: 'Provenance' }).click();
  await expect(page.getByText('Receipt verified')).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/ril-018/race-research-view.png', fullPage: true });
  await page.getByRole('button', { name: 'Close view' }).click();

  await page.getByRole('button', { name: 'Greyhound', exact: true }).click();
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

test('code-specific research panels explain missing specialty inputs', async ({ page }) => {
  const panels = [
    { code: 'Thoroughbred', title: 'Thoroughbred panel · pace and class', file: 'thoroughbred-panel.png' },
    { code: 'Harness', title: 'Harness panel · gait and sectionals', file: 'harness-panel.png' },
    { code: 'Greyhound', title: 'Greyhound panel · box and interference', file: 'greyhound-panel.png' },
  ];

  for (const panel of panels) {
    await page.goto('/');
    await page.getByRole('button', { name: panel.code, exact: true }).click();
    await page.getByRole('button', { name: /Open research view/ }).click();
    const researchView = page.getByRole('region', { name: 'Race research view' });
    await expect(researchView.getByText(panel.title)).toBeVisible();
    await expect(researchView.getByText('No value is invented for the comparison.')).toBeVisible();
    await page.screenshot({ path: `docs/evidence/ril-019/${panel.file}`, fullPage: true });
  }
});

test('degraded states and accessible controls remain explicit at desktop and mobile sizes', async ({ page }) => {
  await page.goto('/');
  for (const state of ['Loading', 'Stale snapshot', 'Quarantined', 'Unsupported', 'Auth denied']) {
    await expect(page.getByRole('article', { name: new RegExp(`· ${state}$`) })).toBeVisible();
  }
  await expect(page.getByText('No partial values are displayed.', { exact: false })).toBeVisible();
  await expect(page.getByText('No value is inferred', { exact: false })).not.toBeVisible();

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations).toEqual([]);

  const allCodes = page.getByRole('button', { name: 'All codes', exact: true });
  await allCodes.focus();
  await expect(allCodes).toBeFocused();
  await expect(allCodes).toHaveAttribute('aria-pressed', 'true');
  await page.getByLabel('Data state').selectOption('AUTH_DENIED');
  await expect(page.getByRole('region', { name: 'Today command cards' }).getByText('Auth denied', { exact: true })).toBeVisible();

  await page.screenshot({ path: 'docs/evidence/ril-020/degraded-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'docs/evidence/ril-020/degraded-mobile.png', fullPage: true });
});

test('market workbench shows provenance and suppresses restricted exports', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open research view' }).first().click();
  await page.getByRole('tab', { name: 'Market workbench' }).click();

  const workbench = page.getByRole('tabpanel', { name: 'Market workbench' });
  await expect(workbench.getByText('synthetic-fixture')).toBeVisible();
  await expect(workbench.getByText('AVAILABLE · 5 min')).toBeVisible();
  await expect(workbench.getByText('1.1250')).toBeVisible();
  await expect(workbench.getByText('NOT_COMPARABLE', { exact: true })).toBeVisible();
  await expect(workbench.getByText('SUPPRESSED · RESTRICTED')).toBeVisible();
  await expect(workbench.getByRole('button', { name: 'Export restricted prices' })).toBeDisabled();
  await page.screenshot({ path: 'docs/evidence/ril-040/market-workbench.png', fullPage: true });
});
