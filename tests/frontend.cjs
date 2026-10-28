const {test,before,after,beforeEach}=require('node:test');
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const http=require('node:http');
const fs=require('node:fs/promises');
const path=require('node:path');
let server,browser,page,url;
const root=path.resolve(__dirname,'..');
before(async()=>{
  server=http.createServer(async(req,res)=>{
    const relative=req.url==='/'?'dev/index.html':decodeURIComponent(req.url.split('?')[0]).slice(1);
    const file=path.resolve(root,relative);
    if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
    try{const data=await fs.readFile(file);res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.html')?'text/html':'application/octet-stream');res.end(data);}catch{res.writeHead(404);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({headless:true,args:['--no-sandbox'],...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH}:{})});
});
after(async()=>{await browser?.close();await new Promise(resolve=>server?.close(resolve));});
beforeEach(async()=>{await page?.close();page=await browser.newPage({viewport:{width:1440,height:1100}});await page.goto(url);await page.locator('room-comfort-card').first().waitFor();});
const salon=()=>page.locator('room-comfort-card').filter({has:page.getByRole('heading',{name:'Salon',exact:true})});
test('all configured rooms appear with real controls',async()=>{
  assert.equal(await page.locator('room-comfort-card').count(),3);
  assert.equal(await salon().getByRole('button',{name:'Heat boost',exact:true}).count(),1);
  assert.equal(await salon().getByRole('slider',{name:'Target temperature'}).inputValue(),'21.5');
});
test('temperature plus and minus use the room climate service',async()=>{
  await salon().getByRole('button',{name:'Target temperature +',exact:true}).click();
  assert.equal(await salon().getByRole('slider').inputValue(),'22');
  const call=await page.evaluate(()=>demo.calls.at(-1));
  assert.deepEqual(call,{domain:'climate',service:'set_temperature',data:{temperature:22},target:{entity_id:'climate.salon'}});
  await salon().getByRole('button',{name:'Target temperature −',exact:true}).click();
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
});
test('boost starts, counts down, then cancels without changing the target',async()=>{
  await salon().getByRole('button',{name:'Heat boost',exact:true}).click();
  assert.equal(await salon().locator('[data-countdown]').count(),1);
  assert.match(await salon().locator('[data-countdown]').textContent(),/^19:5\d|20:00$/);
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
  await salon().getByRole('button',{name:'Cancel boost',exact:true}).click();
  assert.equal(await salon().locator('[data-countdown]').count(),0);
  assert.equal(await page.evaluate(()=>demo.states['climate.salon'].attributes.desired_ac_mode),'off');
});
test('mode buttons call climate set_hvac_mode',async()=>{
  await salon().getByRole('button',{name:'Cool',exact:true}).click();
  assert.equal(await page.evaluate(()=>demo.states['climate.salon'].state),'cool');
  await salon().getByRole('button',{name:'Off',exact:true}).click();
  assert.equal(await page.evaluate(()=>demo.states['climate.salon'].state),'off');
});
test('Cool stays visible with setup guidance in a radiator-only room',async()=>{
  const room=page.locator('room-comfort-card').filter({has:page.getByRole('heading',{name:'Biuro',exact:true})});
  const cool=room.getByRole('button',{name:'Cool',exact:true});
  assert.equal(await cool.isVisible(),true);
  assert.equal(await cool.isDisabled(),true);
  assert.match(await room.locator(".source-hint").first().textContent(),/Assign an air conditioner/);
});
test('cooling targets are separate and selected when switching to Cool',async()=>{
  const input=salon().getByRole('spinbutton',{name:'home cooling temperature',exact:true});
  await input.fill('25');await input.press('Tab');
  await page.waitForFunction(()=>demo.calls.at(-1)?.domain==='number');
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
  await salon().getByRole('button',{name:'Cool',exact:true}).click();
  assert.equal(await salon().getByRole('slider').inputValue(),'25');
  assert.equal(await salon().locator('.pid-demand').count(),0);
  await salon().getByRole('button',{name:'Heat',exact:true}).click();
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
});
test('return mode selector uses the HA select service and cools on return',async()=>{
  await salon().getByRole('combobox',{name:'Coming home mode',exact:true}).selectOption('cool');
  const call=await page.evaluate(()=>demo.calls.at(-1));
  assert.deepEqual(call,{domain:'select',service:'select_option',data:{option:'cool'},target:{entity_id:'select.salon_coming_home_mode'}});
  await page.locator('room-comfort-home-controls').getByRole('switch',{name:'Prepare for my return',exact:true}).click();
  assert.equal(await page.evaluate(()=>demo.states['climate.salon'].state),'cool');
  assert.equal(await salon().getByRole('slider').inputValue(),'24');
});
test('automation help has blueprint and setup links',async()=>{
  const help=page.locator('room-comfort-home-controls .automation-help');
  await help.locator('summary').click();
  assert.equal(await help.getByRole('link',{name:/Open HA blueprints/}).getAttribute('href'),'/config/blueprint/dashboard');
  assert.match(await help.getByRole('link',{name:/Setup guide/}).getAttribute('href'),/docs\/automations.md$/);
});
test('observe mode shows planned outputs and live control can be enabled',async()=>{
  await page.locator('#observe').click();
  assert.match(await salon().locator('.observe').textContent(),/Controller demand/);
  await salon().getByRole('switch',{name:'Enable control',exact:true}).click();
  assert.equal(await salon().getByRole('switch',{name:'Disable control',exact:true}).getAttribute('aria-checked'),'true');
});
test('offline AC disables cooling and boost and shows a useful fault',async()=>{
  await page.locator('#fault').click();
  assert.equal(await salon().getByRole('button',{name:'Heat boost',exact:true}).isDisabled(),true);
  assert.equal(await salon().getByRole('button',{name:'Cool',exact:true}).isDisabled(),true);
  assert.match(await salon().locator('.messages').textContent(),/AC unavailable/);
  await page.getByRole('button',{name:'Needs attention',exact:true}).click();
  assert.equal(await page.locator('room-comfort-card').count(),1);
});
test('sensor faults do not display a fabricated room temperature',async()=>{
  await page.evaluate(()=>{demo.replace('climate.salon',null,{current_temperature:null,demand_status:'sensor_unavailable',controller_status:'sensor_unavailable'});demo.refresh();});
  assert.equal(await salon().getByRole('button',{name:'Heat boost',exact:true}).isDisabled(),true);
  assert.match(await salon().locator('.reading-value').textContent(),/—/);
  assert.match(await salon().locator('.messages').textContent(),/sensor unavailable or stale/);
});
test('service errors are visible and controls recover',async()=>{
  await page.evaluate(()=>demo.failNext());
  await salon().getByRole('button',{name:'Heat boost',exact:true}).click();
  assert.match(await salon().getByRole('alert').textContent(),/Device did not respond/);
  assert.equal(await salon().getByRole('button',{name:'Heat boost',exact:true}).isEnabled(),true);
});
test('device details use HA more-info events',async()=>{
  await salon().locator('summary').click();
  await salon().getByRole('button',{name:/Radiator · balcony/}).click();
  assert.match(await page.locator('#toast').textContent(),/climate.salon_radiator_1/);
});
test('filters and search select the correct rooms',async()=>{
  await page.getByRole('button',{name:'Cooling',exact:true}).click();
  assert.equal(await page.locator('room-comfort-card').count(),1);
  assert.equal(await page.getByRole('heading',{name:'Sypialnia',exact:true}).count(),1);
  await page.getByRole('button',{name:'All rooms',exact:true}).click();
  await page.getByRole('searchbox').fill('biuro');
  assert.equal(await page.locator('room-comfort-card').count(),1);
  assert.equal(await page.getByRole('heading',{name:'Biuro',exact:true}).count(),1);
  await page.getByRole('searchbox').fill('does not exist');
  assert.match(await page.locator('.no-matches').textContent(),/No rooms match/);
});
test('HTML from entity names and service errors is escaped',async()=>{
  await page.evaluate(()=>{demo.replace('climate.salon',null,{room_name:'<img src=x onerror="window.injected=true">'});demo.refresh();});
  assert.equal(await page.locator('room-comfort-card img').count(),0);
  assert.equal(await page.evaluate(()=>window.injected),undefined);
});
test('graphical card editor emits config-changed',async()=>{
  await page.evaluate(()=>{const editor=document.createElement('room-comfort-card-editor');editor.setConfig({entity:'climate.salon'});editor.hass=demo.hass;editor.addEventListener('config-changed',e=>window.editorConfig=e.detail.config);document.body.append(editor);});
  const editor=page.locator('room-comfort-card-editor');
  await editor.locator('select').selectOption('climate.biuro');
  assert.equal(await page.evaluate(()=>window.editorConfig.entity),'climate.biuro');
});
test('Polish labels and dark theme render',async()=>{
  await page.locator('#language').selectOption('pl');
  assert.equal(await page.getByRole('button',{name:'Dogrzewanie',exact:true}).count(),1);
  await page.locator('#theme').click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
});
test('missing room and empty overview have setup states',async()=>{
  await page.evaluate(()=>{const card=document.createElement('room-comfort-card');card.setConfig({entity:'climate.missing'});card.hass=demo.hass;document.body.append(card);for(const id of Object.keys(demo.states)){if(id==='climate.salon'||id==='climate.biuro'||id==='climate.sypialnia')delete demo.states[id];}demo.refresh();});
  assert.match(await page.locator('room-comfort-overview .empty').textContent(),/Make your first room/);
  assert.match(await page.locator('body > room-comfort-card .empty').textContent(),/Choose a Room Comfort/);
});
test('desktop and mobile layouts fit without horizontal scrolling',async()=>{
  await fs.mkdir(path.join(root,'docs/images'),{recursive:true});
  await page.screenshot({path:path.join(root,'docs/images/desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  assert.equal(overflow,false);
  await page.screenshot({path:path.join(root,'docs/images/mobile.png'),fullPage:true});
  await page.locator('#theme').click();
  await page.setViewportSize({width:1440,height:1100});
  await page.screenshot({path:path.join(root,'docs/images/dark.png'),fullPage:true});
});

test('vacation is an explicit household switch and applies configured targets',async()=>{
  const home=page.locator('room-comfort-home-controls');
  await home.getByRole('switch',{name:'Vacation',exact:true}).click();
  assert.equal(await home.getByRole('switch',{name:'Vacation',exact:true}).getAttribute('aria-checked'),'true');
  assert.equal(await salon().getByRole('slider').inputValue(),'17');
  assert.match(await home.locator('.profile').textContent(),/Vacation/);
});

test('coming-home switch exits vacation, selects Home targets and shows timeout',async()=>{
  const home=page.locator('room-comfort-home-controls');
  await home.getByRole('switch',{name:'Vacation',exact:true}).click();
  await home.getByRole('switch',{name:'Prepare for my return',exact:true}).click();
  assert.equal(await home.getByRole('switch',{name:'Vacation',exact:true}).getAttribute('aria-checked'),'false');
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
  assert.equal(await home.locator('[data-prewarm-countdown]').count(),1);
  assert.match(await home.locator('.prewarm-state').textContent(),/Heating or cooling to Home targets/);
});

test('prewarm-ready state remains an active switch',async()=>{
  const home=page.locator('room-comfort-home-controls');
  await home.getByRole('switch',{name:'Prepare for my return',exact:true}).click();
  await page.evaluate(()=>{demo.replace('sensor.home_mode',null,{prewarm_ready:true});demo.refresh();});
  assert.match(await home.locator('.prewarm-state').textContent(),/Ready — holding/);
  assert.equal(await home.getByRole('switch',{name:'Prepare for my return',exact:true}).getAttribute('aria-checked'),'true');
});

test('room profile temperatures are editable through HA number entities',async()=>{
  const input=salon().getByRole('spinbutton',{name:'away temperature',exact:true});
  await input.fill('19.5');
  await input.press('Tab');
  await page.waitForFunction(()=>demo.calls.at(-1)?.domain==='number');
  const call=await page.evaluate(()=>demo.calls.at(-1));
  assert.equal(call.service,'set_value');
  assert.equal(call.data.value,19.5);
  assert.equal(call.target.entity_id,'number.salon_away_temperature');
  assert.equal(await salon().getByRole('slider').inputValue(),'21.5');
});

test('PID demand is explicitly calculated demand rather than valve opening',async()=>{
  assert.match(await salon().locator('.pid-demand').textContent(),/PID · heat demand/);
  assert.equal(await salon().locator('meter').getAttribute('value'),'42');
});

test('presence chips show individual membership and explain the all-away rule',async()=>{
  const home=page.locator('room-comfort-home-controls');
  assert.match(await home.locator('.trackers').textContent(),/Dominik · inside/);
  assert.match(await home.locator('.home-bottom').textContent(),/every tracker outside/);
});

