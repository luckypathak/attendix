import puppeteer from 'puppeteer';
import path from 'path';

async function runVisualDemo() {
  console.log("==============================================================");
  console.log("STARTING VISUAL LOCAL DEMO FOR SUPER ADMIN & OVERTIME WORKFLOW");
  console.log("==============================================================");

  // Setup screenshot save paths in the conversation's artifact folder
  const artifactsDir = '/Users/luckyrajput/.gemini/antigravity-ide/brain/82ebd3ae-4c24-459c-b010-1f3656b5b558';
  const superadminScreenshotPath = path.join(artifactsDir, 'superadmin_companies.png');
  const overtimeScreenshotPath = path.join(artifactsDir, 'attendance_overtime.png');

  // Launch browser in visual mode (headless: false)
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: [
      '--start-maximized',
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  const context = browser.defaultBrowserContext();
  await context.overridePermissions('http://localhost:5173', ['geolocation']);

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  // Listen to browser console and page errors
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Mock geographic location
  await page.setGeolocation({ latitude: 37.774900, longitude: -122.419400, accuracy: 10 });

  try {
    // 1. Navigation & Login
    console.log("1. Navigating to Login Page...");
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' });

    console.log("2. Typing credentials...");
    await page.type('#username', 'localsuper', { delay: 100 });
    await page.type('#password', 'Password@123', { delay: 100 });

    console.log("3. Logging in...");
    await page.click('button[type="submit"]');

    // Wait for the React state change to complete and redirect to dashboard
    await new Promise(r => setTimeout(r, 5000));
    console.log("🎉 Login Successful!");

    // 2. Go to Super Admin Companies Panel
    console.log("4. Navigating to Super Admin Companies Portal...");
    await page.goto('http://localhost:5173/companies', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 3000)); // Allow components to render
    
    console.log(`📸 Saving Super Admin Companies screenshot to: ${superadminScreenshotPath}`);
    await page.screenshot({ path: superadminScreenshotPath });

    // 3. Go to Attendance console and view Overtime table
    console.log("5. Navigating to Attendance & Overtime Approvals Registry...");
    await page.goto('http://localhost:5173/attendance', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 3000)); // Allow components to render

    console.log(`📸 Saving Overtime table screenshot to: ${overtimeScreenshotPath}`);
    await page.screenshot({ path: overtimeScreenshotPath });

    console.log("\n==============================================================");
    console.log("VISUAL SCREENSHOTS CAPTURED SUCCESSFULY!");
    console.log("The browser window will remain open on your screen so you can interact with it.");
    console.log("==============================================================");

  } catch (error) {
    console.error("❌ Error running visual demo:", error);
  }
}

runVisualDemo();
