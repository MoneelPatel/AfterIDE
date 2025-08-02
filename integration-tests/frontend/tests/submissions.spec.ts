import { test, expect, Page } from '@playwright/test';

/**
 * AfterIDE - Submission E2E Tests
 * 
 * End-to-end tests for the submission system, testing the complete workflow
 * from submission creation to review and management.
 */

test.describe('Submission System', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test('should create a new submission successfully', async () => {
    // Login first (assuming we have a test user)
    await loginAsTestUser(page);
    
    // Navigate to a file or create one to submit
    await createTestFile(page);
    
    // Open submission form
    await openSubmissionForm(page);
    
    // Fill out submission form
    await fillSubmissionForm(page, {
      title: 'Test Submission',
      description: 'This is a test submission for E2E testing',
      reviewer: 'reviewer' // if available
    });
    
    // Submit the form
    await submitSubmissionForm(page);
    
    // Verify submission was created successfully
    await expect(page.locator('[data-testid="submission-success"]')).toBeVisible();
    
    // Verify submission appears in the list
    await navigateToSubmissionsList(page);
    await expect(page.locator('text=Test Submission')).toBeVisible();
  });

  test('should display submission form with file information', async () => {
    await loginAsTestUser(page);
    await createTestFile(page);
    
    // Open submission form
    await openSubmissionForm(page);
    
    // Verify form elements are present
    await expect(page.locator('input[name="title"]')).toBeVisible();
    await expect(page.locator('textarea[name="description"]')).toBeVisible();
    await expect(page.locator('input[name="reviewer"]')).toBeVisible();
    
    // Verify file information is displayed
    await expect(page.locator('[data-testid="file-info"]')).toBeVisible();
  });

  test('should validate submission form fields', async () => {
    await loginAsTestUser(page);
    await createTestFile(page);
    
    // Open submission form
    await openSubmissionForm(page);
    
    // Try to submit without title
    await page.locator('textarea[name="description"]').fill('Test description');
    await page.locator('button[type="submit"]').click();
    
    // Should show validation error
    await expect(page.locator('[data-testid="title-error"]')).toBeVisible();
    
    // Fill title and submit
    await page.locator('input[name="title"]').fill('Valid Title');
    await page.locator('button[type="submit"]').click();
    
    // Should not show validation error
    await expect(page.locator('[data-testid="title-error"]')).not.toBeVisible();
  });

  test('should display available reviewers in dropdown', async () => {
    await loginAsTestUser(page);
    await createTestFile(page);
    
    // Open submission form
    await openSubmissionForm(page);
    
    // Click on reviewer field to open dropdown
    await page.locator('input[name="reviewer"]').click();
    
    // Wait for dropdown to appear
    await page.waitForSelector('[data-testid="reviewer-dropdown"]');
    
    // Verify reviewers are listed
    await expect(page.locator('[data-testid="reviewer-dropdown"]')).toBeVisible();
    
    // Select a reviewer
    await page.locator('[data-testid="reviewer-option"]').first().click();
    
    // Verify reviewer is selected
    await expect(page.locator('input[name="reviewer"]')).toHaveValue(/reviewer/);
  });

  test('should display submission list with pagination', async () => {
    await loginAsTestUser(page);
    
    // Navigate to submissions list
    await navigateToSubmissionsList(page);
    
    // Verify submissions list is displayed
    await expect(page.locator('[data-testid="submissions-list"]')).toBeVisible();
    
    // Verify pagination controls are present
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    
    // Verify submission cards are displayed
    await expect(page.locator('[data-testid="submission-card"]')).toBeVisible();
  });

  test('should filter submissions by status', async () => {
    await loginAsTestUser(page);
    await navigateToSubmissionsList(page);
    
    // Click on status filter
    await page.locator('[data-testid="status-filter"]').click();
    
    // Select pending status
    await page.locator('text=Pending').click();
    
    // Verify only pending submissions are shown
    const submissionCards = page.locator('[data-testid="submission-card"]');
    const count = await submissionCards.count();
    
    for (let i = 0; i < count; i++) {
      await expect(submissionCards.nth(i).locator('[data-testid="status-badge"]')).toHaveText('Pending');
    }
  });

  test('should display submission details', async () => {
    await loginAsTestUser(page);
    await navigateToSubmissionsList(page);
    
    // Click on a submission to view details
    await page.locator('[data-testid="submission-card"]').first().click();
    
    // Verify submission details are displayed
    await expect(page.locator('[data-testid="submission-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="submission-description"]')).toBeVisible();
    await expect(page.locator('[data-testid="submission-file"]')).toBeVisible();
    await expect(page.locator('[data-testid="submission-status"]')).toBeVisible();
  });

  test('should allow editing submission', async () => {
    await loginAsTestUser(page);
    await navigateToSubmissionsList(page);
    
    // Click on a submission to view details
    await page.locator('[data-testid="submission-card"]').first().click();
    
    // Click edit button
    await page.locator('[data-testid="edit-submission"]').click();
    
    // Update submission
    await page.locator('input[name="title"]').fill('Updated Title');
    await page.locator('textarea[name="description"]').fill('Updated description');
    
    // Save changes
    await page.locator('button[type="submit"]').click();
    
    // Verify changes are saved
    await expect(page.locator('[data-testid="submission-title"]')).toHaveText('Updated Title');
  });

  test('should allow deleting submission', async () => {
    await loginAsTestUser(page);
    await navigateToSubmissionsList(page);
    
    // Get initial count
    const initialCount = await page.locator('[data-testid="submission-card"]').count();
    
    // Click on a submission to view details
    await page.locator('[data-testid="submission-card"]').first().click();
    
    // Click delete button
    await page.locator('[data-testid="delete-submission"]').click();
    
    // Confirm deletion
    await page.locator('[data-testid="confirm-delete"]').click();
    
    // Verify submission is deleted
    await navigateToSubmissionsList(page);
    const finalCount = await page.locator('[data-testid="submission-card"]').count();
    expect(finalCount).toBe(initialCount - 1);
  });

  test('should display submission statistics', async () => {
    await loginAsTestUser(page);
    await navigateToSubmissionsList(page);
    
    // Verify stats are displayed
    await expect(page.locator('[data-testid="total-submissions"]')).toBeVisible();
    await expect(page.locator('[data-testid="pending-submissions"]')).toBeVisible();
    await expect(page.locator('[data-testid="approved-submissions"]')).toBeVisible();
    await expect(page.locator('[data-testid="rejected-submissions"]')).toBeVisible();
  });

  test('should handle API errors gracefully', async () => {
    await loginAsTestUser(page);
    await createTestFile(page);
    
    // Open submission form
    await openSubmissionForm(page);
    
    // Fill form with invalid data to trigger error
    await page.locator('input[name="title"]').fill('Test');
    await page.locator('input[name="file_id"]').fill('invalid-uuid');
    
    // Submit form
    await page.locator('button[type="submit"]').click();
    
    // Verify error message is displayed
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test('should use HTTPS for all API requests', async () => {
    // This test verifies that no HTTP requests are made
    await loginAsTestUser(page);
    
    // Listen for network requests
    const httpRequests: string[] = [];
    page.on('request', request => {
      if (request.url().startsWith('http://')) {
        httpRequests.push(request.url());
      }
    });
    
    // Navigate to submissions list (this will trigger API requests)
    await navigateToSubmissionsList(page);
    
    // Wait for network requests to complete
    await page.waitForLoadState('networkidle');
    
    // Verify no HTTP requests were made
    expect(httpRequests.length).toBe(0);
  });

  test('should handle authentication errors', async () => {
    // Clear authentication
    await page.evaluate(() => {
      localStorage.removeItem('authToken');
    });
    
    // Try to access submissions list
    await navigateToSubmissionsList(page);
    
    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);
  });
});

