import puppeteer from 'puppeteer';

async function launchVisualLogin() {
  console.log("============================================================");
  console.log("LAUNCHING VISIBLE BROWSER SESSION AND PERFORMING LOGIN");
  console.log("============================================================");

  // Launch browser with headless: false to show it on screen
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null, // Adapts to browser window size
    args: [
      '--start-maximized',
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  const context = browser.defaultBrowserContext();
  // Grant geolocation permission so coordinates verification works immediately
  await context.overridePermissions('http://localhost:5173', ['geolocation']);

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  // Set mock geolocation
  await page.setGeolocation({ latitude: 37.774900, longitude: -122.419400, accuracy: 10 });

  try {
    console.log("Navigating to http://localhost:5173/ ...");
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' });

    console.log("Typing username: john_dev ...");
    await page.type('#username', 'john_dev', { delay: 150 }); // 150ms delay per key to simulate human typing

    console.log("Typing password...");
    await page.type('#password', 'AdminPassword123!', { delay: 150 });

    console.log("Clicking 'Sign In' button...");
    await page.click('button[type="submit"]');

    // Wait for the React state change to complete and reveal the Welcome back screen
    await page.waitForFunction(() => document.body.innerText.includes('Welcome back'), { timeout: 10000 });
    console.log("🎉 Successfully logged in! The browser window will remain open on your screen.");

  } catch (error) {
    console.error("❌ Error during visual login:", error);
  }
  
  // Note: We deliberately do NOT call browser.close() here so the browser window stays open for you!
}

launchVisualLogin();
