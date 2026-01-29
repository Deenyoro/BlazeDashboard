import { chromium } from 'playwright';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, '../../.env') });

const CONFIG = {
  BLAZE_URL: 'https://retail.blaze.me',
  BLAZE_EMAIL: process.env.BLAZE_EMAIL || '',
  BLAZE_PASSWORD: process.env.BLAZE_PASSWORD || '',
  EXPORT_DIR: process.env.EXPORT_DIR || path.join(__dirname, '../../exports'),
  HEADLESS: process.env.HEADLESS !== 'false',
  TIMEOUT: 60000,
  API_URL: process.env.API_URL || 'http://api:8000',
  // Historical start date for full backfill
  HISTORICAL_START_DATE: '2025-04-01',
};

// All available Blaze reports - discovered via 'discover' mode
// The 'tab' field specifies which tab to click first before finding the report
const REPORTS = {
  // Main transaction data - Total Sales Report under Sales tab (modal-based export)
  all_sales: {
    name: 'Total Sales Report',
    tab: 'Sales',
    filename: 'all_sales.csv',
    endpoint: '/api/v1/ingest/csv',
    type: 'transactions',
  },
  // Product-level sales - under Sales tab
  sales_by_product: {
    name: 'Sales by Product Report',
    tab: 'Sales',
    filename: 'sales_by_product.csv',
    endpoint: '/api/v1/ingest/products',
    type: 'products',
  },
  // Category-level sales - under Sales tab
  sales_by_category: {
    name: 'Sales by Product Category Report',
    tab: 'Sales',
    filename: 'sales_by_category.csv',
    endpoint: '/api/v1/ingest/categories',
    type: 'categories',
  },
  // Hourly sales breakdown - under Sales tab
  sales_by_hour: {
    name: 'Sales by Hour Report',
    tab: 'Sales',
    filename: 'sales_by_hour.csv',
    endpoint: '/api/v1/ingest/hourly',
    type: 'hourly',
  },
  // Discount/promotion usage - under Marketing tab
  promotions: {
    name: 'Promotions Used Report',
    tab: 'Manager',
    filename: 'promotions_used.csv',
    endpoint: '/api/v1/ingest/discounts',
    type: 'discounts',
  },
  // Inventory valuation - under Inventory tab
  inventory: {
    name: 'Inventory Valuation By Category Report',
    tab: 'Inventory',
    filename: 'inventory_valuation.csv',
    endpoint: '/api/v1/ingest/inventory',
    type: 'inventory',
  },
  // Refund details - under Sales tab
  refunds: {
    name: 'Refund History Report',
    tab: 'Sales',
    filename: 'refund_history.csv',
    endpoint: '/api/v1/ingest/refunds',
    type: 'refunds',
  },
  // Employee performance - under Frequently used or Manager tab
  employee_sales: {
    name: 'Employee By Sales By Product Report',
    tab: 'Frequently used',
    filename: 'employee_sales.csv',
    endpoint: '/api/v1/ingest/employee-sales',
    type: 'employee_sales',
  },
  // Delivery sales - under Sales tab
  delivery_sales: {
    name: 'Delivery Sales Report',
    tab: 'Sales',
    filename: 'delivery_sales.csv',
    endpoint: '/api/v1/ingest/delivery',
    type: 'delivery',
  },
};

/**
 * Get the last transaction date from the API to enable incremental scraping
 */
async function getLastTransactionDate() {
  try {
    const response = await fetch(`${CONFIG.API_URL}/api/v1/ingest/last-date`);
    if (response.ok) {
      const data = await response.json();
      return data.last_transaction_date_formatted;
    }
  } catch (error) {
    console.log('Could not fetch last transaction date from API:', error.message);
  }
  return null;
}

/**
 * Trigger ingestion via API after scraping
 */
