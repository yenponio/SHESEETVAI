import { test, expect } from "@playwright/test";
const pixel = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#FFF1F1"/><rect x="80" y="40" width="480" height="400" fill="#EFA6A6"/><text x="320" y="225" text-anchor="middle" font-family="sans-serif" font-size="28" fill="#3F2929">TEST EVIDENCE</text><text x="320" y="270" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#3F2929">640 x 480 - exact report image</text></svg>');
const students = Array.from({length:12},(_,i)=>({id:i+1,student_number:`TEST-${i+1}`,barcode:`1234${i+1}`,full_name:i ? `Student ${i+1}` : "Alexandra Example Long Student Name",email:`student${i+1}.long.email@example.test`,college:i%2 ? "SOC" : "School of Engineering and Architecture",id_front:pixel,offense_counts:{total_minor_offenses:i ? 0 : 5,equivalent_major_offenses:i ? 0 : 1}}));
const records = [{id:41,studentNumber:"TEST-1",name:students[0].full_name,college:"SEA",collegeName:students[0].college,violationType:"Shoulders exposed, Midriff exposed",date:"2026-09-23",time:"14:30:00",reportedAt:"2026-09-23T14:30:00+08:00",evidence_image:pixel,total_minor_offenses:5,equivalent_major_offenses:1,confirmed_entry:true,osa_decision:"CONFIRMED_ALLOW",email_status:"SENT"}];
const inspection = {id:110,attempt_id:55,student:{student_number:"TEST-1",name:students[0].full_name,college:students[0].college,photo:pixel},ai_result:"VIOLATION",violations:["Shoulders exposed","Midriff exposed","Knees exposed"],screenshot:pixel,confirmation_status:"PENDING",detected_at:"2026-09-23T14:30:00+08:00"};
async function setup(page, {pending=true, empty=false, fail=false}={}) {
  const calls=[]; let decision=null;
  await page.addInitScript(()=>localStorage.setItem("osaLoggedIn","true"));
  await page.route("http://127.0.0.1:5000/**",route=>route.fulfill({json:{success:true,active:false,finished:false}}));
  await page.route("http://127.0.0.1:8000/**",async route=>{
    const request=route.request(), url=new URL(request.url());
    if(fail) return route.fulfill({status:503,json:{message:"Test service unavailable"}});
    if(url.pathname.endsWith("/review/")) { const body=request.postDataJSON(); calls.push(body); decision=body.decision; await new Promise(resolve=>setTimeout(resolve,150)); return route.fulfill({json:{success:true,message:decision==="DENY" ? "Gate stays closed." : "Opening authorized; waiting for acknowledgement."}}); }
    if(url.pathname.endsWith("/pending/")) return route.fulfill({json:{success:pending&&!decision&&!empty,inspection}});
    if(url.pathname.includes("/gate/attempts/")) return route.fulfill({json:{attempt_id:55,phase:decision==="DENY" ? "CLOSED" : decision ? "QUEUED" : "WAITING_OSA",outcome:decision==="DENY" ? "DENIED" : "PENDING",message:"Waiting for OSA",connected:true,gate_opened:false,entered:false,confirmation_status:decision==="YES" ? "CONFIRMED_ALLOW" : decision==="NO" ? "REJECTED" : decision==="DENY" ? "CONFIRMED_DENY" : "PENDING"}});
    if(url.pathname.endsWith("/login/")) return route.fulfill({json:{success:true}});
    if(url.pathname.endsWith("/scan/")) return route.fulfill({json:{success:true,student:{id:"TEST-1",name:students[0].full_name,college:"SEA",photo:pixel},attempt_id:55,hardware_gate:true}});
    if(url.pathname.endsWith("/system-status/")) return route.fulfill({json:{arduino_connected:true,gate_ready:true,active_cycle:null,scans_today:12,entries_today:10,denied_today:2,smtp_configured:true,timezone:"Asia/Manila",recent_detections:empty ? [] : [{id:110,student_number:"TEST-1",name:students[0].full_name,ai_result:"VIOLATION",decision:"PENDING",detected_at:inspection.detected_at}]}});
    if(url.pathname.endsWith("/dashboard/")) return route.fulfill({json:{students_today:10,total_violations:5,violations_today:1,college_chart:empty ? [] : [{college:"SEA",violations:5}],compliance_chart:[{name:"Compliant (No Violation)",value:11},{name:"With Violation",value:1}],recent_logs:empty ? [] : [{studentNumber:"TEST-1",name:students[0].full_name,college:"SEA",status:"With Violation",time:inspection.detected_at}]}});
    if(url.pathname.includes("/records/")) return route.fulfill({json:{records:empty ? [] : records,total:empty ? 0 : 1,schools:["SEA","SOC"],school:"SEA"}});
    if(url.pathname.includes("/audit/")) return route.fulfill({json:{results:empty || url.searchParams.get("q")==="missing" ? [] : [{id:55,student_number:"TEST-1",name:students[0].full_name,college:"SEA",scan_time:inspection.detected_at,ai_result:"VIOLATION",osa_decision:"CONFIRMED_DENY",gate_phase:"CLOSED",gate_event:"OSA denied entry",outcome:"DENIED",gate_opened:false,entered:false}],page:1,pages:1,total:empty ? 0 : 1,entered_total:0}});
    if(url.pathname.includes("/notifications/")) return route.fulfill({json:{results:empty || url.searchParams.get("q")==="missing" ? [] : [{id:4,student_number:"TEST-1",name:students[0].full_name,email:students[0].email,violation:records[0].violationType,total_minor_offenses:5,equivalent_major_offenses:1,created_at:inspection.detected_at,sent_at:inspection.detected_at,status:"SENT",error:""}],page:1,pages:1,total:empty ? 0 : 1}});
    return route.fulfill({json:empty ? [] : students});
  });
  return calls;
}
const routes=["/dashboard","/chatbot","/students","/students/TEST-1","/records","/records/sea","/scan-history","/email-notifications","/settings","/osa","/"];
for(const width of [1440,1366,1024,768,430,375]) {
 test(`all routes fit ${width}px with valid IDs`,async({page},info)=>{
  const errors=[];page.on("pageerror",error=>errors.push(error.message));await setup(page);await page.setViewportSize({width,height:900});
  for(const path of routes) {
   await page.goto(path);await expect(page.locator("h1")).toBeVisible();await page.waitForTimeout(100);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),path).toBe(true);
   const ids=await page.locator("[id]").evaluateAll(nodes=>nodes.map(node=>node.id));expect(new Set(ids).size, path).toBe(ids.length);
   expect(await page.locator("[aria-labelledby],[aria-controls],label[for]").evaluateAll(nodes=>nodes.flatMap(node=>[node.getAttribute("aria-labelledby"),node.getAttribute("aria-controls"),node.getAttribute("for")].filter(Boolean).flatMap(value=>value.split(" ")).filter(id=>!document.getElementById(id)))),path).toEqual([]);
   if(path==="/chatbot") {await expect(page.locator("#btn-confirm-deny")).toBeVisible();if(width===1440||width===375) await page.screenshot({path:info.outputPath(`review-${width}.png`),fullPage:true});}
   if(path==="/dashboard"&&width===1440) await page.screenshot({path:info.outputPath("dashboard-1440.png"),fullPage:true});
  }
  expect(errors).toEqual([]);
 });
}
for(const [button,decision] of [["btn-confirm-allow","YES"],["btn-no-violation","NO"],["btn-confirm-deny","DENY"]]) {
 test(`OSA ${decision} modal submits once with exact inspection`,async({page})=>{
  const calls=await setup(page);await page.goto("/chatbot");await page.locator(`#${button}`).click();const modal=page.getByRole("dialog");await expect(modal).toBeVisible();expect(calls).toHaveLength(0);
  await modal.getByRole("button",{name:"Cancel",exact:true}).click();expect(calls).toHaveLength(0);await page.locator(`#${button}`).click();
  if(decision==="DENY") await expect(modal).toContainText("No official offense is created");
  await modal.getByRole("button",{name:"Submit decision"}).click();await expect(modal.getByRole("button",{name:"Submitting"})).toBeDisabled();await expect(modal).not.toBeVisible();expect(calls).toEqual([{inspection_id:110,decision}]);await expect(page.locator("#review-result-toast")).toBeVisible();
 });
}
test("students search, filters, pagination and profile",async({page})=>{
 await setup(page);await page.goto("/students");await page.getByLabel("Search students").fill("missing");await expect(page.getByText("No students match")).toBeVisible();await page.getByLabel("Search students").fill("");await page.getByRole("button",{name:"Next",exact:true}).click();await expect(page.getByText("Page 2 of 2",{exact:false})).toBeVisible();await page.getByLabel("School",{exact:true}).selectOption("SOC");await expect(page.getByText("Page 1 of 1",{exact:false})).toBeVisible();await page.getByLabel("School",{exact:true}).selectOption("");await page.getByLabel("Official history").selectOption("recorded");await page.getByRole("link",{name:/View profile of Alexandra/}).click();await expect(page.getByRole("heading",{name:"Identity & contact information"})).toBeVisible();
});
test("records filters and exact evidence dialog keyboard close",async({page})=>{
 await setup(page);await page.goto("/records");await page.getByLabel("Search official records").fill("missing");await expect(page.getByText("No official records match")).toBeVisible();await page.getByLabel("Search official records").fill("");await page.getByLabel("Date (Manila)",{exact:true}).fill("2026-09-24");await expect(page.getByText("No official records match")).toBeVisible();await page.getByLabel("Date (Manila)",{exact:true}).fill("");await page.getByLabel("Violation",{exact:true}).selectOption(records[0].violationType);await page.getByRole("button",{name:students[0].full_name,exact:true}).click();const modal=page.getByRole("dialog");await expect(modal).toBeVisible();await expect(modal.locator("img")).toHaveAttribute("src",pixel);await page.keyboard.press("Escape");await expect(modal).not.toBeVisible();await expect(page.getByRole("button",{name:students[0].full_name,exact:true})).toBeFocused();
});
test("mobile navigation, account dropdown and logout",async({page})=>{
 await setup(page);await page.setViewportSize({width:375,height:812});await page.goto("/dashboard");await page.getByRole("button",{name:"Open navigation"}).click();await expect(page.getByRole("dialog")).toBeVisible();await page.getByRole("dialog").getByRole("link",{name:"Students",exact:true}).click();await expect(page).toHaveURL(/students$/);await expect(page.getByRole("dialog")).not.toBeVisible();await page.locator(".account-menu summary").click();await page.locator(".account-dropdown").getByRole("button",{name:"Logout"}).click();await expect(page).toHaveURL(/osa$/);
});
test("desktop sidebar resizes content and all navigation items work",async({page})=>{
 await setup(page);await page.setViewportSize({width:1440,height:900});await page.goto("/dashboard");const before=await page.locator("#main-content").boundingBox();await page.getByRole("button",{name:"Collapse navigation"}).click();const after=await page.locator("#main-content").boundingBox();expect(after.width).toBeGreaterThan(before.width);await page.getByRole("button",{name:"Expand navigation"}).click();
 for(const [name,path] of [["Live Detection","/chatbot"],["Students","/students"],["Violation Records","/records"],["Entry and Audit Logs","/scan-history"],["Email Notifications","/email-notifications"],["System Settings","/settings"],["Dashboard","/dashboard"]]) {await page.locator("#desktop-navigation").getByRole("link",{name,exact:true}).click();await expect(page).toHaveURL(new RegExp(path+"$"));}
});
test("login form submits original credentials fields",async({page})=>{
 await setup(page);await page.goto("/osa");await page.getByLabel("Email address").fill("osa@example.test");await page.getByLabel("Password",{exact:true}).fill("test-only");const request=page.waitForRequest(req=>req.url().endsWith("/login/"));await page.getByRole("button",{name:"Sign in",exact:true}).click();expect((await request).postDataJSON()).toEqual({email:"osa@example.test",password:"test-only"});await expect(page).toHaveURL(/dashboard$/);
});
test("audit and email searches and filters send supported parameters",async({page})=>{
 await setup(page);await page.goto("/scan-history");await page.getByLabel("Passage outcome").selectOption("DENIED");await page.getByLabel("Search audit logs").fill("missing");await expect(page.getByText("No matching attempts")).toBeVisible();await page.goto("/email-notifications");await page.getByLabel("Delivery status").selectOption("SENT");await page.getByLabel("Search notifications").fill("missing");await expect(page.getByText("No matching email notices")).toBeVisible();await expect(page.getByRole("button",{name:/resend/i})).toHaveCount(0);
});
test("empty states do not fabricate rows or rainy-day controls",async({page})=>{
 await setup(page,{empty:true});for(const path of ["/students","/records","/scan-history","/email-notifications","/chatbot"]) {await page.goto(path);await expect(page.locator(".empty-state").first()).toBeVisible();}await page.goto("/settings");await expect(page.getByText("Not implemented",{exact:true})).toBeVisible();await expect(page.getByRole("switch")).toHaveCount(0);
});
test("API failures show readable error states",async({page})=>{
 await setup(page,{fail:true});for(const path of ["/dashboard","/students","/records","/scan-history","/email-notifications","/chatbot"]) {await page.goto(path);await expect(page.getByRole("alert").first()).toBeVisible();}
});
test("scanner starts existing camera with exact attempt and does not authorize entry",async({page})=>{
 await setup(page);await page.goto("/");const cameraStart=page.waitForRequest(request=>request.url().endsWith("/start-camera"));await page.keyboard.type("12345");await page.keyboard.press("Enter");expect((await cameraStart).postDataJSON()).toEqual({student_number:"TEST-1",attempt_id:55});await expect(page.getByRole("heading",{name:students[0].full_name})).toBeVisible();await expect(page.getByText("Gate closed. Waiting for AI inspection and OSA decision.")).toBeVisible();
});