// Helper functions
async function loginAsTestUser(page: Page) {
  // Navigate to login page
  await page.goto('/login');
  
  // Fill login form
  await page.locator('input[name="username"]').fill('testuser');
  await page.locator('input[name="password"]').fill('testpassword123');
  
  // Submit form
  await page.locator('button[type="submit"]').click();
  
  // Wait for login to complete
  await page.waitForURL('**/dashboard**');
}

async function createTestFile(page: Page) {
  // Navigate to editor or create a new file
  await page.goto('/editor');
  
  // Create a simple test file
  await page.locator('[data-testid="new-file"]').click();
  await page.locator('input[name="filename"]').fill('test_file.py');
  await page.locator('textarea[name="content"]').fill('print("Hello, World!")');
  await page.locator('button[type="submit"]').click();
  
  // Wait for file to be created
  await page.waitForSelector('[data-testid="file-created"]');
}

async function openSubmissionForm(page: Page) {
  // Click on submit button or context menu
  await page.locator('[data-testid="submit-file"]').click();
  
  // Wait for form to appear
  await page.waitForSelector('[data-testid="submission-form"]');
}

async function fillSubmissionForm(page: Page, data: { title: string; description: string; reviewer?: string }) {
  await page.locator('input[name="title"]').fill(data.title);
  await page.locator('textarea[name="description"]').fill(data.description);
  
  if (data.reviewer) {
    await page.locator('input[name="reviewer"]').click();
    await page.locator(`[data-testid="reviewer-option"]:has-text("${data.reviewer}")`).click();
  }
}

async function submitSubmissionForm(page: Page) {
  await page.locator('button[type="submit"]').click();
  
  // Wait for submission to complete
  await page.waitForSelector('[data-testid="submission-success"]');
}

async function navigateToSubmissionsList(page: Page) {
  // Navigate to submissions page
  await page.goto('/submissions');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
} 