async function triggerIngestion(reportKey) {
  const report = REPORTS[reportKey];
  if (!report) return null;

  try {
    console.log(`\nTriggering ingestion for ${report.name}...`);
    const endpoint = report.endpoint + (reportKey === 'all_sales' ? '?use_default=true' : '');
    const response = await fetch(`${CONFIG.API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: report.filename }),
    });
    if (response.ok) {
      const data = await response.json();
      console.log('Ingestion result:', JSON.stringify(data, null, 2));
      return data;
    } else {
      console.error('Ingestion failed:', response.status, await response.text());
    }
  } catch (error) {
    console.error('Could not trigger ingestion:', error.message);
  }
  return null;
}

/**
 * Validate data integrity after ingestion
 */
async function validateData() {
  try {
    console.log('\nValidating data integrity...');
    const response = await fetch(`${CONFIG.API_URL}/api/v1/ingest/validate`);
    if (response.ok) {
      const data = await response.json();
      console.log('Validation result:', JSON.stringify(data, null, 2));

      if (data.data_integrity === 'FAIL') {
        console.error('WARNING: Duplicate transactions detected!');
        console.error('Duplicate IDs:', data.duplicates.duplicate_ids);
        return false;
      }
      console.log('Data integrity check: PASSED');
      return true;
    }
  } catch (error) {
    console.error('Could not validate data:', error.message);
  }
  return false;
}

async function login(page) {
  console.log('Navigating to Blaze login...');
  await page.goto(CONFIG.BLAZE_URL, { waitUntil: 'networkidle', timeout: CONFIG.TIMEOUT });

  // Wait for login form
  await page.waitForSelector('input[type="email"], input[name="email"], input[placeholder*="email" i]', {
    timeout: CONFIG.TIMEOUT
  });

  console.log('Entering credentials...');

  // Try different selectors for email field
  const emailSelectors = [
    'input[type="email"]',
    'input[name="email"]',
    'input[placeholder*="email" i]',
    'input[id*="email" i]',
  ];

  for (const selector of emailSelectors) {
    try {
      const emailInput = await page.$(selector);
      if (emailInput) {
        await emailInput.fill(CONFIG.BLAZE_EMAIL);
        break;
      }
    } catch (e) {
      continue;
    }
  }

  // Try different selectors for password field
  const passwordSelectors = [
    'input[type="password"]',
    'input[name="password"]',
    'input[placeholder*="password" i]',
  ];

  for (const selector of passwordSelectors) {
    try {
      const passwordInput = await page.$(selector);
      if (passwordInput) {
        await passwordInput.fill(CONFIG.BLAZE_PASSWORD);
        break;
      }
    } catch (e) {
      continue;
    }
  }

  // Click login button
  const loginSelectors = [
    'button[type="submit"]',
    'button:has-text("Log in")',
    'button:has-text("Login")',
    'button:has-text("Sign in")',
    'input[type="submit"]',
  ];

  for (const selector of loginSelectors) {
    try {
      const loginBtn = await page.$(selector);
      if (loginBtn) {
        await loginBtn.click();
        break;
      }
    } catch (e) {
      continue;
    }
  }

  // Wait for navigation after login
  console.log('Waiting for login to complete...');
  await page.waitForURL('**/dashboard**', { timeout: CONFIG.TIMEOUT }).catch(() => {
    // Sometimes the URL pattern is different
  });

  // Wait for the app to load
  await page.waitForTimeout(3000);
  console.log('Login successful!');
}

/**
 * List all available reports on the reports page
 */
async function listAvailableReports(page) {
  console.log('\nNavigating to reports page to discover available reports...');
  await page.goto(`${CONFIG.BLAZE_URL}/reports`, { waitUntil: 'networkidle', timeout: CONFIG.TIMEOUT });
  await page.waitForTimeout(2000);

  // Get all report links/buttons
  const reports = await page.evaluate(() => {
    const reportElements = document.querySelectorAll('a[href*="report"], button[class*="report"], .report-item, .report-link, [data-report]');
    const reportNames = [];

    reportElements.forEach(el => {
      const text = el.innerText || el.textContent;
      if (text && text.trim()) {
        reportNames.push(text.trim());
      }
    });

    // Also try to get text from all clickable items in the reports section
    const allLinks = document.querySelectorAll('.reports a, .reports button, [class*="report"] a');
    allLinks.forEach(el => {
      const text = el.innerText || el.textContent;
      if (text && text.trim() && !reportNames.includes(text.trim())) {
        reportNames.push(text.trim());
      }
    });

    return reportNames;
  });

  console.log('\nDiscovered report options:');
  reports.forEach((r, i) => console.log(`  ${i + 1}. ${r}`));

  return reports;
}

async function exportReport(page, reportKey, startDate, endDate) {
  const report = REPORTS[reportKey];
  if (!report) {
    throw new Error(`Unknown report: ${reportKey}`);
  }

  console.log(`\nExporting: ${report.name}`);
  console.log(`Date range: ${startDate} to ${endDate}`);

  // Navigate to reports
  console.log('Navigating to reports...');
  await page.goto(`${CONFIG.BLAZE_URL}/reports`, { waitUntil: 'networkidle', timeout: CONFIG.TIMEOUT });
  await page.waitForTimeout(2000);

  // Click on the appropriate tab first if specified
  if (report.tab) {
    console.log(`Clicking on "${report.tab}" tab...`);
    let tabClicked = false;

    // Strategy 1: Click tab by exact text in navigation area
    try {
      const tabSelector = `div.nav-tabs a:has-text("${report.tab}"), ul.nav-tabs li:has-text("${report.tab}"), .tab:has-text("${report.tab}"), [role="tab"]:has-text("${report.tab}")`;
      await page.click(tabSelector, { timeout: 3000 });
      tabClicked = true;
      console.log(`Switched to "${report.tab}" tab (strategy 1)`);
    } catch (e) {
      console.log('Tab strategy 1 failed...');
    }

    // Strategy 2: Use getByRole for tab
    if (!tabClicked) {
      try {
        await page.getByRole('tab', { name: report.tab }).click({ timeout: 3000 });
        tabClicked = true;
        console.log(`Switched to "${report.tab}" tab (strategy 2)`);
      } catch (e) {
        console.log('Tab strategy 2 failed...');
      }
    }

    // Strategy 3: Find any clickable element with exact tab text
    if (!tabClicked) {
      try {
        await page.locator(`text="${report.tab}"`).first().click({ timeout: 3000 });
        tabClicked = true;
        console.log(`Switched to "${report.tab}" tab (strategy 3)`);
      } catch (e) {
        console.log('Tab strategy 3 failed...');
      }
    }

    // Strategy 4: Use evaluate to find and click tab
    if (!tabClicked) {
      try {
        const clicked = await page.evaluate((tabName) => {
          // Look for tab elements
          const elements = document.querySelectorAll('a, button, div, span, li');
          for (const el of elements) {
            if (el.textContent && el.textContent.trim() === tabName) {
              el.click();
              return true;
            }
          }
          return false;
        }, report.tab);
        if (clicked) {
          tabClicked = true;
          console.log(`Switched to "${report.tab}" tab (strategy 4)`);
        }
      } catch (e) {
        console.log('Tab strategy 4 failed...');
      }
    }

    if (tabClicked) {
      await page.waitForTimeout(1500);
    } else {
      console.log(`WARNING: Could not click tab "${report.tab}", trying to find report anyway...`);
    }

    // Debug: Take screenshot after tab click and list visible reports
    const debugScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_tab_${Date.now()}.png`);
    await page.screenshot({ path: debugScreenshot });
    console.log(`Debug screenshot saved: ${debugScreenshot}`);

    // List visible report names
    const visibleReports = await page.evaluate(() => {
      const links = document.querySelectorAll('a');
      const reports = [];
      links.forEach(link => {
        const text = link.textContent?.trim();
        if (text && text.includes('Report')) {
          reports.push(text);
        }
      });
      return reports;
    });
    console.log('Visible reports after tab click:', visibleReports.join(', '));
  }

  // Click on the specific report
  console.log(`Opening ${report.name}...`);

  // Try multiple selector strategies for clicking on the report
  let clicked = false;

  // Strategy 1: Exact text match with quotes
  try {
    await page.click(`text="${report.name}"`, { timeout: 5000 });
    clicked = true;
    console.log('Clicked using exact text match');
  } catch (e) {
    console.log('Exact text match failed, trying alternatives...');
  }

  // Strategy 2: getByText exact match
  if (!clicked) {
    try {
      await page.getByText(report.name, { exact: true }).click({ timeout: 5000 });
      clicked = true;
      console.log('Clicked using getByText exact');
    } catch (e) {
      console.log('getByText exact failed...');
    }
  }

  // Strategy 3: Find element with class containing 'name' and exact text
  if (!clicked) {
    try {
      await page.locator(`.name:text-is("${report.name}")`).click({ timeout: 5000 });
      clicked = true;
      console.log('Clicked using .name class selector');
    } catch (e) {
      console.log('.name selector failed...');
    }
  }

  // Strategy 4: Look for list item or link containing the report name
  if (!clicked) {
    try {
      await page.locator(`li:has-text("${report.name}"), a:has-text("${report.name}")`).first().click({ timeout: 5000 });
      clicked = true;
      console.log('Clicked using li/a has-text');
    } catch (e) {
      console.log('li/a has-text failed...');
    }
  }

  // Strategy 5: Use evaluate to find and click
  if (!clicked) {
    try {
      await page.evaluate((reportName) => {
        const elements = document.querySelectorAll('*');
        for (const el of elements) {
          if (el.textContent && el.textContent.trim() === reportName) {
            el.click();
            return true;
          }
        }
        return false;
      }, report.name);
      clicked = true;
      console.log('Clicked using evaluate');
    } catch (e) {
      console.log('Evaluate click failed...');
    }
  }

  if (!clicked) {
    throw new Error(`Could not find report: ${report.name}`);
  }

  await page.waitForTimeout(2000);

  // Take screenshot after clicking report
  const afterClickScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_click_${Date.now()}.png`);
  await page.screenshot({ path: afterClickScreenshot });
  console.log(`After report click screenshot: ${afterClickScreenshot}`);

  // Check if we landed on a page vs a modal
  const currentUrl = page.url();
  console.log(`Current URL after click: ${currentUrl}`);

  // Handle page-based flow for Real-Time reports vs modal-based flow for other reports
  if (report.pageFlow) {
    console.log('Using page-based flow for Real-Time report...');

    // Wait for the report page to load - look for the GENERATE button as indicator
    try {
      await page.waitForSelector('button:has-text("GENERATE"), button:has-text("Generate"), select', { timeout: 15000 });
      console.log('Report page loaded');
    } catch (e) {
      console.log('Could not find GENERATE button, continuing anyway...');
    }

    // Take debug screenshot
    const pageScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_report_page_${Date.now()}.png`);
    await page.screenshot({ path: pageScreenshot });
    console.log(`Report page screenshot: ${pageScreenshot}`);

    // Select "Custom Dates" from the Date dropdown
    console.log('Selecting custom date range...');

    // Find all selects and identify the Date dropdown (second one, after Report Type)
    const selects = await page.$$('select');
    console.log(`Found ${selects.length} select elements`);

    if (selects.length >= 2) {
      // The Date dropdown is the second select
      const dateDropdown = selects[1];

      // Try different option values for Custom Dates
      const customOptions = ['Custom Dates', 'CUSTOM_DATES', 'CUSTOM', 'custom_dates', 'custom'];
      let customSelected = false;

      for (const optValue of customOptions) {
        try {
          await dateDropdown.selectOption({ label: optValue });
          console.log(`Selected "${optValue}" from Date dropdown`);
          customSelected = true;
          break;
        } catch (e) {
          // Try by value
          try {
            await dateDropdown.selectOption(optValue);
            console.log(`Selected "${optValue}" by value from Date dropdown`);
            customSelected = true;
            break;
          } catch (e2) {
            continue;
          }
        }
      }

      if (!customSelected) {
        // Try clicking the dropdown and selecting by text
        try {
          await dateDropdown.click();
          await page.waitForTimeout(500);
          await page.click('option:has-text("Custom")');
          customSelected = true;
          console.log('Selected Custom by clicking option');
        } catch (e) {
          console.log('Could not click Custom option');
        }
      }

      await page.waitForTimeout(1500);
    }

    // Take screenshot after selecting Custom Dates
    const afterCustomScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_custom_${Date.now()}.png`);
    await page.screenshot({ path: afterCustomScreenshot });
    console.log(`After custom selection screenshot: ${afterCustomScreenshot}`);

    // Wait for date inputs to appear and fill them
    console.log('Setting date range...');
    let datesSet = false;

    // Strategy 1: Look for date inputs that appeared after selecting Custom Dates
    try {
      await page.waitForSelector('input[type="date"]', { timeout: 5000 });
      const dateInputs = await page.$$('input[type="date"]');
      console.log(`Found ${dateInputs.length} date inputs`);
      if (dateInputs.length >= 2) {
        await dateInputs[0].fill(startDate);
        await dateInputs[1].fill(endDate);
        datesSet = true;
        console.log(`Set dates: ${startDate} to ${endDate}`);
      }
    } catch (e) {
      console.log('Date input strategy 1 failed:', e.message);
    }

    // Strategy 2: Look for text inputs with date-related attributes
    if (!datesSet) {
      try {
        const inputs = await page.$$('input[type="text"]');
        console.log(`Found ${inputs.length} text inputs`);
        // Filter for date-looking inputs
        for (let i = 0; i < inputs.length - 1; i++) {
          const placeholder = await inputs[i].getAttribute('placeholder');
          if (placeholder && (placeholder.includes('date') || placeholder.includes('Date') || placeholder.includes('/'))) {
            await inputs[i].fill(startDate);
            await inputs[i + 1].fill(endDate);
            datesSet = true;
            console.log('Set dates using text inputs');
            break;
          }
        }
      } catch (e) {
        console.log('Date input strategy 2 failed:', e.message);
      }
    }

    await page.waitForTimeout(500);

    // Take screenshot before clicking generate
    const preGenScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_pre_generate_${Date.now()}.png`);
    await page.screenshot({ path: preGenScreenshot });
    console.log(`Pre-generate screenshot: ${preGenScreenshot}`);

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 300000 });

    // Click GENERATE button
    console.log('Clicking GENERATE button...');
    let generateClicked = false;

    // Try different strategies to click GENERATE
    try {
      await page.click('button:has-text("GENERATE")', { timeout: 5000 });
      generateClicked = true;
      console.log('Clicked GENERATE button');
    } catch (e) {
      console.log('GENERATE button click failed, trying alternatives...');
    }

    if (!generateClicked) {
      try {
        await page.getByRole('button', { name: /generate/i }).click({ timeout: 5000 });
        generateClicked = true;
        console.log('Clicked GENERATE via getByRole');
      } catch (e) {
        console.log('getByRole failed...');
      }
    }

    if (!generateClicked) {
      try {
        // Use evaluate to click
        await page.evaluate(() => {
          const buttons = document.querySelectorAll('button');
          for (const btn of buttons) {
            if (btn.textContent && btn.textContent.includes('GENERATE')) {
              btn.click();
              return true;
            }
          }
          return false;
        });
        generateClicked = true;
        console.log('Clicked GENERATE via evaluate');
      } catch (e) {
        console.log('Evaluate click failed...');
      }
    }

    // Take screenshot after clicking GENERATE
    await page.waitForTimeout(2000);
    const afterGenerateScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_generate_${Date.now()}.png`);
    await page.screenshot({ path: afterGenerateScreenshot });
    console.log(`After GENERATE screenshot: ${afterGenerateScreenshot}`);

    // Wait a bit for the report to generate (might show loading state)
    await page.waitForTimeout(5000);

    // Take another screenshot
    const afterWaitScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_wait_${Date.now()}.png`);
    await page.screenshot({ path: afterWaitScreenshot });
    console.log(`After wait screenshot: ${afterWaitScreenshot}`);

    // Look for export/download options that might have appeared
    const exportLinks = await page.evaluate(() => {
      const links = [];
      const elements = document.querySelectorAll('a, button');
      elements.forEach(el => {
        const text = (el.textContent || '').toLowerCase();
        if (text.includes('download') || text.includes('export') || text.includes('csv') || text.includes('excel')) {
          links.push(text.trim());
        }
      });
      return links;
    });
    console.log('Export/download options found:', exportLinks.join(', ') || 'none');

    // If no download started yet, try looking for download links
    if (exportLinks.length > 0) {
      console.log('Trying to click export link...');
      try {
        await page.click('a:has-text("download"), a:has-text("export"), a:has-text("csv")');
      } catch (e) {
        console.log('No clickable export link found');
      }
    }

    // Wait for download
    console.log('Waiting for download (this may take a while for large date ranges)...');
    const download = await downloadPromise;

    // Generate timestamped filename for archive
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const archiveFilename = `${report.filename.replace('.csv', '')}_${timestamp}.csv`;
    const archivePath = path.join(CONFIG.EXPORT_DIR, archiveFilename);

    // Save to archive
    await download.saveAs(archivePath);
    console.log(`Archived to: ${archivePath}`);

    // Also save to main location for ingestion
    const mainPath = path.join(CONFIG.EXPORT_DIR, report.filename);
    fs.copyFileSync(archivePath, mainPath);
    console.log(`Main file: ${mainPath}`);

    // For all_sales, also copy to root location for docker volume mount
    if (reportKey === 'all_sales') {
      const rootPath = path.join(__dirname, '../../total_sales.csv');
      fs.copyFileSync(archivePath, rootPath);
      console.log(`Root file: ${rootPath}`);
    }

    return mainPath;
  }

  // Modal-based flow for non-Real-Time reports
  console.log('Using modal-based flow...');

  // Check if we're on a report page instead of a modal
  const hasModal = await page.$('.modal-content, .modal, [role="dialog"]');
  const hasReportPage = await page.$('button:has-text("GENERATE"), button:has-text("Continue")');

  if (!hasModal && hasReportPage) {
    console.log('Detected report page instead of modal, switching to page flow...');
    // This report uses page-based flow, handle it like Real-Time reports

    // Take screenshot
    const reportPageScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_report_page_flow_${Date.now()}.png`);
    await page.screenshot({ path: reportPageScreenshot });
    console.log(`Report page screenshot: ${reportPageScreenshot}`);

    // Select Custom Dates from dropdown
    console.log('Selecting custom date range...');
    const selects = await page.$$('select');
    if (selects.length >= 1) {
      for (const sel of selects) {
        try {
          await sel.selectOption({ label: 'Custom Dates' });
          console.log('Selected Custom Dates');
          await page.waitForTimeout(1500);
          break;
        } catch (e) {
          continue;
        }
      }
    }

    // Fill date inputs
    const dateInputs = await page.$$('input[type="text"], input[type="date"]');
    console.log(`Found ${dateInputs.length} date inputs`);
    for (let i = 0; i < dateInputs.length - 1; i++) {
      try {
        await dateInputs[i].fill(startDate);
        await dateInputs[i + 1].fill(endDate);
        console.log(`Set dates: ${startDate} to ${endDate}`);
        break;
      } catch (e) {
        continue;
      }
    }

    await page.waitForTimeout(500);

    // Take screenshot before generate
    const preGenScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_pre_gen_page_${Date.now()}.png`);
    await page.screenshot({ path: preGenScreenshot });
    console.log(`Pre-generate screenshot: ${preGenScreenshot}`);

    // Set up download handler
    const downloadPromise = page.waitForEvent('download', { timeout: 300000 });

    // Click Continue or Generate button
    console.log('Clicking Continue/Generate button...');
    try {
      await page.click('button:has-text("Continue")');
      console.log('Clicked Continue button');
    } catch (e) {
      try {
        await page.click('button:has-text("GENERATE")');
        console.log('Clicked GENERATE button');
      } catch (e2) {
        await page.click('button.btn-success, button.btn-primary').catch(() => {});
      }
    }

    // Wait for download
    console.log('Waiting for download...');
    const download = await downloadPromise;

    // Save the file
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const archiveFilename = `${report.filename.replace('.csv', '')}_${timestamp}.csv`;
    const archivePath = path.join(CONFIG.EXPORT_DIR, archiveFilename);
    await download.saveAs(archivePath);
    console.log(`Archived to: ${archivePath}`);

    const mainPath = path.join(CONFIG.EXPORT_DIR, report.filename);
    fs.copyFileSync(archivePath, mainPath);
    console.log(`Main file: ${mainPath}`);

    if (reportKey === 'all_sales') {
      const rootPath = path.join(__dirname, '../../total_sales.csv');
      fs.copyFileSync(archivePath, rootPath);
      console.log(`Root file: ${rootPath}`);
    }

    return mainPath;
  }

  // Wait for modal
  console.log('Waiting for modal...');
  await page.waitForSelector('.modal-content, .modal, [role="dialog"]', { timeout: CONFIG.TIMEOUT });

  // Take screenshot of modal
  const modalScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_modal_${Date.now()}.png`);
  await page.screenshot({ path: modalScreenshot });
  console.log(`Modal screenshot: ${modalScreenshot}`);

  // Select "Export report" option if available (should already be selected)
  try {
    const exportRadio = await page.$('input[value="export_report"]');
    if (exportRadio) {
      await exportRadio.click();
      console.log('Selected Export report option');
    }
  } catch (e) {
    // May not have this option or already selected
  }

  // Select "Custom" or "Custom Dates" from the Date dropdown
  console.log('Selecting custom date range...');
  const modalSelect = await page.$('.modal select, .modal-content select, [role="dialog"] select');
  if (modalSelect) {
    // Try different option labels
    const customOptions = ['Custom', 'Custom Dates', 'CUSTOM', 'custom'];
    let customSelected = false;

    for (const opt of customOptions) {
      try {
        await modalSelect.selectOption({ label: opt });
        customSelected = true;
        console.log(`Selected "${opt}" from Date dropdown`);
        break;
      } catch (e) {
        try {
          await modalSelect.selectOption(opt);
          customSelected = true;
          console.log(`Selected "${opt}" by value from Date dropdown`);
          break;
        } catch (e2) {
          continue;
        }
      }
    }

    if (!customSelected) {
      console.log('Could not select Custom option, available options:');
      const options = await page.evaluate(() => {
        const sel = document.querySelector('.modal select, .modal-content select');
        if (sel) {
          return Array.from(sel.options).map(o => `${o.value}: ${o.text}`);
        }
        return [];
      });
      console.log(options.join(', '));
    }
  } else {
    console.log('No select dropdown found in modal');
  }

  // Wait for date inputs to appear
  await page.waitForTimeout(1500);

  // Take screenshot after selecting custom
  const afterCustomScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_modal_after_custom_${Date.now()}.png`);
  await page.screenshot({ path: afterCustomScreenshot });
  console.log(`After custom selection screenshot: ${afterCustomScreenshot}`);

  // Wait for date inputs to appear and fill them
  console.log('Setting date range...');
  let datesSet = false;

  // Strategy 1: Look for date inputs in the modal
  try {
    const modalDateInputs = await page.$$('.modal input[type="date"], .modal-content input[type="date"]');
    console.log(`Found ${modalDateInputs.length} date inputs in modal`);
    if (modalDateInputs.length >= 2) {
      await modalDateInputs[0].fill(startDate);
      await modalDateInputs[1].fill(endDate);
      datesSet = true;
      console.log(`Set dates: ${startDate} to ${endDate}`);
    }
  } catch (e) {
    console.log('Date strategy 1 failed:', e.message);
  }

  // Strategy 2: Look for text inputs in the modal
  if (!datesSet) {
    try {
      const modalInputs = await page.$$('.modal input[type="text"], .modal-content input[type="text"]');
      console.log(`Found ${modalInputs.length} text inputs in modal`);
      if (modalInputs.length >= 2) {
        await modalInputs[0].fill(startDate);
        await modalInputs[1].fill(endDate);
        datesSet = true;
        console.log(`Set dates using text inputs: ${startDate} to ${endDate}`);
      }
    } catch (e) {
      console.log('Date strategy 2 failed:', e.message);
    }
  }

  // Strategy 3: Look for any inputs after the select
  if (!datesSet) {
    try {
      const allInputs = await page.$$('.modal input, .modal-content input');
      const textInputs = [];
      for (const input of allInputs) {
        const type = await input.getAttribute('type');
        if (type === 'text' || type === 'date' || !type) {
          textInputs.push(input);
        }
      }
      console.log(`Found ${textInputs.length} potential date inputs`);
      if (textInputs.length >= 2) {
        await textInputs[0].fill(startDate);
        await textInputs[1].fill(endDate);
        datesSet = true;
        console.log(`Set dates using any inputs: ${startDate} to ${endDate}`);
      }
    } catch (e) {
      console.log('Date strategy 3 failed:', e.message);
    }
  }

  await page.waitForTimeout(500);

  // Take screenshot before clicking Continue
  const preContinueScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_modal_pre_continue_${Date.now()}.png`);
  await page.screenshot({ path: preContinueScreenshot });
  console.log(`Pre-continue screenshot: ${preContinueScreenshot}`);

  // Set up download handler
  const downloadPromise = page.waitForEvent('download', { timeout: 180000 });

  // Click Continue/Export button
  console.log('Clicking export button...');
  const exportSelectors = [
    'button:has-text("Continue")',
    'button:has-text("Export")',
    'button:has-text("Download")',
    'button.btn-success',
    'button.btn-primary',
    'button[type="submit"]',
  ];

  for (const selector of exportSelectors) {
    try {
      const btn = await page.$(selector);
      if (btn) {
        await btn.click();
        break;
      }
    } catch (e) {
      continue;
    }
  }

  // Wait for download - try direct download first, then check Generated tab
  console.log('Waiting for download...');

  let download = null;
  try {
    // Wait up to 30 seconds for direct download
    download = await Promise.race([
      downloadPromise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 30000))
    ]);
    console.log('Direct download started');
  } catch (e) {
    console.log('No direct download, checking Generated tab...');

    // Take screenshot after clicking Continue
    const afterContinueScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_after_continue_${Date.now()}.png`);
    await page.screenshot({ path: afterContinueScreenshot });
    console.log(`After continue screenshot: ${afterContinueScreenshot}`);

    // Wait a bit for the report to be generated
    await page.waitForTimeout(5000);

    // Click on the Generated tab
    try {
      await page.click('text="Generated"', { timeout: 5000 });
      console.log('Clicked Generated tab');
      await page.waitForTimeout(3000);

      // Take screenshot of Generated tab
      const generatedScreenshot = path.join(CONFIG.EXPORT_DIR, `debug_generated_tab_${Date.now()}.png`);
      await page.screenshot({ path: generatedScreenshot });
      console.log(`Generated tab screenshot: ${generatedScreenshot}`);

      // Click "REFRESH GENERATED SECTION" button if available
      try {
        await page.click('button:has-text("REFRESH"), text="REFRESH GENERATED SECTION"', { timeout: 3000 });
        console.log('Clicked refresh button');
        await page.waitForTimeout(3000);
      } catch (e) {
        console.log('No refresh button found');
      }

      // Look for downloadable reports in the Generated section
      // First, inspect what type of elements the Download links are
      const downloadInfo = await page.evaluate(() => {
        // Find all elements with "Download" text
        const allElements = document.querySelectorAll('*');
        const downloadElements = [];
        for (const el of allElements) {
          if (el.textContent && el.textContent.trim() === 'Download' && el.childNodes.length <= 1) {
            downloadElements.push({
              tag: el.tagName,
              href: el.href || null,
              onclick: el.onclick ? 'has onclick' : null,
              className: el.className,
              outerHTML: el.outerHTML.substring(0, 200)
            });
          }
        }
        return downloadElements;
      });

      console.log('Download elements found:', JSON.stringify(downloadInfo, null, 2));

      // Get the download URL
      let downloadUrl = null;
      for (const info of downloadInfo) {
        if (info.href) {
          downloadUrl = info.href;
          break;
        }
      }

      console.log(`Download URL: ${downloadUrl || 'none'}`);

      if (downloadUrl) {
        // Try multiple download strategies
        let downloadStarted = false;

        // Strategy 1: Use page.goto with download capture
        try {
          console.log('Trying direct navigation to download URL...');
          const genDownloadPromise = page.waitForEvent('download', { timeout: 60000 });

          // Navigate to the download URL
          await page.evaluate((url) => {
            const a = document.createElement('a');
            a.href = url;
            a.download = 'report.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          }, downloadUrl);

          download = await genDownloadPromise;
          downloadStarted = true;
          console.log('Download started via programmatic click');
        } catch (e) {
          console.log('Programmatic click failed:', e.message);
        }

        // Strategy 2: Open in new context and capture download
        if (!downloadStarted) {
          try {
            console.log('Trying new page navigation...');
            const newPagePromise = page.context().waitForEvent('page', { timeout: 10000 });
            await page.click('text="Download"', { force: true });

            const newPage = await newPagePromise;
            const genDownloadPromise = newPage.waitForEvent('download', { timeout: 60000 });
            download = await genDownloadPromise;
            downloadStarted = true;
            console.log('Download started via new page');
            await newPage.close();
          } catch (e) {
            console.log('New page strategy failed:', e.message);
          }
        }

        // Strategy 3: Direct fetch using page context
        if (!downloadStarted) {
          try {
            console.log('Trying direct fetch...');
            const response = await page.request.get(downloadUrl);
            if (response.ok()) {
              const buffer = await response.body();
              const filePath = path.join(CONFIG.EXPORT_DIR, report.filename);
              fs.writeFileSync(filePath, buffer);
              console.log(`Downloaded via fetch to: ${filePath}`);
              return filePath;
            }
          } catch (e) {
            console.log('Direct fetch failed:', e.message);
          }
        }

        // Strategy 4: Click and wait for download with longer timeout
        if (!downloadStarted) {
          try {
            console.log('Trying click with extended timeout...');
            const genDownloadPromise = page.waitForEvent('download', { timeout: 180000 });
            await page.click('a:has-text("Download")', { force: true });
            download = await genDownloadPromise;
            downloadStarted = true;
            console.log('Download started with extended wait');
          } catch (e) {
            console.log('Extended click failed:', e.message);
          }
        }

        if (!downloadStarted) {
          console.log('All download strategies failed');
        }
      }

      // If no download URL, try clicking directly and capturing network response
      if (!download) {
        console.log('Trying to click Download element and capture network response...');

        // Set up response listener to capture file data
        let fileData = null;
        let fileUrl = null;

        const responseHandler = async (response) => {
          const url = response.url();
          const contentType = response.headers()['content-type'] || '';
          console.log(`Response: ${url.substring(0, 100)} - ${contentType}`);

          // Look for CSV or file download responses
          if (contentType.includes('csv') ||
              contentType.includes('octet-stream') ||
              contentType.includes('download') ||
              url.includes('export') ||
              url.includes('download') ||
              url.includes('generated')) {
            try {
              fileData = await response.body();
              fileUrl = url;
              console.log(`Captured file response from: ${url} (${fileData.length} bytes)`);
            } catch (e) {
              console.log(`Could not get body from ${url}: ${e.message}`);
            }
          }
        };

        page.on('response', responseHandler);

        try {
          // Find the first completed report row and click its Download link
          const completedRows = await page.$$('tr:has-text("Completed")');
          console.log(`Found ${completedRows.length} completed report rows`);

          if (completedRows.length > 0) {
            // Click the Download link in the first completed row
            const downloadLink = await completedRows[0].$('a:has-text("Download")');
            if (downloadLink) {
              console.log('Clicking Download link in completed row...');
              await downloadLink.click({ force: true });
            } else {
              // Fallback: click the Download text anywhere
              console.log('Clicking first Download text...');
              await page.click('text="Download"', { force: true });
            }
          } else {
            await page.click('text="Download"', { force: true });
          }

          console.log('Waiting for network response...');

          // Wait for response
          await page.waitForTimeout(10000);

          // Check if we captured file data
          if (fileData) {
            const filePath = path.join(CONFIG.EXPORT_DIR, report.filename);
            fs.writeFileSync(filePath, fileData);
            console.log(`Downloaded via network capture to: ${filePath} (${fileData.length} bytes)`);

            // Archive copy
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const archiveFilename = `${report.filename.replace('.csv', '')}_${timestamp}.csv`;
            const archivePath = path.join(CONFIG.EXPORT_DIR, archiveFilename);
            fs.writeFileSync(archivePath, fileData);
            console.log(`Archived to: ${archivePath}`);

            // For all_sales, also copy to root location
            if (reportKey === 'all_sales') {
              const rootPath = path.join(__dirname, '../../total_sales.csv');
              fs.writeFileSync(rootPath, fileData);
              console.log(`Root file: ${rootPath}`);
            }

            return filePath;
          } else {
            console.log('No file data captured from network');
          }
        } catch (e) {
          console.log('Click and capture failed:', e.message);
        } finally {
          page.off('response', responseHandler);
        }
      }
    } catch (tabError) {
      console.log('Could not access Generated tab:', tabError.message);
    }
  }

  if (!download) {
    // Last resort: wait longer for the original download promise
    console.log('Waiting longer for download...');
    download = await downloadPromise;
  }

  // Generate timestamped filename for archive
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const archiveFilename = `${report.filename.replace('.csv', '')}_${timestamp}.csv`;
  const archivePath = path.join(CONFIG.EXPORT_DIR, archiveFilename);

  // Save to archive
  await download.saveAs(archivePath);
  console.log(`Archived to: ${archivePath}`);

  // Also save to main location for ingestion
  const mainPath = path.join(CONFIG.EXPORT_DIR, report.filename);
  fs.copyFileSync(archivePath, mainPath);
  console.log(`Main file: ${mainPath}`);

  // For all_sales, also copy to root location for docker volume mount
  if (reportKey === 'all_sales') {
    const rootPath = path.join(__dirname, '../../total_sales.csv');
    fs.copyFileSync(archivePath, rootPath);
    console.log(`Root file: ${rootPath}`);
  }

  return mainPath;
}

