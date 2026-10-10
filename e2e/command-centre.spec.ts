import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('command centre filters codes and distinguishes data states', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today / Command Centre' })).toBeVisible();
  await expect(page.getByText('DEMO ONLY')).toBeVisible();
  await expect(page.locator('header').getByText('SYNTHETIC_ONLY')).toBeVisible();
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

test('research workbench compares B0 to B4 and exposes synthetic evaluation evidence', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open research view' }).first().click();
  await page.getByRole('tab', { name: 'Forecast archive' }).click();

  const workbench = page.getByRole('tabpanel', { name: 'Forecast comparison workbench' });
  await expect(workbench.getByRole('heading', { name: 'Winning-probability assessments' })).toBeVisible();
  await expect(workbench.getByText('B0 · Uniform')).toBeVisible();
  await expect(workbench.getByText('B3 · LightGBM')).toBeVisible();
  await expect(workbench.getByText('B4 · Combined')).toBeVisible();
  await expect(workbench.getByText('Model disagreement:', { exact: false }).first()).toBeVisible();
  await expect(workbench.getByRole('heading', { name: 'Walk-forward evaluation' })).toBeVisible();
  await expect(workbench.getByText('Feature-family ablation')).toBeVisible();
  await expect(workbench.getByRole('heading', { name: 'Feature availability and provenance' })).toBeVisible();
  await expect(workbench.getByText('Starting price / post-race result')).toBeVisible();
  await expect(workbench.getByText('Never eligible for pre-race forecasts')).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/ril-061/research-workbench.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: 'docs/evidence/ril-061/research-workbench-mobile.png', fullPage: true });
});

test('bounded assistant cites evidence, explains discrepancies and requires note approval', async ({ page }) => {
  await page.goto('/');
  const assistant = page.getByRole('region', { name: 'Ask an evidence-grounded question.' });
  await expect(assistant).toBeVisible();
  await expect(assistant.getByText('Source ID', { exact: true })).toBeVisible();
  await expect(assistant.getByText('SYNTHETIC_ONLY', { exact: true })).toBeVisible();

  await assistant.getByRole('button', { name: 'Explain discrepancy' }).click();
  await expect(assistant.getByText('The forecast and field use different revisions.')).toBeVisible();
  await expect(assistant.locator('p').filter({ hasText: 'field-r1' })).toBeVisible();
  await expect(assistant.locator('p').filter({ hasText: 'no replacement probability was estimated' })).toBeVisible();

  const saveNote = assistant.getByRole('button', { name: 'Save approved note' });
  await expect(saveNote).toBeDisabled();
  await assistant.getByRole('checkbox', { name: /I approve saving/ }).check();
  await expect(saveNote).toBeEnabled();
  await saveNote.click();
  await expect(assistant.getByRole('status')).toContainText('Saved locally');

  await assistant.getByRole('button', { name: 'Ask for missing value' }).click();
  await expect(assistant.getByText('NOT_AVAILABLE · verified specialty evidence is absent.')).toBeVisible();
  await expect(assistant.getByText('will not estimate a current value')).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/ril-049/assistant-citations.png', fullPage: true });
});
