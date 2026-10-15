import { expect, test } from '@playwright/test';

const workspaces = [
  { label: 'Meetings', file: 'meetings' },
  { label: 'Tactical', file: 'tactical' },
  { label: 'Runner', file: 'runner' },
  { label: 'Compare', file: 'compare' },
  { label: 'Models', file: 'models' },
  { label: 'Markets', file: 'markets' },
  { label: 'Evidence', file: 'evidence' },
  { label: 'Assistant', file: 'assistant' },
  { label: 'Notebook', file: 'notebook' },
  { label: 'Watchlists', file: 'watchlists' },
  { label: 'Alerts', file: 'alerts' },
  { label: 'Reports', file: 'reports' },
  { label: 'Settings', file: 'settings' },
];

test.setTimeout(300000);

test('V7 visual surfaces are individually authored and responsive', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today / Command Centre' })).toBeVisible();
  await expect(page.getByText('OWNER ANALYSIS LAB')).toBeVisible();
  await expect(page.getByText('Full V7 visual test environment')).toBeVisible();
  await expect(page.getByRole('region', { name: 'Synthetic command centre visual summary' })).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/v7-implementation/command-centre-1440.png', fullPage: true });

  for (const workspace of workspaces) {
    await page.getByRole('navigation', { name: 'Research workspaces' }).getByRole('button', { name: new RegExp(`^${workspace.label}`) }).click();
    await expect(page.getByRole('region', { name: /workspace$/ })).toBeVisible();
    await expect(page.getByText('WORKSPACE ATLAS · SYNTHETIC DEMO')).toBeVisible();
      if (workspace.label === 'Tactical') {
      await expect(page.getByRole('region', { name: 'Tactical Track V7 visual surface' })).toBeVisible();
      await expect(page.locator('.tactical-runner')).toHaveCount(11);
      await page.getByLabel('Synthetic field size').selectOption('6');
      await expect(page.locator('.tactical-runner')).toHaveCount(6);
      await expect(page.getByText('6 runners · layout adapts to the race field')).toBeVisible();
      await page.screenshot({ path: 'docs/evidence/v7-implementation/tactical-6-1440.png', fullPage: true });
      await page.getByLabel('Synthetic field size').selectOption('14');
      await expect(page.locator('.tactical-runner')).toHaveCount(14);
      await page.screenshot({ path: 'docs/evidence/v7-implementation/tactical-14-1440.png', fullPage: true });
      await page.getByLabel('Synthetic field size').selectOption('11');
      await expect(page.locator('.tactical-runner')).toHaveCount(11);
      await page.getByRole('button', { name: 'Contested lead' }).click();
      await expect(page.getByText('Position is contextual, not predictive.')).toBeVisible();
      await page.getByRole('button', { name: 'Select runner 5 Desert King' }).click();
      await expect(page.getByRole('button', { name: 'Select runner 5 Desert King' }).first()).toHaveClass(/selected/);
        await expect(page.getByText('Desert King', { exact: true }).first()).toBeVisible();
      }
      if (workspace.label === 'Evidence') {
        const evidence = page.locator('.evidence-atlas-preview');
        await evidence.locator('.surface-primary-action').click();
        await expect(evidence.locator('.surface-action-feedback')).toContainText('Receipt ledger opened · synthetic preview only');
        await evidence.getByLabel('Dismiss evidence action feedback').click();
        await evidence.locator('.surface-tabs button').nth(1).click();
        await expect(evidence.locator('.surface-tabs button').nth(1)).toHaveAttribute('aria-selected', 'true');
      }
      if (workspace.label === 'Alerts') {
        const alerts = page.locator('.alerts-workspace');
        await alerts.locator('.surface-primary-action').click();
        await expect(alerts.locator('.surface-action-feedback')).toContainText('New alert flow opened · local preview only');
        await alerts.getByLabel('Dismiss alert action feedback').click();
        await alerts.locator('.alert-toggle').first().click();
        await expect(alerts.locator('.alert-toggle').first()).toHaveAttribute('aria-pressed', 'false');
      }
      if (workspace.label === 'Settings') {
        const settings = page.locator('.settings-workspace');
        await settings.locator('.surface-primary-action').click();
        await expect(settings.locator('.surface-action-feedback')).toContainText('Assurance review opened · local preview only');
        await settings.getByLabel('Dismiss settings action feedback').click();
        await settings.locator('.preference-row').first().click();
        await expect(settings.locator('.preference-row').first()).toHaveAttribute('aria-pressed', 'true');
      }
      if (workspace.label === 'Markets') {
        const markets = page.locator('.markets-room');
        await markets.locator('.surface-primary-action').click();
        await expect(markets.locator('.surface-action-feedback')).toContainText('Market analysis opened · paper preview only');
        await markets.getByLabel('Dismiss market action feedback').click();
        await markets.locator('.surface-tabs button').nth(1).click();
        await expect(markets.locator('.surface-tabs button').nth(1)).toHaveAttribute('aria-selected', 'true');
      }
      if (workspace.label === 'Assistant') {
        const assistant = page.locator('.assistant-room');
        await assistant.locator('.surface-primary-action').click();
        await expect(assistant.getByText('NOT_AVAILABLE', { exact: false }).first()).toBeVisible();
        await assistant.getByLabel('Ask a bounded question').fill('What evidence supports this race?');
        await assistant.getByLabel('Submit assistant question').click();
        await expect(assistant.getByText('Evidence is available for the synthetic field record.', { exact: true })).toBeVisible();
      }
      if (workspace.label === 'Notebook') {
        const notebook = page.locator('.notebook-room');
        await notebook.getByRole('button', { name: 'New note' }).click();
        await notebook.locator('.notebook-note-list button').nth(1).click();
        await expect(notebook.locator('.notebook-note-list button').nth(1)).toHaveClass(/selected/);
      }
      if (!['Tactical', 'Evidence', 'Alerts', 'Settings', 'Markets', 'Assistant', 'Notebook'].includes(workspace.label)) {
        const surface = page.locator('.cinematic-surface');
        await surface.locator('.surface-primary-action').click();
        await expect(surface.locator('.surface-action-feedback')).toContainText('opened · synthetic preview only');
        await surface.getByLabel('Dismiss action feedback').click();
        await surface.locator('.surface-tabs button').nth(1).click();
        await expect(surface.locator('.surface-tabs button').nth(1)).toHaveAttribute('aria-selected', 'true');
      }
      await page.screenshot({ path: `docs/evidence/v7-implementation/${workspace.file}-1440.png`, fullPage: true });
  }

  for (const viewport of [{ width: 768, height: 1024, name: '768' }, { width: 390, height: 844, name: '390' }]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/');
    await expect(page.getByText('OWNER ANALYSIS LAB')).toBeVisible();
    await expect(page.getByRole('region', { name: 'Synthetic command centre visual summary' })).toBeVisible();
    await page.screenshot({ path: `docs/evidence/v7-implementation/command-centre-${viewport.name}.png`, fullPage: true });
    for (const workspace of workspaces) {
      await page.getByRole('navigation', { name: 'Research workspaces' }).getByRole('button', { name: new RegExp(`^${workspace.label}`) }).click();
      await expect(page.getByRole('region', { name: /workspace$/ })).toBeVisible();
      await expect(page.getByText('WORKSPACE ATLAS · SYNTHETIC DEMO')).toBeVisible();
      if (workspace.label === 'Tactical') await expect(page.locator('.tactical-runner')).toHaveCount(11);
      await page.screenshot({ path: `docs/evidence/v7-implementation/${workspace.file}-${viewport.name}.png`, fullPage: true });
    }
  }
});