function getTodayDate() {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

function getYesterdayDate() {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  return date.toISOString().split('T')[0];
}

function addDays(dateStr, days) {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
}

async function main() {
  // Validate credentials
  if (!CONFIG.BLAZE_EMAIL || !CONFIG.BLAZE_PASSWORD) {
    console.error('ERROR: Missing BLAZE_EMAIL or BLAZE_PASSWORD in environment');
    console.error('Set these in your .env file:');
    console.error('  BLAZE_EMAIL=your@email.com');
    console.error('  BLAZE_PASSWORD=yourpassword');
    process.exit(1);
  }

  // Create export directory
  if (!fs.existsSync(CONFIG.EXPORT_DIR)) {
    fs.mkdirSync(CONFIG.EXPORT_DIR, { recursive: true });
  }

  // Create logs directory
  const logsDir = path.join(CONFIG.EXPORT_DIR, 'logs');
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }

  // Parse command line args
  const args = process.argv.slice(2);
  let mode = args[0] || 'incremental';  // 'incremental', 'full', 'discover', or specific dates
  let startDate, endDate;

  // Which reports to run
  let reportsToRun = ['all_sales'];  // Default: just all sales (transactions)

  // Check for --all flag to run all reports
  if (args.includes('--all')) {
    reportsToRun = Object.keys(REPORTS);
  }

  // Check for specific report
  const reportArg = args.find(a => a.startsWith('--report='));
  if (reportArg) {
    const reportKey = reportArg.split('=')[1];
    if (REPORTS[reportKey]) {
      reportsToRun = [reportKey];
    } else {
      console.error(`Unknown report: ${reportKey}`);
      console.error('Available reports:', Object.keys(REPORTS).join(', '));
      process.exit(1);
    }
  }

  if (mode === 'discover') {
    // Just login and list available reports
    console.log('='.repeat(60));
    console.log('BLAZE REPORT DISCOVERY MODE');
    console.log('='.repeat(60));

    const browser = await chromium.launch({
      headless: CONFIG.HEADLESS,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--single-process',
      ],
    });

    const context = await browser.newContext({
      acceptDownloads: true,
      viewport: { width: 1280, height: 800 },
    });

    const page = await context.newPage();

    try {
      await login(page);
      await listAvailableReports(page);

      // Take a screenshot of the reports page
      const screenshotPath = path.join(CONFIG.EXPORT_DIR, 'reports_page.png');
      await page.screenshot({ path: screenshotPath, fullPage: true });
      console.log(`\nScreenshot saved: ${screenshotPath}`);

    } catch (error) {
      console.error('Error during discovery:', error);
    } finally {
      await browser.close();
    }
    return;
  }

  if (mode === 'full') {
    // Full historical scrape
    startDate = CONFIG.HISTORICAL_START_DATE;
    endDate = getTodayDate();
    console.log('Mode: FULL historical scrape');
  } else if (mode === 'incremental') {
    // Incremental: from last transaction date to today
    const lastDate = await getLastTransactionDate();
    if (lastDate) {
      // Start from day after last transaction
      startDate = addDays(lastDate, 1);
      endDate = getTodayDate();

      if (startDate > endDate) {
        console.log('Database is already up to date. No new data to scrape.');
        console.log(`Last transaction date: ${lastDate}`);
        console.log(`Today: ${endDate}`);
        process.exit(0);
      }
      console.log('Mode: INCREMENTAL scrape');
      console.log(`Last transaction in DB: ${lastDate}`);
    } else {
      // No data in DB, do full scrape
      startDate = CONFIG.HISTORICAL_START_DATE;
      endDate = getTodayDate();
      console.log('Mode: FULL scrape (no existing data found)');
    }
  } else {
    // Manual date range
    startDate = args[0];
    endDate = args[1] || getTodayDate();
    console.log('Mode: MANUAL date range');
  }

  console.log('='.repeat(60));
  console.log('BLAZE MULTI-REPORT SCRAPER');
  console.log('='.repeat(60));
  console.log(`Reports to export: ${reportsToRun.join(', ')}`);
  console.log(`Start Date: ${startDate}`);
  console.log(`End Date: ${endDate}`);
  console.log(`Headless: ${CONFIG.HEADLESS}`);
  console.log(`Export Dir: ${CONFIG.EXPORT_DIR}`);
  console.log('='.repeat(60));

  const browser = await chromium.launch({
    headless: CONFIG.HEADLESS,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--single-process',
    ],
  });

  const context = await browser.newContext({
    acceptDownloads: true,
    viewport: { width: 1280, height: 800 },
  });

  const page = await context.newPage();

  try {
    // Step 1: Login
    await login(page);

    // Step 2: Export each report
    const exportResults = {};
    for (const reportKey of reportsToRun) {
      try {
        console.log('\n' + '='.repeat(60));
        console.log(`EXPORTING: ${REPORTS[reportKey].name}`);
        console.log('='.repeat(60));

        const filePath = await exportReport(page, reportKey, startDate, endDate);
        exportResults[reportKey] = { success: true, path: filePath };

        // Wait between reports to avoid rate limiting
        if (reportsToRun.indexOf(reportKey) < reportsToRun.length - 1) {
          console.log('\nWaiting before next report...');
          await page.waitForTimeout(2000);
        }
      } catch (error) {
        console.error(`Failed to export ${reportKey}:`, error.message);
        exportResults[reportKey] = { success: false, error: error.message };

        // Take screenshot on error
        const screenshotPath = path.join(CONFIG.EXPORT_DIR, `error_${reportKey}_${Date.now()}.png`);
        await page.screenshot({ path: screenshotPath });
        console.log(`Error screenshot: ${screenshotPath}`);
      }
    }

    console.log('\n' + '='.repeat(60));
    console.log('EXPORT SUMMARY');
    console.log('='.repeat(60));
    for (const [key, result] of Object.entries(exportResults)) {
      console.log(`${REPORTS[key].name}: ${result.success ? 'SUCCESS' : 'FAILED'}`);
    }

    // Step 3: Trigger ingestion for successful exports
    console.log('\n' + '='.repeat(60));
    console.log('INGESTION PHASE');
    console.log('='.repeat(60));

    const ingestionResults = {};
    for (const reportKey of reportsToRun) {
      if (exportResults[reportKey]?.success) {
        const result = await triggerIngestion(reportKey);
        ingestionResults[reportKey] = result;
      }
    }

    // Step 4: Validate (for transaction data)
    if (reportsToRun.includes('all_sales')) {
      const valid = await validateData();
      if (!valid) {
        console.error('\nWARNING: Data validation failed!');
        process.exit(1);
      }
    }

    console.log('\n' + '='.repeat(60));
    console.log('ALL OPERATIONS COMPLETE');
    console.log('='.repeat(60));

    // Summary
    console.log('\nFinal Summary:');
    for (const reportKey of reportsToRun) {
      const exported = exportResults[reportKey]?.success ? 'YES' : 'NO';
      const ingested = ingestionResults[reportKey] ? 'YES' : 'NO';
      console.log(`  ${REPORTS[reportKey].name}: Exported=${exported}, Ingested=${ingested}`);
    }

  } catch (error) {
    console.error('Error during scrape:', error);

    // Take screenshot for debugging
    const screenshotPath = path.join(CONFIG.EXPORT_DIR, `error_screenshot_${Date.now()}.png`);
    await page.screenshot({ path: screenshotPath });
    console.log(`Screenshot saved: ${screenshotPath}`);

    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
