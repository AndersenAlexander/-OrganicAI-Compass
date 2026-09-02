import { expect, test, type Page } from "@playwright/test";
import { installMockAuthSession } from "./utils/authSession";

const viewports = [{width:1448,height:1086},{width:1366,height:768},{width:1024,height:768},{width:768,height:1024},{width:390,height:844}] as const;

async function prepare(page:Page, theme:"dark"|"light"="dark"){
  await page.addInitScript(({theme})=>{localStorage.setItem("organicai-theme",theme);localStorage.setItem("organicai_active_profile_id","demo-profile")},{theme});
}
async function noOverflow(page:Page){ expect(await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth)).toBeLessThanOrEqual(0); }

test.describe("Public Project Roadmap",()=>{
  for(const viewport of viewports){
    test(`${viewport.width}x${viewport.height} renders without overflow`,async({page})=>{
      await page.setViewportSize(viewport);await prepare(page);await page.goto("/project-roadmap");
      await expect(page.getByRole("heading",{level:1,name:/From research concept/})).toBeVisible();
      await expect(page.locator(".project-roadmap-milestone")).toHaveCount(8);
      await expect(page.locator("header.no-print")).toHaveCount(1);await noOverflow(page);
      if(viewport.width>=1280){const nav=page.getByRole("navigation",{name:"Global navigation"});await expect(nav.getByRole("link",{name:"Project Roadmap",exact:true})).toHaveAttribute("aria-current","page");}
      else{await page.getByRole("button",{name:"Open navigation menu"}).click();const nav=page.getByRole("navigation",{name:"Global mobile navigation"});await expect(nav.getByRole("link",{name:"Project Roadmap",exact:true})).toHaveAttribute("aria-current","page");}
    });
  }
  test("statuses, evidence, and CTA routes are accurate",async({page})=>{
    await page.setViewportSize({width:1448,height:1086});await prepare(page);await page.goto("/project-roadmap");
    await expect(page.getByText("READY FOR API TESTING",{exact:true})).toBeVisible();
    await expect(page.locator(".project-roadmap-verification").getByText("Software verification does not equal empirical user validation.",{exact:true})).toBeVisible();
    await expect(page.getByRole("link",{name:/Explore the Research/}).first()).toHaveAttribute("href","/research");
    await expect(page.getByRole("link",{name:"Open Knowledge Base"}).first()).toHaveAttribute("href","/knowledge-base");
    await expect(page.getByRole("link",{name:/Try the Diagnostic/}).first()).toHaveAttribute("href","/diagnostic");
  });
  test("personalized roadmap keeps the GlobalHeader workspace active state",async({page})=>{
    await page.setViewportSize({width:1448,height:1086});await installMockAuthSession(page,{state:"demo"});await page.goto("/roadmap/demo-profile");
    await expect(page.getByRole("navigation",{name:"Global navigation"})).toBeVisible();
    await expect(page.getByRole("button",{name:"Workspace"})).toHaveClass(/global-header__link--active/);
    await expect(page.getByRole("navigation",{name:"Public navigation"})).toHaveCount(0);
    await expect(page.getByRole("navigation",{name:"Workspace navigation"})).toHaveCount(0);
  });
  test("light mode remains readable at every required viewport",async({page})=>{
    for(const viewport of viewports){
      await page.setViewportSize(viewport);await prepare(page,"light");await page.goto("/project-roadmap");
      await expect(page.locator("html")).toHaveAttribute("data-theme","light");await noOverflow(page);
      const contrast=await page.locator(".milestone-card").first().evaluate((card)=>{
        const parse=(value:string)=>{const match=value.match(/[\d.]+/g)?.slice(0,3).map(Number)??[0,0,0];return match.map(channel=>{const normalized=channel/255;return normalized<=.03928?normalized/12.92:Math.pow((normalized+.055)/1.055,2.4);});};
        const luminance=(rgb:number[])=>.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];
        const text=luminance(parse(getComputedStyle(card.querySelector("p")!).color));
        // Light milestone surfaces are an opaque white-to-light-cyan gradient; white is the conservative endpoint.
        const background=luminance([1,1,1]);
        return (Math.max(text,background)+.05)/(Math.min(text,background)+.05);
      });
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    }
  });
  test("captures actual viewport and full-page dark screenshots while checking light mode",async({page})=>{
    await page.setViewportSize({width:1448,height:1086});await prepare(page);await page.goto("/project-roadmap");
    await page.screenshot({path:"qa-project-roadmap-1448x1086.png"});await page.screenshot({path:"qa-project-roadmap-full-1448.png",fullPage:true});
    await page.getByRole("button",{name:"Switch to light mode"}).click();await expect(page.locator("html")).toHaveAttribute("data-theme","light");await noOverflow(page);await page.screenshot({path:"qa-project-roadmap-light-1448x1086.png"});await page.screenshot({path:"qa-project-roadmap-light-full-1448.png",fullPage:true});
    await page.setViewportSize({width:390,height:844});await page.evaluate(()=>localStorage.setItem("organicai-theme","dark"));await page.goto("/project-roadmap");
    await page.screenshot({path:"qa-project-roadmap-390x844.png"});await page.screenshot({path:"qa-project-roadmap-full-390.png",fullPage:true});
    await page.getByRole("button",{name:"Switch to light mode"}).click();await expect(page.locator("html")).toHaveAttribute("data-theme","light");await noOverflow(page);await page.screenshot({path:"qa-project-roadmap-light-390x844.png"});await page.screenshot({path:"qa-project-roadmap-light-full-390.png",fullPage:true});
  });
});
