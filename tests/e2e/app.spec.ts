import { test, expect } from '@playwright/test';

// Basic unauthenticated flow

test('shows login screen when not authenticated', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: /sign in with auth0/i })).toBeVisible();
});

// Authenticated dashboard flow with mocked API

test('allows creating a new job', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('websets_token', 'test-token');
    localStorage.setItem('websets_refresh_token', 'refresh');
  });

  await page.route('**/auth/me', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: '1', email: 'test@example.com', full_name: 'Test User', is_active: true }),
    });
  });

  let jobs: any[] = [];
  await page.route('**/jobs/', async route => {
    const { method } = route.request();
    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(jobs),
      });
    } else if (method === 'POST') {
      const body = await route.request().postDataJSON();
      const job = {
        id: 'j1',
        prompt: body.prompt,
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: '1',
      };
      jobs.push(job);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(job),
      });
    }
  });

  await page.goto('/');
  await expect(page.getByText(/welcome, test user/i)).toBeVisible();

  await page.getByRole('button', { name: /new job/i }).click();
  await page.fill('textarea#prompt', 'Test job');
  await page.getByRole('button', { name: /start mining/i }).click();

  await expect(page.getByText('Test job')).toBeVisible();
});
