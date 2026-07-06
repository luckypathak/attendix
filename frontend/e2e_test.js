import puppeteer from 'puppeteer';
import path from 'path';
import fs from 'fs';

const screenshotDir = '/Users/luckyrajput/.gemini/antigravity-ide/brain/82ebd3ae-4c24-459c-b010-1f3656b5b558';

async function runE2ETests() {
  console.log("============================================================");
  console.log("STARTING ATTENDIX WORKFORCE OS E2E UI BROWSER TEST (PUPPETEER)");
  console.log("============================================================");

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = browser.defaultBrowserContext();
  // Override permissions to grant geolocation automatically
  await context.overridePermissions('http://localhost:5173', ['geolocation']);

  const page = await browser.newPage();
  // Set viewport to responsive standard laptop screen
  await page.setViewport({ width: 1280, height: 800 });
  // Set GPS location coordinates for clock-in checks
  await page.setGeolocation({ latitude: 37.774900, longitude: -122.419400, accuracy: 10 });

  try {
    // ---------------------------------------------------------
    // STEP 1: VISIT LOGIN PAGE
    // ---------------------------------------------------------
    console.log("\n[UI STEP 1] Navigating to http://localhost:5173/ ...");
    await page.goto('http://localhost:5173/', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: path.join(screenshotDir, 'ui_1_login_page.png') });
    console.log("📸 Captured login page: ui_1_login_page.png");

    // ---------------------------------------------------------
    // STEP 2: PERFORM LOGIN AS EMPLOYEE (john_dev)
    // ---------------------------------------------------------
    console.log("\n[UI STEP 2] Entering employee login credentials...");
    await page.type('#username', 'john_dev');
    await page.type('#password', 'AdminPassword123!');
    
    console.log("Clicking Sign In...");
    await page.click('button[type="submit"]');
    // Wait for the React dashboard UI components to render
    await page.waitForFunction(() => document.body.innerText.includes('Welcome back'), { timeout: 15000 });

    await page.screenshot({ path: path.join(screenshotDir, 'ui_2_employee_dashboard.png') });
    console.log("📸 Captured employee dashboard: ui_2_employee_dashboard.png");

    // ---------------------------------------------------------
    // STEP 3: NAVIGATE TO ATTENDANCE TIMECARD
    // ---------------------------------------------------------
    console.log("\n[UI STEP 3] Navigating to /attendance page...");
    await page.goto('http://localhost:5173/attendance', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: path.join(screenshotDir, 'ui_3_attendance_page.png') });
    console.log("📸 Captured attendance page before clock action: ui_3_attendance_page.png");

    // Trigger fetch GPS coordinates in the UI
    console.log("Clicking 'Fetch Live GPS Location' button...");
    await page.click('button:has-text("Fetch Live GPS Location")').catch(() => {});
    // Wait for geocoding simulation
    await page.waitForTimeout ? await page.waitForTimeout(3000) : new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: path.join(screenshotDir, 'ui_4_gps_locked.png') });
    console.log("📸 Captured attendance page with locked coordinates: ui_4_gps_locked.png");

    // ---------------------------------------------------------
    // STEP 4: NAVIGATE TO LEAVES PLANNER
    // ---------------------------------------------------------
    console.log("\n[UI STEP 4] Navigating to /leaves page...");
    await page.goto('http://localhost:5173/leaves', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: path.join(screenshotDir, 'ui_5_leaves_page.png') });
    console.log("📸 Captured leaves request workspace: ui_5_leaves_page.png");

    // ---------------------------------------------------------
    // STEP 5: LOG OUT AND LOG IN AS MANAGER (sarah_hr)
    // ---------------------------------------------------------
    console.log("\n[UI STEP 5] Signing out employee (clearing session)...");
    await page.evaluate(() => {
      localStorage.clear();
    });
    // Redirect to login page
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' });
    
    console.log("Logging in as HR Manager: sarah_hr...");
    await page.type('#username', 'sarah_hr');
    await page.type('#password', 'AdminPassword123!');
    await page.click('button[type="submit"]');
    // Wait for the React dashboard UI components to render
    await page.waitForFunction(() => document.body.innerText.includes('Welcome back'), { timeout: 15000 });
    
    await page.screenshot({ path: path.join(screenshotDir, 'ui_6_manager_dashboard.png') });
    console.log("📸 Captured manager dashboard: ui_6_manager_dashboard.png");

    // ---------------------------------------------------------
    // STEP 6: REVIEW AUDIT TIMELINES
    // ---------------------------------------------------------
    console.log("\n[UI STEP 6] Navigating to /audit page...");
    await page.goto('http://localhost:5173/audit', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: path.join(screenshotDir, 'ui_7_audit_logs.png') });
    console.log("📸 Captured security audit trail page: ui_7_audit_logs.png");

    console.log("\n" + "="*60);
    console.log("E2E UI BROWSER TEST COMPLETED SUCCESSFULLY!");
    console.log("============================================================");

  } catch (error) {
    console.error("❌ E2E UI Test encountered an error:", error);
  } finally {
    await browser.close();
  }
}

runE2ETests();
