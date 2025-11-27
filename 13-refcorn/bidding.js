const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs-extra');
const path = require('path');

puppeteer.use(StealthPlugin());


function parseRemainingTime(rt) {
    const match = rt.match(/(\d+)\s*Day,?\s*(\d{2}):(\d{2}):(\d{2})/);
    if (!match) return 0;
    const [_, days, hours, minutes, seconds] = match.map(Number);
    return days*86400 + hours*3600 + minutes*60 + seconds;
}

async function readCSV(filePath) {
    const content = await fs.readFile(filePath, "utf-8");
    return content.split(/\r?\n/).filter(Boolean);
}


async function login(browser) {
    const loginUrl = "https://auctions.redcorn.co.uk/Account/LogOn?returnUrl=%2F";
    const page = await browser.newPage();
    await page.goto(loginUrl, { waitUntil: "networkidle2" });

    console.log("👉 LOGIN: Please log in manually on the browser, then press Enter here to continue...");
    await new Promise(resolve => {
        process.stdin.resume();
        process.stdin.once('data', () => {
            process.stdin.pause();
            resolve();
        });
    });

    console.log("✔ Login complete! Now monitoring auctions.");
    return page;
}


async function monitorAuctionUntilEnd(id, page, htmlFolder) {
    const listingUrl = `https://auctions.redcorn.co.uk/Listing/History/${id}?currency=GBP`;
    const htmlPath = path.join(htmlFolder, `${id}.html`);

    console.log(`🔄 Monitoring Auction ID: ${id}`);
    await page.goto(listingUrl, { waitUntil: "networkidle2" });

    let remainingTimeSec = 1;

    while (remainingTimeSec > 0) {
        const remainingTime = await page.evaluate(() => {
            const rows = Array.from(document.querySelectorAll(".table-condensed tr"));
            const row = rows.find(r => r.querySelector("td strong")?.innerText.trim() === "Remaining Time");
            return row ? row.querySelectorAll("td")[1]?.innerText.trim() : "";
        });

        remainingTimeSec = parseRemainingTime(remainingTime);
        console.log(`🕒 ID: ${id} | Remaining Time: ${remainingTime}`);

        if (remainingTimeSec > 0) {

            await new Promise(r => setTimeout(r, 5000));
            await page.reload({ waitUntil: "networkidle2" });
        }
    }


    const fullHtml = await page.evaluate(() => document.documentElement.outerHTML);
    await fs.writeFile(htmlPath, fullHtml);
    console.log(`✅ Auction ID ${id} ended. HTML saved: ${htmlPath}`);
}

(async () => {
    const csvPath = path.join(__dirname, "auction_ids.csv");
    const ids = await readCSV(csvPath);

    const htmlFolder = path.join(__dirname, "bidding");
    await fs.ensureDir(htmlFolder);

    const browser = await puppeteer.launch({
        headless: false,
        executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
        userDataDir: "C:/Users/HP/AppData/Local/Google/Chrome/User Data Puppeteer",
        defaultViewport: null
    });


    const page = await login(browser);


    for (const id of ids) {
        await monitorAuctionUntilEnd(id, page, htmlFolder);
    }

    console.log("🏁 All auctions processed.");
    await browser.close();
})();
