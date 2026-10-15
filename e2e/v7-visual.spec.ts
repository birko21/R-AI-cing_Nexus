import { expect, test } from '@playwright/test';

const workspaces = [
  { label: 'Meetings', file: 'meetings' },
  { label: 'Race', file: 'race' },
  { label: 'Tactical', file: 'tactical' },
  { label: 'Runner', file: 'runner' },
  { label: 'Compare', file: 'compare' },
  { label: 'Models', file: 'models' },
  { label: 'Scenarios', file: 'scenarios' },
  { label: 'Markets', file: 'markets' },
  { label: 'Evidence', file: 'evidence' },
  { label: 'Assistant', file: 'assistant' },
  { label: 'Notebook', file: 'notebook' },
  { label: 'Watchlists', file: 'watchlists' },
  { label: 'Reports', file: 'reports' },
];

test.setTimeout(300000);

test('V7 visual surfaces are individually authored and responsive', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today / Command Centre' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Synthetic command centre visual summary' })).toBeVisible();
  await page.screenshot({ path: 'docs/evidence/v7-implementation/command-centre-1440.png', fullPage: true });

  for (const workspace of workspaces) {
    await page.getByRole('navigation', { name: 'Research workspaces' }).getByRole('button', { name: new RegExp(`^${workspace.label}`) }).click();
    await expect(page.getByRole('region', { name: /workspace$/ })).toBeVisible();
    await expect(page.getByText('Research preview · synthetic only.')).toBeVisible();
    if (workspace.label === 'Tactical') {
      await expect(page.getByRole('region', { name: 'Tactical Track V7 visual surface' })).toBeVisible();
      await expect(page.locator('.tactical-runner')).toHaveCount(11);
      await page.getByRole('button', { name: 'Contested lead' }).click();
      await expect(page.getByText('Position is contextual, not predictive.')).toBeVisible();
      await page.getByRole('button', { name: 'Select runner 5 Desert King' }).click();
      await expect(page.getByRole('button', { name: 'Select runner 5 Desert King' }).first()).toHaveClass(/selected/);
      await expect(page.getByText('Desert King', { exact: true }).first()).toBeVisible();
    }
    await page.screenshot({ path: `docs/evidence/v7-implementation/${workspace.file}-1440.png`, fullPage: true });
  }

  for (const viewport of [{ width: 768, height: 1024, name: '768' }, { width: 390, height: 844, name: '390' }]) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto('/');
    await expect(page.getByRole('region', { name: 'Synthetic command centre visual summary' })).toBeVisible();
    await page.screenshot({ path: `docs/evidence/v7-implementation/command-centre-${viewport.name}.png`, fullPage: true });
    for (const workspace of workspaces) {
      await page.getByRole('navigation', { name: 'Research workspaces' }).getByRole('button', { name: new RegExp(`^${workspace.label}`) }).click();
      await expect(page.getByRole('region', { name: /workspace$/ })).toBeVisible();
      await expect(page.getByText('Research preview · synthetic only.')).toBeVisible();
      if (workspace.label === 'Tactical') await expect(page.locator('.tactical-runner')).toHaveCount(11);
      await page.screenshot({ path: `docs/evidence/v7-implementation/${workspace.file}-${viewport.name}.png`, fullPage: true });
    }
  }
});
