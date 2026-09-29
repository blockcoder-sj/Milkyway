/* Requires Node >=20, Playwright and Chrome. Only runs against the synthetic fixture. */
const assert = require("node:assert/strict");
const {chromium} = require("playwright");
(async () => {
  const base = "http://127.0.0.1:8767";
  const response = await fetch(base + "/api/config");
  assert.equal(response.headers.get("X-Milkyway-Offline-Fixture"), "synthetic-no-external-ai",
    "Refusing approval clicks outside the isolated synthetic fixture");
  const browser = await chromium.launch({headless:true, ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[]; page.on("pageerror",e=>errors.push(e.message));
    await page.goto(base + "/#strategy");
    await page.waitForSelector("#researchTurns .research-turn");
    const count=await page.locator("#researchVersions .research-version").count();
    await page.locator("#researchMessage textarea").fill("손절 조건을 검토해줘");
    await page.locator("#researchMessage button").click();
    await page.waitForSelector('[data-research-action="approve"]');
    assert.match(await page.locator(".research-approval").innerText(),/gpt-5\.4-mini · 추론 none/);
    await page.reload(); await page.waitForSelector('[data-research-action="approve"]');
    await page.locator('[data-research-action="approve"]').click();
    await page.waitForFunction(n=>document.querySelectorAll("#researchVersions .research-version").length===n+1,count);
    await page.locator("#researchDeploy select").selectOption({index:0});
    await page.locator("#researchDeploy button").click();
    await page.waitForSelector('[data-research-action="history"]');
    await page.locator('[data-research-action="history"]').first().click();
    await page.waitForSelector("#accountHistoryDialog[open]");
    await page.locator("#accountHistoryDialog [data-close]").click();
    await page.locator("[data-candidate]").first().check();
    for(const [key,value] of Object.entries({start_date:"2026-03-02",split_date:"2026-06-01",end_date:"2026-09-24",objective:"return_pct"})) {
      const input=page.locator(`#researchExperiment [name=${key}]`);
      if(key==="objective") await input.selectOption(value); else await input.fill(value);
    }
    const job=page.waitForResponse(r=>r.url().endsWith("/experiments")&&r.request().method()==="POST");
    await page.locator("#researchExperiment button").click();
    const comparison=await job; assert.equal(comparison.status(),201); assert.equal((await comparison.json()).objective,"return_pct");
    await page.waitForFunction(()=>document.querySelectorAll(".research-comparison").length===2);
    if(process.env.SCREENSHOT_DIR) await page.screenshot({path:process.env.SCREENSHOT_DIR+"/research-desktop.png",fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,"Mobile horizontal overflow");
    if(process.env.SCREENSHOT_DIR) await page.screenshot({path:process.env.SCREENSHOT_DIR+"/research-mobile.png",fullPage:true});
    assert.equal(await page.locator("#researchError").innerText(),"");
    assert.deepEqual(errors,[]);
    console.log("PASS: preview, restored approval, immutable version, paper deployment, history, comparison objective, mobile, no browser errors");
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