test("mobile dialogs fit, contain focus, and restore the opener",async({page})=>{
 await setup(page);
 for(const width of [375,430,768,1440]) {
  await page.setViewportSize({width,height:740});await page.goto("/chatbot");await page.locator("#btn-confirm-deny").click();const modal=page.getByRole("dialog");await expect(modal).toBeVisible();
  const box=await modal.boundingBox();expect(box.width).toBeLessThanOrEqual(width);expect(box.y).toBeGreaterThanOrEqual(0);expect(box.y+box.height).toBeLessThanOrEqual(741);
  for(let i=0;i<8;i++) {await page.keyboard.press("Tab");expect(await modal.evaluate(node=>node.contains(document.activeElement))).toBe(true);}
  await page.keyboard.press("Escape");await expect(page.locator("#btn-confirm-deny")).toBeFocused();
  await page.goto("/records");await page.getByRole("button",{name:students[0].full_name,exact:true}).click();await expect(page.getByRole("dialog")).toBeVisible();const evidenceBox=await page.getByRole("dialog").boundingBox();expect(evidenceBox.width).toBeLessThanOrEqual(width);expect(evidenceBox.y+evidenceBox.height).toBeLessThanOrEqual(741);await page.keyboard.press("Escape");
 }
});
test("review failure keeps the decision recoverable and evidence absence is explicit",async({page})=>{
 await setup(page);await page.route("**/ai-inspection/review/",route=>route.fulfill({status:409,json:{success:false,message:"Gate is offline. Decision not saved."}}));await page.goto("/chatbot");await page.locator("#btn-confirm-allow").click();await page.getByRole("button",{name:"Submit decision"}).click();await expect(page.getByRole("dialog").getByRole("alert")).toContainText("Gate is offline");await expect(page.getByRole("button",{name:"Submit decision"})).toBeEnabled();await page.keyboard.press("Escape");
 await page.route("**/api/students/records/",route=>route.fulfill({json:{records:[{...records[0],evidence_image:null}],schools:["SEA"],total:1}}));await page.goto("/records");await page.getByRole("button",{name:students[0].full_name,exact:true}).click();await expect(page.getByRole("dialog")).toContainText("No evidence image available.");
});
test("loading state is visible while data is pending",async({page})=>{
 await setup(page);await page.route("**/api/students/",async route=>{await new Promise(resolve=>setTimeout(resolve,700));await route.fulfill({json:students});});await page.goto("/students");await expect(page.getByRole("status")).toContainText("Loading records");await expect(page.getByRole("link",{name:/View profile of Alexandra/})).toBeVisible();
});
