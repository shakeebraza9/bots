const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");
const fs = require("fs-extra");
const path = require("path");

puppeteer.use(StealthPlugin());

(async () => {
    const browseUrl = "https://auctions.redcorn.co.uk/Browse/C160534/Cars?ViewStyle=list&StatusFilter=active_only&ListingType=&SortFilterOptions=0";

    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,
        executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
        userDataDir: "C:/Users/HP/AppData/Local/Google/Chrome/User Data Puppeteer"
    });

    const page = await browser.newPage();
    await page.goto(browseUrl, { waitUntil: "networkidle2" });

    console.log("👉 Login manually if required, then press Enter in terminal...");
    require("child_process").execSync("pause >nul");

    const htmlFolder = path.join(__dirname, "html");
    await fs.ensureDir(htmlFolder);

    const csvPath = path.join(__dirname, "auction_ids.csv");

    // 📌 Create CSV with only header "id"
    if (!fs.existsSync(csvPath)) {
        await fs.writeFile(csvPath, "id\n");
    }

    let pageNo = 1;

    while (true) {
        console.log(`🔄 Checking Browse Page ${pageNo}...`);
        await page.waitForSelector("section[data-listingid]");

        const listings = await page.$$eval("section[data-listingid]", (items) => {
            return items
                .map((el) => {
                    const timeEl = el.querySelector(".time span[data-end-hide-selector]");
                    if (!timeEl) return null;

                    const timeText = timeEl.innerText.trim();
                    const match = timeText.match(/0 Days 0?(\d):(\d{2}):(\d{2})/);
                    if (!match) return null;

                    const hours = parseInt(match[1]);
                    if (hours >= 1) return null;

                    const link = el.querySelector("a.btn-default")?.href;
                    const id = link?.match(/Listing\/Details\/(\d+)/)?.[1];

                    return id;
                })
                .filter(Boolean);
        });

        console.log(`⏱️ Found Listings < 1 Hour:`, listings);

        for (const id of listings) {
            const detailUrl = `https://auctions.redcorn.co.uk/Listing/Details/${id}`;
            console.log(`➡️ Opening Detail Page ID: ${id}`);

            await page.goto(detailUrl, { waitUntil: "networkidle2" });
            await new Promise(r => setTimeout(r, 2000));

            const html = await page.evaluate(() => document.documentElement.outerHTML);
            await fs.writeFile(path.join(htmlFolder, `${id}.html`), html);

            console.log(`💾 Saved HTML: ${id}.html`);

            // 📌 Append CSV with ID only
            await fs.appendFile(csvPath, `${id}\n`);
            console.log(`📝 Added ID to CSV: ${id}`);

            await page.goto(browseUrl, { waitUntil: "networkidle2" });
        }

        const hasNext = await page.$("ul.pagination li.active + li a");
        if (!hasNext) break;

        const nextUrl = await page.$eval("ul.pagination li.active + li a", el => el.href);
        await page.goto(nextUrl, { waitUntil: "networkidle2" });
        pageNo++;
    }

    console.log("🏁 Completed scraping pages ending < 1 hour!");

    await browser.close();
})();
