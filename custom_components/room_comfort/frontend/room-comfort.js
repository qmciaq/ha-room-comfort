/* Room Comfort 0.5.0. Bundled, dependency-free Home Assistant web components. */
(() => {
  "use strict";
  const VERSION = "0.5.0";
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const finite = value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
  const unavailable = entity => !entity || ["unavailable", "unknown"].includes(entity.state);
  const roomEntities = hass => Object.values(hass?.states || {}).filter(e => e.entity_id.startsWith("climate.") && e.attributes.room_comfort === true);
  const fire = (node, type, detail = {}) => node.dispatchEvent(new CustomEvent(type, {detail, bubbles: true, composed: true}));
  const paths = {
    heat: '<path d="M12 3c1 5-4 6-4 10a4 4 0 0 0 8 0c0-2-1-3-1-3s0 3-2 3c2-5-1-10-1-10Z"/>',
    cool: '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9 5l3 3 3-3M9 19l3-3 3 3M4.4 11l4-1-1-4M19.6 13l-4 1 1 4M4.4 13l4 1-1 4M19.6 11l-4-1 1-4"/>',
    radiator: '<rect x="4" y="5" width="4" height="14" rx="2"/><rect x="10" y="5" width="4" height="14" rx="2"/><rect x="16" y="5" width="4" height="14" rx="2"/><path d="M2 9h2m16 0h2M2 15h2m16 0h2"/>',
    ac: '<rect x="3" y="4" width="18" height="9" rx="2"/><path d="M6 10h12M7 17c0 2-2 2-2 4m7-4v4m5-4c0 2 2 2 2 4"/>',
    off: '<path d="M12 3v8m-5-6a8 8 0 1 0 10 0"/>',
    bolt: '<path d="m13 2-9 12h7l-1 8 10-13h-7l1-7Z"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    room: '<path d="m3 11 9-8 9 8M5 10v10h14V10M9 20v-7h6v7"/>',
    sensor: '<path d="M9 14V5a3 3 0 0 1 6 0v9a5 5 0 1 1-6 0Zm3-6v10"/>',
    arrow: '<path d="m9 5 7 7-7 7"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v1"/>',
    alert: '<path d="m12 3 10 18H2L12 3ZM12 9v5m0 3v1"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  };
  const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">${paths[name] || paths.room}</svg>`;
  const text = {
    en: {
      room: "Room", current: "Room temperature", target: "Target temperature", setTo: "SET TO", heat: "Heat", cool: "Cool", off: "Off",
      source: "HEATING SOURCE", radiators: "Radiators", radiator: "Radiator", ac: "Air conditioner", boost: "Heat boost", cancel: "Cancel boost",
      boostHint: "AC helps the radiators warm the room, then switches off.", boostEnds: "Until target or", minute: "min", remaining: "remaining",
      devices: "Devices & room sensor", sensor: "Room sensor", history: "View temperature history", details: "Room details", live: "Live control",
      observe: "Observe only", observeHint: "Decisions are shown below. Devices stay under their existing controls.", enable: "Enable control", disable: "Disable control",
      demand: "Controller demand", waiting: "Waiting for Home Assistant…", pending: "Sending command…", missing: "This room thermostat is not available.",
      noEntity: "Choose a Room Comfort thermostat in the card editor.", offline: "Unavailable", online: "Online", active: "Active", standby: "Standby", targetShort: "Target",
      enableHint: "Enabling takes control of the assigned devices. Radiator heads and AC use demand setpoints controlled by the room sensor.",
      title: "Room Comfort", subtitle: "A comfortable temperature, room by room.", overview: "YOUR HOME", all: "All rooms", heating: "Heating", cooling: "Cooling", attention: "Needs attention",
      search: "Find a room", add: "Add room", settings: "Room settings", noRooms: "Make your first room comfortable.", noRoomsHint: "Connect a room sensor, its radiators and an optional air conditioner. You get one temperature control for the whole room.",
      noMatches: "No rooms match this view.", reset: "Show all rooms", roomCount: "Rooms", control: "In control", preview: "Preview", showDevices: "Show device details", showSensor: "Show room sensor", entity: "Room thermostat", name: "Display name (optional)",
      noSelection: "Select a room", failed: "Command failed. Please try again.", unavailableAC: "AC unavailable · boost and cooling are blocked", sensorFault: "Room sensor unavailable or stale · temperature control paused",
      activeIntent: "Requested mode; actual heat output is not measured.", window: "Window", sensorRead: "Sensor reading", controlUnavailable: "Control switch is unavailable.",
    },
    pl: {
      room: "Pokój", current: "Temperatura w pokoju", target: "Temperatura docelowa", setTo: "USTAWIONO", heat: "Grzanie", cool: "Chłodzenie", off: "Wyłącz",
      source: "ŹRÓDŁO OGRZEWANIA", radiators: "Grzejniki", radiator: "Grzejnik", ac: "Klimatyzator", boost: "Dogrzewanie", cancel: "Zakończ dogrzewanie",
      boostHint: "Klimatyzator pomaga grzejnikom ogrzać pokój, a potem się wyłącza.", boostEnds: "Do osiągnięcia celu lub", minute: "min", remaining: "pozostało",
      devices: "Urządzenia i czujnik pokoju", sensor: "Czujnik pokoju", history: "Pokaż historię temperatury", details: "Szczegóły pokoju", live: "Sterowanie aktywne",
      observe: "Tylko podgląd", observeHint: "Poniżej widać decyzje regulatora. Urządzenia zachowują dotychczasowe sterowanie.", enable: "Włącz sterowanie", disable: "Wyłącz sterowanie",
      demand: "Zapotrzebowanie regulatora", waiting: "Oczekiwanie na Home Assistant…", pending: "Wysyłanie polecenia…", missing: "Termostat tego pokoju jest niedostępny.",
      noEntity: "Wybierz termostat Room Comfort w edytorze karty.", offline: "Niedostępne", online: "Dostępne", active: "Aktywne", standby: "Gotowe", targetShort: "Cel",
      enableHint: "Włączenie przejmuje sterowanie wybranymi urządzeniami. Grzejniki i klimatyzator otrzymują temperatury robocze według czujnika pokojowego.",
      title: "Room Comfort", subtitle: "Komfortowa temperatura w każdym pokoju.", overview: "TWÓJ DOM", all: "Wszystkie", heating: "Grzanie", cooling: "Chłodzenie", attention: "Wymagają uwagi",
      search: "Znajdź pokój", add: "Dodaj pokój", settings: "Ustawienia pokojów", noRooms: "Zacznij od pierwszego pokoju.", noRoomsHint: "Połącz czujnik temperatury, grzejniki i opcjonalny klimatyzator. Cały pokój będzie miał jeden regulator temperatury.",
      noMatches: "Brak pokojów w tym widoku.", reset: "Pokaż wszystkie", roomCount: "Pokoje", control: "Sterowanie", preview: "Podgląd", showDevices: "Pokaż szczegóły urządzeń", showSensor: "Pokaż czujnik pokoju", entity: "Termostat pokojowy", name: "Wyświetlana nazwa (opcjonalnie)",
      noSelection: "Wybierz pokój", failed: "Nie udało się wykonać polecenia. Spróbuj ponownie.", unavailableAC: "Klimatyzator niedostępny · dogrzewanie i chłodzenie zablokowane", sensorFault: "Czujnik niedostępny lub nieaktualny · regulacja wstrzymana",
      activeIntent: "Żądany tryb; rzeczywista moc grzania nie jest mierzona.", window: "Okno", sensorRead: "Odczyt czujnika", controlUnavailable: "Przełącznik sterowania jest niedostępny.",
    },
  };
  const statusTexts = {
    en: {outdoor_heat_blocked:"Heating paused · warm outdoors",outdoor_cool_blocked:"Cooling paused · cool outdoors",outdoor_unavailable:"Outdoor sensor unavailable or stale",room_unoccupied:"Room empty · temperature control paused",off:"Room is off", idle:"At your temperature", heating:"Heating with radiators", boosting:"Radiators + AC heat boost", cooling:"Cooling with AC", observe_only:"Observe only", sensor_unavailable:"Room sensor unavailable", window_open:"Window open or unavailable", ac_cooldown:"Waiting for AC cooldown", waiting_for_off:"Waiting for device to stop", waiting_for_ac_off:"Waiting for AC to stop", waiting_for_radiators_off:"Waiting for radiators to stop", waiting_for_device:"Waiting for device feedback", stopping_devices:"Stopping devices before releasing control", device_error:"A device needs attention", device_unavailable:"A device is unavailable", invalid_mode:"Unsupported room mode"},
    pl: {outdoor_heat_blocked:"Grzanie wstrzymane · ciepło na zewnątrz",outdoor_cool_blocked:"Chłodzenie wstrzymane · chłodno na zewnątrz",outdoor_unavailable:"Czujnik zewnętrzny niedostępny lub nieaktualny",room_unoccupied:"Pusty pokój · regulacja wstrzymana",off:"Pokój wyłączony", idle:"Temperatura osiągnięta", heating:"Grzanie grzejnikami", boosting:"Grzejniki + dogrzewanie klimatyzatorem", cooling:"Chłodzenie klimatyzatorem", observe_only:"Tylko podgląd", sensor_unavailable:"Czujnik pokoju niedostępny", window_open:"Okno otwarte lub czujnik niedostępny", ac_cooldown:"Przerwa przed startem klimatyzatora", waiting_for_off:"Oczekiwanie na wyłączenie urządzenia", waiting_for_ac_off:"Oczekiwanie na wyłączenie klimatyzatora", waiting_for_radiators_off:"Oczekiwanie na wyłączenie grzejników", waiting_for_device:"Oczekiwanie na odpowiedź urządzenia", stopping_devices:"Wyłączanie urządzeń przed zakończeniem sterowania", device_error:"Urządzenie wymaga uwagi", device_unavailable:"Urządzenie niedostępne", invalid_mode:"Nieobsługiwany tryb pokoju"},
  };
  function lang(hass, config) { return (config?.language || hass?.language || hass?.locale?.language || "en").startsWith("pl") ? "pl" : "en"; }
  function formatTemp(value, locale = "en") { return finite(value) ? new Intl.NumberFormat(locale, {maximumFractionDigits:1, minimumFractionDigits:1}).format(Number(value)) : "—"; }
  function tone(entity) { return entity?.state === "cool" ? "cool" : entity?.state === "heat" ? "heat" : "off"; }
  function warning(entity, hass) {
    const a = entity?.attributes || {};
    return unavailable(entity) || ["sensor_unavailable","outdoor_unavailable"].includes(a.demand_status) || Object.keys(a.device_errors || {}).length > 0 ||
      [...(a.radiators || []), a.air_conditioner, ...(a.windows || [])].filter(Boolean).some(id => unavailable(hass?.states[id]));
  }
  function conditionSummary(a, language) {
    const pl=language==='pl', parts=[];
    const settings=a.outdoor_settings;
    if(settings?.outdoor_enabled)parts.push(`${pl?'Na zewnątrz':'Outside'} ${formatTemp(a.outdoor_temperature,language)}°C · ${pl?'Grzanie':'Heat'} < ${settings.outdoor_heat_below}°C · ${pl?'Chłodzenie':'Cool'} > ${settings.outdoor_cool_above}°C · ${a.outdoor_policy==='custom'?(pl?'własne':'room override'):(pl?'globalne':'global')}`);
    if(a.windows?.length)parts.push(a.window_pending?(pl?`Otwarte okno/drzwi · pauza po ${a.window_open_seconds} s`:`Door/window open · pause after ${a.window_open_seconds}s`):(pl?`Okna/drzwi · opóźnienie ${a.window_open_seconds}s`:`Doors/windows · ${a.window_open_seconds}s delay`));
    if(a.presence_sensors?.length){
      parts.push(a.room_occupied===true?(pl?'Obecność w pokoju':'Presence detected'):a.room_occupied===false?(pl?'Brak obecności':'No room presence'):(pl?'Obecność nieznana · komfort zachowany':'Presence unknown · keeping comfort'));
      parts.push(`${pl?'Pauza po':'Pause after'} ${a.pause_heat_when_empty?`${a.heat_absence_minutes}m ${pl?'grzanie':'heat'}`:''}${a.pause_heat_when_empty&&a.pause_cool_when_empty?' / ':''}${a.pause_cool_when_empty?`${a.cool_absence_minutes}m AC`:''}${!a.pause_heat_when_empty&&!a.pause_cool_when_empty?(pl?'wyłączona':'disabled'):''}`);
      if(a.home_profile==='prewarming')parts.push(pl?'Powrót pomija pauzę pustego pokoju':'Coming home bypasses empty-room pauses');
    }
    return parts.join(' · ');
  }
  const sharedStyles = `
    :host{display:block;font-family:var(--primary-font-family,Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif);color:var(--primary-text-color,#242924);--rc-line:var(--divider-color,#e8e9e4);--rc-muted:var(--secondary-text-color,#737b72);--rc-bg:var(--ha-card-background,var(--card-background-color,#fff));--rc-soft:color-mix(in srgb,var(--rc-bg) 94%,var(--primary-text-color,#293229) 6%);--rc-accent:#b65c31;--rc-tint:color-mix(in srgb,var(--rc-bg) 90%,var(--rc-accent) 10%);--rc-focus:#3482d9}
    *,*:before,*:after{box-sizing:border-box}button,input,select{font:inherit}button,a,input,select{-webkit-tap-highlight-color:transparent}button{cursor:pointer;color:inherit}button:disabled{cursor:default;opacity:.45}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible,select:focus-visible{outline:3px solid var(--rc-focus);outline-offset:3px}svg{width:21px;height:21px;flex:none;vertical-align:middle}button{min-height:44px}a{color:inherit;text-decoration:none}.muted{color:var(--rc-muted)}.eyebrow{font-size:10px;font-weight:700;letter-spacing:1.7px;text-transform:uppercase}.icon-button{display:inline-flex;justify-content:center;align-items:center;width:44px;height:44px;padding:0;border:1px solid var(--rc-line);background:transparent;border-radius:50%}.error{display:flex;gap:9px;border-radius:12px;padding:11px 13px;background:color-mix(in srgb,var(--rc-bg) 88%,#d88e34 12%);color:var(--primary-text-color,#634119);font-size:12px;line-height:1.5}.error svg{width:17px;height:17px;margin-top:1px}.primary{background:var(--primary-text-color,#293229);color:var(--rc-bg);padding:12px 19px;border:0;border-radius:11px;display:inline-flex;align-items:center;gap:9px;font-weight:600;font-size:13px}a.primary{min-height:44px}.small{font-size:12px}.empty{padding:32px;text-align:center}.empty svg{width:42px;height:42px;color:var(--rc-muted)}.empty h2{font-size:22px;font-weight:500;letter-spacing:-.6px}.empty p{color:var(--rc-muted);font-size:14px;line-height:1.7;max-width:460px;margin:12px auto 24px}@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}`;

  class RoomComfortCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({mode:"open"});
      this._config = {show_devices:true, show_sensor:true};
      this._busy = false;
      this._error = "";
      this._draft = null;
      this._details = false;
      this._tick = null;
      this.shadowRoot.addEventListener("click", e => this._click(e));
      this.shadowRoot.addEventListener("input", e => {
        if (e.target.dataset.action === "temperature") {
          this._dragging = true;
          this._draft = Number(e.target.value);
          const output = this.shadowRoot.querySelector("[data-target]");
          if (output) output.textContent = formatTemp(this._draft, this._language);
        }
      });
      this.shadowRoot.addEventListener("change", e => {
        if(e.target.dataset.returnMode){void this._service("select","select_option",e.target.dataset.returnMode,{option:e.target.value});return;}
        if(e.target.dataset.profileEntity){void this._service("number","set_value",e.target.dataset.profileEntity,{value:Number(e.target.value)});return;}
        if (e.target.dataset.action === "temperature") {
          this._dragging = false;
          void this._setTemperature(Number(e.target.value));
        }
      });
    }
    connectedCallback() {
      if (!this._tick) this._tick = setInterval(() => this._countdown(), 1000);
      this._render();
    }
    disconnectedCallback() { clearInterval(this._tick); this._tick = null; }
    setConfig(config) {
      if (!config.entity?.startsWith("climate.")) throw new Error("Room Comfort: select a room climate entity.");
      this._config = {show_devices:true, show_sensor:true, layout:this.defaultLayout || "full", ...config};
      this._render();
    }
    set hass(hass) {
      const old = this._hass;
      this._hass = hass;
      const state = hass.states[this._config.entity];
      if (this._draft !== null && Number(state?.attributes.temperature) === this._draft) this._draft = null;
      const a = state?.attributes || {};
      const relevant = [this._config.entity, a.room_sensor, a.control_switch, a.air_conditioner, ...(a.radiators || []), ...(a.windows || []), ...(a.presence_sensors || [])].filter(Boolean);
      if (!old || relevant.some(id => old.states[id] !== hass.states[id]) || old.language !== hass.language) {
        if (!this._dragging && !this.shadowRoot.activeElement?.dataset.profileEntity && !this.shadowRoot.activeElement?.dataset.returnMode) this._render();
      }
    }
    get hass() { return this._hass; }
    getCardSize() { return this._config.layout === "tile" ? 1 : this._config.layout === "compact" ? 3 : this._config.show_devices === false ? 6 : 8; }
    getGridOptions() { return {columns:this._config.layout && this._config.layout !== "full" ? 6 : 12, rows:"auto", min_columns:3}; }
    static getConfigElement() { return document.createElement("room-comfort-card-editor"); }
    static getStubConfig(hass) { return {entity:roomEntities(hass)[0]?.entity_id || "climate.choose_room", show_devices:true, show_sensor:true}; }
    _info(entityId) { if (entityId) fire(this, "hass-more-info", {entityId}); }
    async _service(domain, service, entityId, data = {}) {
      if (this._busy || !entityId) return;
      this._busy = true; this._error = ""; this._render();
      try {
        await this._hass.callService(domain, service, data, {entity_id:entityId});
      } catch (error) {
        this._error = error?.message || String(error) || text[this._language].failed;
        this._draft = null;
      } finally { this._busy = false; this._render(); }
    }
    async _setTemperature(value) {
      const entity = this._hass?.states[this._config.entity];
      if (!entity || this._busy || !Number.isFinite(value)) return;
      const a = entity.attributes;
      this._draft = Math.min(a.max_temp ?? 28, Math.max(a.min_temp ?? 16, value));
      await this._service("climate", "set_temperature", entity.entity_id, {temperature:this._draft});
    }
    _click(event) {
      const button = event.target.closest("[data-action]");
      if (!button || button.disabled) return;
      const action = button.dataset.action;
      const entity = this._hass?.states[this._config.entity];
      if (!entity) return;
      const a = entity.attributes;
      if (action === "info") return this._info(button.dataset.entity || entity.entity_id);
      if (action === "minus" || action === "plus") {
        const step = Number(a.target_temp_step || .5);
        const current = this._draft ?? Number(a.temperature);
        return void this._setTemperature(Math.round((current + (action === "plus" ? step : -step)) * 100) / 100);
      }
      if (action === "mode") return void this._service("climate", "set_hvac_mode", entity.entity_id, {hvac_mode:button.dataset.mode});
      if (action === "radiators") return void this._service("climate", "set_preset_mode", entity.entity_id, {preset_mode:"radiators"});
      if (action === "boost") return void this._service("climate", "set_preset_mode", entity.entity_id, {preset_mode:"boost"});
      if (action === "cancel") {
        if (a.cancel_boost_button) return void this._service("button", "press", a.cancel_boost_button);
        return void this._service("climate", "set_preset_mode", entity.entity_id, {preset_mode:"radiators"});
      }
      if (action === "control") return void this._service("switch", a.control_devices ? "turn_off" : "turn_on", a.control_switch);
    }
    _countdown() {
      const e = this._hass?.states[this._config.entity];
      const end = Number(e?.attributes.boost_ends_at || 0);
      const remaining = Math.max(0, Math.ceil(end - Date.now()/1000));
      const output = this.shadowRoot.querySelector("[data-countdown]");
      if (output) output.textContent = `${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,"0")}`;
    }
    _device(id, kind, t) {
      const e = this._hass.states[id];
      const a = e?.attributes || {};
      const bad = unavailable(e);
      const active = !bad && !["off", "idle"].includes(e.state);
      const stateName = bad ? t.offline : kind === "window" ? (e.state === "on" ? (this._language === "pl" ? "Otwarte" : "Open") : (this._language === "pl" ? "Zamknięte" : "Closed")) : kind === "presence" ? (e.state === "on" ? (this._language === "pl" ? "Obecność" : "Occupied") : (this._language === "pl" ? "Brak obecności" : "Clear")) : statusTexts[this._language][e.state] || ({heat:t.heat,cool:t.cool,auto:"Auto",off:t.off,on:t.active}[e.state] || e.state);
      return `<button class="device" data-action="info" data-entity="${escape(id)}" title="${escape(id)}">
        <span class="device-icon ${bad ? "bad" : active ? "running" : ""}">${icon(kind === "radiator" ? "radiator" : kind === "ac" ? "ac" : "sensor")}</span>
        <span class="device-copy"><span>${escape(a.friendly_name || id)}</span><small>${escape(kind === "radiator" ? t.radiator : kind === "ac" ? t.ac : kind === "presence" ? (this._language === "pl" ? "Obecność" : "Presence") : t.window)}</small></span>
        <span class="device-state ${bad ? "bad" : ""}"><i class="dot ${active ? "running" : ""}"></i>${escape(stateName)}</span>
      </button>`;
    }
    _renderCompact(entity) {
      const a=entity.attributes,t=text[this._language],pl=this._language==='pl';
      const unit=a.temperature_unit || this._hass.config?.unit_system?.temperature || '°C';
      const name=this._config.name||a.room_name||a.friendly_name;
      const status=statusTexts[this._language][a.controller_status]||a.controller_status;
      const details=conditionSummary(a,this._language);
      const shortDetails=[a.outdoor_settings?.outdoor_enabled?`${formatTemp(a.outdoor_temperature,this._language)}°C ${pl?'na zewnątrz':'outside'}`:'',a.presence_sensors?.length?(a.room_occupied===true?(pl?'Obecność':'Occupied'):a.room_occupied===false?(pl?'Pusto':'Empty'):(pl?'Obecność nieznana':'Presence unknown')):'',a.window_pending?(pl?'Timer okna':'Window timer'):'' ].filter(Boolean).join(' · ');
      const shortStatus=({heating:t.heating,cooling:t.cooling,boosting:t.boost,idle:pl?'Gotowe':'Idle',off:t.off})[a.controller_status] || (a.controller_status==='observe_only'?t.observe:(pl?'Wstrzymane':'Paused'));
      const canCool=Boolean(a.air_conditioner&&(a.hvac_modes||[]).includes('cool'));
      const coolBlocked=!canCool||unavailable(this._hass.states[a.air_conditioner])||!finite(a.current_temperature);
      const busy=this._busy?'disabled':'';
      const focusAction=this.shadowRoot.activeElement?.dataset.action;
      const style=`${sharedStyles}:host{min-width:0}.compact{background:var(--rc-bg);border:1px solid var(--rc-line);border-radius:16px;padding:16px;--rc-accent:${entity.state==='cool'?'#397e9b':entity.state==='heat'?'#b65c31':'#7b8478'}}.head{display:flex;align-items:center;justify-content:space-between;gap:8px}.name{font-size:14px;font-weight:600;min-width:0;overflow:hidden;text-overflow:ellipsis}.head .icon-button{width:32px;height:32px;min-height:32px;border:0;color:var(--rc-muted)}.readings{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;margin:12px 0}.current{font-size:26px;letter-spacing:-1px}.current small{font-size:11px;color:var(--rc-muted);letter-spacing:0}.target{display:flex;align-items:center;gap:5px;font-size:20px;font-variant-numeric:tabular-nums}.target .icon-button{width:34px;height:38px;min-height:44px;border:0}.target strong{min-width:42px;text-align:center;font-weight:500}.status{font-size:11px;color:var(--rc-accent);line-height:1.5;margin:8px 0}.modes{display:flex;gap:4px}.mode{flex:1;min-width:0;padding:7px 3px;border:1px solid var(--rc-line);border-radius:8px;background:transparent;color:var(--rc-muted);font-size:10px;display:flex;align-items:center;justify-content:center;gap:3px}.mode svg{width:14px;height:14px}.mode[aria-pressed=true]{background:var(--rc-tint);color:var(--rc-accent);border-color:var(--rc-accent)}.note{font-size:10px;color:var(--rc-muted);line-height:1.6;margin-top:9px}.bottom{display:flex;align-items:center;justify-content:space-between;margin-top:6px;gap:6px;font-size:10px;color:var(--rc-muted)}.bottom button{border:0;background:transparent;font-size:10px;color:inherit;padding:4px}.tile{padding:13px;width:100%;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:8px;text-align:left}.tile>svg{display:none}.tile svg{color:var(--rc-accent);width:24px;height:24px}.tile-copy{flex:1;min-width:0}.tile .name{display:block}.tile .status{display:block;margin:4px 0 0;font-size:10px}.tile-temp{text-align:right;white-space:nowrap;font-size:22px}.tile-temp small{display:block;color:var(--rc-muted);font-size:10px;margin-top:3px}.error{margin-top:8px}@media(max-width:240px){.compact{padding:11px}.readings{flex-direction:column;align-items:flex-start;gap:0}.tile{gap:6px}.tile-temp{font-size:18px}.modes{gap:2px}.mode svg{display:none}}`;
      if(this._config.layout==='tile'){
        this.shadowRoot.innerHTML=`<style>${style}</style><button class="compact tile" data-action="info" aria-label="${escape(name)} · ${t.details}" title="${escape(details)}">${icon(entity.state)}<span class="tile-copy"><span class="name">${escape(name)}</span><span class="status">${escape(shortStatus)}${!a.control_devices?' · '+t.observe:''}</span></span><span class="tile-temp">${formatTemp(a.current_temperature,this._language)}°<small>→ ${formatTemp(a.temperature,this._language)}°</small></span></button>`;
        return;
      }
      this.shadowRoot.innerHTML=`<style>${style}</style><article class="compact"><div class="head"><span class="name">${escape(name)}</span><button class="icon-button" data-action="info" aria-label="${t.details}">${icon('info')}</button></div><div class="readings"><div class="current">${formatTemp(a.current_temperature,this._language)}<small> ${escape(unit)}</small></div><div class="target"><button class="icon-button" data-action="minus" aria-label="${t.target} −" ${busy} ${Number(a.temperature)<=Number(a.min_temp??5)?'disabled':''}>${icon('minus')}</button><strong data-target>${formatTemp(this._draft??a.temperature,this._language)}°</strong><button class="icon-button" data-action="plus" aria-label="${t.target} +" ${busy} ${Number(a.temperature)>=Number(a.max_temp??30)?'disabled':''}>${icon('plus')}</button></div></div><div class="modes">${['heat','cool','off'].map(mode=>`<button class="mode" data-action="mode" data-mode="${mode}" aria-pressed="${entity.state===mode}" ${busy} ${mode==='cool'&&coolBlocked?'disabled':''} title="${escape(mode==='cool'&&!canCool?(pl?'Przypisz klimatyzator w ustawieniach pokoju':'Assign AC in room settings'):'')}">${icon(mode)}${t[mode]}</button>`).join('')}</div><p class="status">${escape(status)}</p>${shortDetails?`<div class="note" title="${escape(details)}">${escape(shortDetails)}</div>`:''}<div class="bottom"><span>${a.control_devices?t.live:t.observe}</span><button data-action="control" role="switch" aria-checked="${Boolean(a.control_devices)}" aria-label="${a.control_devices?t.disable:t.enable}" ${busy} ${!a.control_switch||unavailable(this._hass.states[a.control_switch])?'disabled':''}>${a.control_devices?t.disable:t.enable}</button></div>${this._error?`<div class="error" role="alert">${escape(this._error)}</div>`:''}</article>`;
      if(focusAction)this.shadowRoot.querySelector(`[data-action="${focusAction}"]`)?.focus({preventScroll:true});
    }
    _render() {
      if (!this.shadowRoot || !this._hass) return;
      this._language = lang(this._hass, this._config);
      const t = text[this._language];
      const entity = this._hass.states[this._config.entity];
      if (!entity || entity.attributes.room_comfort !== true || unavailable(entity)) {
        this.shadowRoot.innerHTML = `<style>${sharedStyles}</style><ha-card><div class="empty">${icon("room")}<h2>${escape(this._config.name || t.room)}</h2><p>${escape(entity ? t.missing : t.noEntity)}</p></div></ha-card>`;
        return;
      }
      if (["compact","tile"].includes(this._config.layout)) { this._renderCompact(entity); return; }
      const focusAction = this.shadowRoot.activeElement?.dataset.action;
      const a = entity.attributes;
      const unit = a.temperature_unit || this._hass.config?.unit_system?.temperature || "°C";
      const target = this._draft ?? a.temperature;
      const current = a.current_temperature;
      const boost = Number(a.boost_ends_at) > Date.now()/1000;
      const ac = a.air_conditioner && this._hass.states[a.air_conditioner];
      const acBad = Boolean(a.air_conditioner && unavailable(ac));
      const canCool = Boolean(a.air_conditioner && (a.hvac_modes || []).includes("cool"));
      const sensorBad = !finite(current) || a.demand_status === "sensor_unavailable";
      const coolReason = !canCool ? (this._language === "pl" ? "Przypisz klimatyzator w ustawieniach pokoju, aby chłodzić." : "Assign an air conditioner in room settings to enable cooling.") : acBad ? t.unavailableAC : sensorBad ? t.sensorFault : "";
      const busy = this._busy ? "disabled" : "";
      const min = a.min_temp ?? 16, max = a.max_temp ?? 28, step = a.target_temp_step ?? .5;
      const progress = finite(target) ? Math.max(0, Math.min(100, (Number(target)-min)/(max-min)*100)) : 0;
      const status = statusTexts[this._language][a.controller_status] || a.controller_status;
      const boostMinutes = a.boost_duration_minutes || 20;
      const demands = [a.desired_radiator_heat ? `${(a.radiators || []).length} ${t.radiators.toLowerCase()}` : "", a.desired_ac_mode !== "off" ? `${t.ac} · ${a.desired_ac_mode === "cool" ? t.cool : t.heat}` : ""].filter(Boolean).join(" + ") || t.off;
      const errors = Object.entries(a.device_errors || {});
      this.shadowRoot.innerHTML = `<style>${sharedStyles}
        .condition-note{margin-top:14px;padding:10px 12px;border-radius:10px;background:var(--rc-soft);font-size:10px;line-height:1.8;color:var(--rc-muted)}.condition-note a{text-decoration:underline}.profile-kind{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--rc-muted);margin:12px 0 7px}.profile-kind svg{width:14px;height:14px}.return-mode{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:11px;margin-top:12px;color:var(--rc-muted)}.return-mode select{background:var(--rc-bg);color:inherit;border:1px solid var(--rc-line);border-radius:8px;padding:8px;min-height:40px}.profiles{margin-top:18px}.profile-heading{display:flex;align-items:center;justify-content:space-between;font-size:9px;letter-spacing:1px;color:var(--rc-muted);margin-bottom:9px}.profile-heading strong{font-size:10px;letter-spacing:0;color:var(--rc-accent);font-weight:550}.profile-fields{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.profile-field{padding:10px;border:1px solid var(--rc-line);border-radius:10px;min-width:0}.profile-field.active{border-color:color-mix(in srgb,var(--rc-accent) 40%,var(--rc-line));background:var(--rc-tint)}.profile-field>span{font-size:10px;color:var(--rc-muted);display:block;margin-bottom:7px}.profile-field>div{display:flex;align-items:center;gap:2px}.profile-field input{min-width:0;width:100%;color:inherit;background:transparent;border:0;border-bottom:1px solid var(--rc-line);padding:2px 0;font-size:16px}.profile-field small{font-size:9px;color:var(--rc-muted)}.pid-demand{display:flex;align-items:center;gap:8px;margin-top:14px;font-size:10px;color:var(--rc-muted)}.pid-demand strong{color:var(--rc-accent);font-size:11px}.pid-demand meter{flex:1;min-width:35px;height:6px;accent-color:var(--rc-accent)}
        :host{min-width:0}ha-card{display:block;background:var(--rc-bg);border:1px solid var(--rc-line);border-radius:22px;box-shadow:none;overflow:hidden}.card{padding:24px}.card.cool{--rc-accent:#397e9b}.card.off{--rc-accent:#7b8478}.top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.room-type{display:flex;gap:7px;align-items:center;color:var(--rc-muted);margin-bottom:7px}.room-type svg{width:14px;height:14px}h2{font-size:24px;font-weight:550;letter-spacing:-.8px;margin:0;line-height:1.2}.top .icon-button{width:36px;height:36px;min-height:36px;border:0;color:var(--rc-muted)}.status{display:flex;align-items:center;gap:7px;font-size:12px;line-height:1.4;color:var(--rc-muted);margin:10px 0 0}.dot{display:inline-block;flex:none;width:6px;height:6px;background:var(--rc-muted);border-radius:50%}.running,.status .dot{color:var(--rc-accent)}.dot.running,.status .dot{background:var(--rc-accent)}.temperature{display:flex;align-items:center;justify-content:space-between;padding:23px 0 10px;gap:12px}.reading{min-width:0}.reading-label{font-size:11px;line-height:1.5;max-width:90px;color:var(--rc-muted)}.reading-value{font-size:31px;font-weight:450;letter-spacing:-1.4px;white-space:nowrap;margin-top:6px}.reading-value small{font-size:16px;letter-spacing:-.5px;color:var(--rc-muted)}.dial{display:grid;place-items:center;width:174px;height:174px;flex:none;border-radius:50%;background:conic-gradient(from 215deg,var(--rc-accent) 0deg,var(--rc-accent) calc(var(--progress)*2.9deg),var(--rc-soft) calc(var(--progress)*2.9deg),var(--rc-soft) 290deg,transparent 290deg);position:relative;isolation:isolate}.dial:before{content:"";position:absolute;inset:5px;background:var(--rc-bg);border-radius:50%;z-index:-1}.dial-center{text-align:center;padding-top:4px}.dial .eyebrow{font-size:9px;color:var(--rc-muted);letter-spacing:1.3px}.setpoint{display:block;font-size:51px;font-weight:450;line-height:1.1;letter-spacing:-2.4px;margin-top:8px;font-variant-numeric:tabular-nums}.setpoint small{font-size:19px;letter-spacing:-1px;vertical-align:top;display:inline-block;margin-top:8px}.dial-mode{font-size:10px;color:var(--rc-accent);margin-top:9px;display:flex;gap:4px;align-items:center;justify-content:center}.dial-mode svg{width:13px;height:13px}.stepper{display:flex;align-items:center;justify-content:center;gap:15px;padding-bottom:13px}.stepper .icon-button{width:39px;height:39px;min-height:44px;border-color:var(--rc-line)}.stepper input{width:100%;min-width:50px;height:44px;accent-color:var(--rc-accent);cursor:pointer;margin:0 2px}.stepper button{flex:none}.modes{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:4px;background:var(--rc-soft);border-radius:12px}.modes.two{grid-template-columns:repeat(2,1fr)}.mode{background:transparent;border:0;display:flex;align-items:center;justify-content:center;gap:6px;font-size:12px;border-radius:9px;color:var(--rc-muted);min-width:0;padding:8px 4px}.mode svg{width:16px;height:16px}.mode.selected{color:var(--primary-text-color,#242924);background:var(--rc-bg);box-shadow:0 1px 3px #0000000b}.source{margin-top:21px}.source .eyebrow{color:var(--rc-muted);font-size:9px;letter-spacing:1.3px}.sources{display:flex;gap:8px;margin-top:9px}.source-button{flex:1;display:flex;gap:7px;align-items:center;justify-content:center;white-space:nowrap;padding:9px 7px;font-size:11px;font-weight:550;border:1px solid var(--rc-line);background:transparent;border-radius:10px}.source-button svg{width:16px;height:16px}.source-button.selected{color:var(--rc-accent);border-color:color-mix(in srgb,var(--rc-accent) 40%,var(--rc-line));background:var(--rc-tint)}.source-hint{font-size:11px;line-height:1.5;color:var(--rc-muted);margin:9px 0 0}.countdown{font-variant-numeric:tabular-nums;display:flex;align-items:center;justify-content:space-between;gap:8px;background:var(--rc-tint);border:1px solid color-mix(in srgb,var(--rc-accent) 20%,var(--rc-line));padding:10px 12px;margin-top:10px;border-radius:10px;font-size:11px}.countdown span{display:flex;align-items:center;gap:6px}.countdown svg{width:15px;height:15px}.countdown strong{font-size:17px;font-weight:600;color:var(--rc-accent)}.messages{display:grid;gap:8px;margin-top:13px}.observe{background:var(--rc-soft);border-radius:12px;padding:12px;display:flex;gap:8px;color:var(--rc-muted);font-size:11px;line-height:1.5}.observe svg{width:16px;height:16px;flex:none}.observe strong{display:block;color:var(--primary-text-color);font-weight:600}.observe p{margin:3px 0 0}.observe .demand{display:block;margin-top:6px;font-size:10px}.devices{border-top:1px solid var(--rc-line);margin-top:20px;padding-top:4px}summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;font-size:11px;color:var(--rc-muted);min-height:44px}summary::-webkit-details-marker{display:none}summary svg{width:14px;height:14px;transform:rotate(90deg)}details[open] summary svg{transform:rotate(-90deg)}.device{width:100%;background:transparent;border:0;padding:9px 0;display:flex;align-items:center;gap:9px;text-align:left;min-height:52px}.device-icon{display:grid;place-items:center;flex:none;width:32px;height:32px;background:var(--rc-soft);border-radius:9px;color:var(--rc-muted)}.device-icon.running{background:var(--rc-tint);color:var(--rc-accent)}.device-icon svg{width:17px;height:17px}.device-copy{min-width:0;flex:1}.device-copy>span{font-size:11px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px}.device-copy small{font-size:10px;color:var(--rc-muted);display:block;margin-top:3px}.device-state{font-size:10px;color:var(--rc-muted);display:flex;align-items:center;gap:5px;max-width:105px;text-align:right;line-height:1.4}.device-state .dot{width:4px;height:4px}.bad{color:#b77c2f}.sensor-row{display:flex;align-items:center;justify-content:space-between;padding:11px 0 0;font-size:11px;color:var(--rc-muted);gap:8px}.sensor-row button{padding:0;background:none;border:0;display:flex;align-items:center;gap:6px;min-width:0;text-align:left}.sensor-row svg{width:15px;height:15px}.sensor-row strong{font-size:12px;color:var(--primary-text-color);white-space:nowrap}.footer{border-top:1px solid var(--rc-line);margin-top:14px;padding-top:13px;display:flex;align-items:center;justify-content:space-between;gap:10px}.control-label{font-size:10px;color:var(--rc-muted);display:flex;align-items:center;gap:5px}.control-label svg{width:13px;height:13px}.control{font-size:10px;display:inline-flex;align-items:center;gap:7px;border:0;background:transparent;padding:0 0 0 8px;min-height:34px}.toggle{display:inline-flex;align-items:center;width:29px;height:17px;background:var(--rc-line);border-radius:20px;padding:3px;transition:background .15s}.toggle:after{content:"";background:var(--rc-bg);border-radius:50%;width:11px;height:11px;box-shadow:0 1px 2px #0002;transition:transform .15s}.control[aria-checked=true] .toggle{background:var(--rc-accent)}.control[aria-checked=true] .toggle:after{transform:translateX(12px)}.busy{font-size:10px;color:var(--rc-muted);margin:7px 0 0;text-align:center}.source-button:disabled{opacity:.45}.source-button:disabled[aria-pressed=true]{opacity:1}@media(max-width:350px){.card{padding:18px}.dial{width:155px;height:155px}.reading-value{font-size:27px}.setpoint{font-size:46px}.source-button{font-size:10px}h2{font-size:22px}}@media(pointer:coarse){.stepper .icon-button{width:44px}}
      </style><ha-card><article class="card ${tone(entity)}" aria-label="${escape(this._config.name || a.room_name || a.friendly_name)}">
        <div class="top"><div><div class="room-type eyebrow">${icon("room")}${t.room}</div><h2>${escape(this._config.name || a.room_name || a.friendly_name)}</h2></div><button class="icon-button" data-action="info" aria-label="${t.details}">${icon("info")}</button></div>
        <p class="status" role="status" title="${escape(t.activeIntent)}"><i class="dot"></i>${escape(status)}</p>
        <div class="temperature"><div class="reading"><div class="reading-label">${t.current}</div><div class="reading-value">${formatTemp(current, this._language)}<small> ${escape(unit)}</small></div></div><div class="dial" style="--progress:${progress}"><div class="dial-center"><span class="eyebrow">${t.setTo}</span><span class="setpoint"><span data-target>${formatTemp(target, this._language)}</span><small>°</small></span><div class="dial-mode">${icon(entity.state === "cool" ? "cool" : entity.state === "heat" ? "heat" : "off")}${escape(entity.state === "cool" ? t.cool : entity.state === "heat" ? t.heat : t.off)}</div></div></div></div>
        <div class="stepper"><button class="icon-button" data-action="minus" aria-label="${escape(t.target)} −" ${busy} ${Number(target)<=min?"disabled":""}>${icon("minus")}</button><input data-action="temperature" type="range" min="${escape(min)}" max="${escape(max)}" step="${escape(step)}" value="${escape(target)}" aria-label="${t.target}" aria-valuetext="${formatTemp(target,this._language)} ${escape(unit)}" ${busy}><button class="icon-button" data-action="plus" aria-label="${escape(t.target)} +" ${busy} ${Number(target)>=max?"disabled":""}>${icon("plus")}</button></div>
        <div class="modes" role="group" aria-label="HVAC">
          ${["heat","cool","off"].map(mode=>`<button class="mode ${entity.state===mode?"selected":""}" data-action="mode" data-mode="${mode}" aria-pressed="${entity.state===mode}" ${busy} ${mode==="cool"&&(!canCool||acBad||sensorBad)?"disabled":""} title="${escape(mode==="cool"?coolReason:"")}">${icon(mode)}${t[mode]}</button>`).join("")}
        </div>
        ${!canCool?`<p class="source-hint">${escape(coolReason)} <a href="/config/integrations/integration/room_comfort">${t.settings} ↗</a></p>`:""}
        ${a.profile_temperatures?`<div class="profiles" role="group" aria-label="${this._language==='pl'?'Temperatury trybów':'Profile temperatures'}"><div class="profile-heading"><span>${this._language==='pl'?'TEMPERATURY TRYBÓW':'COMFORT TARGETS'}</span><strong>${escape(({home:'Home',away:'Away',vacation:'Vacation',prewarming:'Coming home'})[a.home_profile]||'Home')}</strong></div>${['heat',...(canCool?['cool']:[])].map(mode=>{
          const values=(mode==='cool'?a.cooling_profile_temperatures:a.heating_profile_temperatures)||a.profile_temperatures;
          const ids=(mode==='cool'?a.cooling_profile_temperature_entities:a.heating_profile_temperature_entities)||a.profile_temperature_entities;
          return `<div class="profile-kind">${icon(mode)}${t[mode]}</div><div class="profile-fields">${['home','away','vacation'].map(profile=>`<label class="profile-field ${(a.home_profile==='prewarming'?'home':a.home_profile)===profile&&((entity.state==='cool')===(mode==='cool'))?'active':''}"><span>${escape(({home:this._language==='pl'?'Dom':'Home',away:this._language==='pl'?'Poza domem':'Away',vacation:this._language==='pl'?'Wakacje':'Vacation'})[profile])}</span><div><input type="number" min="5" max="30" step="0.5" value="${escape(values[profile])}" data-profile-entity="${escape(ids?.[profile]||'')}" aria-label="${profile} ${mode==='cool'?'cooling ':''}temperature" ${!ids?.[profile]||this._busy?'disabled':''}><small>°C</small></div></label>`).join('')}</div>`;
        }).join('')}${a.coming_home_mode_entity?`<label class="return-mode">${this._language==='pl'?'Przed powrotem':'For my return'}<select data-return-mode="${escape(a.coming_home_mode_entity)}" aria-label="Coming home mode" ${busy}>${['heat',...(canCool?['cool']:[])].map(mode=>`<option value="${mode}" ${a.coming_home_mode===mode?'selected':''}>${t[mode]}</option>`).join('')}</select></label>`:''}</div>`:''}
        ${a.control_method==='pid'&&entity.state!=='cool'?`<div class="pid-demand"><span>PID · ${this._language==='pl'?'zapotrzebowanie ciepła':'heat demand'}</span><strong>${Math.round(a.heat_demand_percent||0)}%</strong><meter min="0" max="100" value="${Number(a.heat_demand_percent)||0}" aria-label="Calculated heat demand"></meter></div>`:''}
        ${entity.state==="cool"?`<div class="source"><div class="eyebrow">${t.cool}</div><div class="sources"><span class="source-button selected">${icon("ac")}${t.ac}</span></div><p class="source-hint">${this._language==="pl"?"Klimatyzator chłodzi według czujnika pokoju. Grzejniki pozostają wyłączone. Histereza i minimalny czas postoju chronią przed częstym przełączaniem.":"AC cools using the room sensor. Radiators stay off. Hysteresis and the minimum off time limit switching."}</p></div>`:`<div class="source"><div class="eyebrow">${t.source}</div><div class="sources"><button class="source-button ${entity.state==="heat"&&!boost?"selected":""}" data-action="radiators" aria-pressed="${entity.state==="heat"&&!boost}" ${busy}>${icon("radiator")}${t.radiators}</button>${a.air_conditioner?`<button class="source-button ${boost?"selected":""}" data-action="${boost?"cancel":"boost"}" aria-pressed="${boost}" ${busy} ${!boost&&(acBad||sensorBad)?"disabled":""} title="${escape(t.boostHint)}">${icon("bolt")}${boost?t.cancel:t.boost}</button>`:""}</div>${a.air_conditioner?`<p class="source-hint">${t.boostHint}</p>`:""}</div>`}
        ${boost?`<div class="countdown"><span>${icon("clock")}${t.remaining} · ${boostMinutes} ${t.minute} max</span><strong data-countdown></strong></div>`:""}
        ${conditionSummary(a,this._language)?`<div class="condition-note">${escape(conditionSummary(a,this._language))}<br><a href="/config/integrations/integration/room_comfort">${t.settings} ↗</a></div>`:""}
        <div class="messages" aria-live="polite">${this._error?`<div class="error" role="alert">${icon("alert")}<span>${escape(this._error)}</span></div>`:""}${sensorBad?`<div class="error">${icon("alert")}<span>${t.sensorFault}</span></div>`:""}${acBad?`<div class="error">${icon("alert")}<span>${t.unavailableAC}</span></div>`:""}${errors.length?`<div class="error">${icon("alert")}<span>${errors.map(([id,msg])=>`${escape(this._hass.states[id]?.attributes.friendly_name||id)}: ${escape(msg)}`).join("<br>")}</span></div>`:""}${!a.control_devices?`<div class="observe">${icon("info")}<div><strong>${t.observe}</strong><p>${t.observeHint}</p><span class="demand">${t.demand}: ${escape(demands)}</span></div></div>`:""}</div>
        ${this._config.show_devices!==false?`<details class="devices" ${this._details?"open":""}><summary>${t.devices}${icon("arrow")}</summary>${(a.radiators||[]).map(id=>this._device(id,"radiator",t)).join("")}${a.air_conditioner?this._device(a.air_conditioner,"ac",t):""}${(a.windows||[]).map(id=>this._device(id,"window",t)).join("")}${(a.presence_sensors||[]).map(id=>this._device(id,"presence",t)).join("")}</details>`:""}
        ${this._config.show_sensor!==false?`<div class="sensor-row"><button data-action="info" data-entity="${escape(a.room_sensor)}" title="${escape(t.history)}">${icon("sensor")}<span>${escape(this._hass.states[a.room_sensor]?.attributes.friendly_name||t.sensor)}</span></button><strong>${formatTemp(current,this._language)} ${escape(unit)}</strong></div>`:""}
        <div class="footer"><span class="control-label">${icon(a.control_devices?"check":"info")}${a.control_devices?t.live:t.observe}</span><button class="control" role="switch" aria-checked="${Boolean(a.control_devices)}" aria-label="${a.control_devices?t.disable:t.enable}" data-action="control" title="${escape(a.control_switch?t.enableHint:t.controlUnavailable)}" ${busy} ${!a.control_switch||unavailable(this._hass.states[a.control_switch])?"disabled":""}><span>${a.control_devices?t.disable:t.enable}</span><i class="toggle"></i></button></div>
        ${this._busy?`<p class="busy" role="status">${t.pending}</p>`:""}
      </article></ha-card>`;
      const details = this.shadowRoot.querySelector("details");
      if (details) details.addEventListener("toggle", () => { this._details = details.open; });
      if (focusAction) this.shadowRoot.querySelector(`[data-action="${focusAction}"]`)?.focus({preventScroll:true});
      this._countdown();
    }
  }

  class RoomComfortMiniCard extends RoomComfortCard {
    get defaultLayout(){return 'compact';}
    static getStubConfig(hass){return {...super.getStubConfig(hass),type:'custom:room-comfort-mini-card',layout:'compact'};}
  }
  class RoomComfortStatusCard extends RoomComfortCard {
    get defaultLayout(){return 'tile';}
    static getStubConfig(hass){return {...super.getStubConfig(hass),type:'custom:room-comfort-status-card',layout:'tile'};}
  }

  class RoomComfortHomeControls extends HTMLElement {
    constructor(){
      super();this.attachShadow({mode:"open"});this._busy=false;this._error="";
      this.shadowRoot.addEventListener("click",async event=>{
        const button=event.target.closest("[data-home-switch]");
        if(!button||button.disabled||this._busy)return;
        const id=button.dataset.homeSwitch;
        this._busy=true;this._error="";this._render();
        try{await this._hass.callService("switch",this._hass.states[id]?.state==="on"?"turn_off":"turn_on",{},{entity_id:id});}
        catch(error){this._error=error.message||String(error);}
        finally{this._busy=false;this._render();}
      });
    }
    connectedCallback(){this._timer=setInterval(()=>this._countdown(),1000);}
    disconnectedCallback(){clearInterval(this._timer);}
    set hass(hass){this._hass=hass;this._render();}
    _countdown(){
      const output=this.shadowRoot.querySelector("[data-prewarm-countdown]");
      if(output){const seconds=Math.max(0,Math.ceil((this._ends||0)-Date.now()/1000));output.textContent=`${Math.floor(seconds/3600)}h ${Math.floor(seconds%3600/60)}m`;}
    }
    _render(){
      if(!this._hass)return;
      const pl=lang(this._hass)==="pl";
      const mode=Object.values(this._hass.states).find(e=>e.entity_id.startsWith("sensor.")&&e.attributes.room_comfort_household);
      if(!mode){this.shadowRoot.innerHTML="";return;}
      const a=mode.attributes, entities=a.household_entities||{};
      const labels=pl?{home:"W domu",away:"Poza domem",vacation:"Wakacje",prewarming:"Powrót do domu"}:{home:"Home",away:"Away",vacation:"Vacation",prewarming:"Coming home"};
      const labels2=pl?{vacation:"Wakacje",coming_home:"Przygotuj dom przed powrotem",automatic_away:"Automatycznie poza domem"}:{vacation:"Vacation",coming_home:"Prepare for my return",automatic_away:"Automatic away"};
      const profile=a.home_profile||mode.state;
      this._ends=a.prewarm_ends_at;
      const memberships=Object.entries(a.memberships||{});
      const ready=profile==="prewarming"&&a.prewarm_ready;
      this.shadowRoot.innerHTML=`<style>${sharedStyles}
        .outdoor-global{font-size:10px;line-height:1.7;color:var(--rc-muted);margin-top:12px}.outdoor-global a{text-decoration:underline}.automation-help{border-top:1px solid var(--rc-line);margin-top:14px;padding-top:6px;font-size:11px;color:var(--rc-muted)}.automation-help summary{display:flex;align-items:center;justify-content:space-between;cursor:pointer;min-height:44px}.automation-help summary svg{width:14px;height:14px}.automation-help p{line-height:1.6;margin:0 0 10px}.automation-help a{text-decoration:underline;display:inline-block;line-height:2}.home-box{margin:24px 0 0;padding:20px 22px;border:1px solid var(--rc-line);border-radius:16px;background:var(--rc-bg)}.home-head{display:flex;justify-content:space-between;gap:14px;align-items:center}.home-title{display:flex;align-items:center;gap:9px;font-size:14px;font-weight:600}.profile{font-size:11px;border-radius:20px;padding:6px 10px;background:var(--rc-tint);color:var(--rc-accent);white-space:nowrap}.home-help{font-size:11px;color:var(--rc-muted);line-height:1.6;margin:9px 0 15px}.home-switches{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.home-switch{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:49px;text-align:left;background:transparent;border:1px solid var(--rc-line);border-radius:11px;padding:10px 12px;font-size:11px}.home-switch[aria-checked=true]{background:var(--rc-tint);border-color:color-mix(in srgb,var(--rc-accent) 40%,var(--rc-line))}.home-switch .label{display:flex;align-items:center;gap:7px}.home-switch svg{width:17px;height:17px}.home-toggle{background:var(--rc-line);width:29px;height:17px;flex:none;padding:3px;border-radius:20px}.home-toggle:after{content:"";display:block;width:11px;height:11px;background:var(--rc-bg);border-radius:50%}.home-switch[aria-checked=true] .home-toggle{background:var(--rc-accent)}.home-switch[aria-checked=true] .home-toggle:after{transform:translateX(12px)}.trackers{display:flex;flex-wrap:wrap;gap:7px;margin-top:13px}.tracker{display:inline-flex;align-items:center;gap:5px;padding:5px 8px;border:1px solid var(--rc-line);border-radius:20px;font-size:10px;color:var(--rc-muted)}.tracker i{height:5px;width:5px;border-radius:50%;background:#b98c42}.tracker.inside i{background:#4c9666}.tracker.outside i{background:#87978a}.home-bottom{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:10px;color:var(--rc-muted);line-height:1.7;margin-top:12px}.home-bottom a{white-space:nowrap}.prewarm-state{margin-top:12px;padding:10px 12px;border-radius:10px;background:var(--rc-tint);font-size:11px;display:flex;align-items:center;justify-content:space-between;gap:12px}.error{margin-top:12px}@media(max-width:720px){.home-box{padding:16px;margin-top:20px}.home-switches{grid-template-columns:1fr}.home-head{align-items:flex-start}.home-bottom{align-items:flex-start;flex-direction:column;gap:4px}.home-switch{font-size:12px;min-height:47px}}
      </style><section class="home-box" aria-label="${pl?"Tryby domu":"Home comfort modes"}"><div class="home-head"><div class="home-title">${icon("room")}${pl?"Komfort w domu":"Home comfort"}</div><span class="profile">${escape(labels[profile]||profile)}</span></div><p class="home-help">${pl?"Poza domem nadal utrzymujemy ustawioną temperaturę dla każdego pokoju. Wakacje włączasz ręcznie.":"Away still maintains each room’s configured comfort temperature. Vacation only starts when you switch it on."}</p><div class="home-switches">${["vacation","coming_home","automatic_away"].map(key=>{
        const id=entities[key],on=this._hass.states[id]?.state==="on";
        return `<button class="home-switch" role="switch" aria-label="${escape(labels2[key])}" aria-checked="${on}" data-home-switch="${escape(id||"")}" ${!id||unavailable(this._hass.states[id])||this._busy?"disabled":""}><span class="label">${icon(key==="coming_home"?"ac":key==="vacation"?"room":"sensor")}${labels2[key]}</span><i class="home-toggle"></i></button>`;
      }).join("")}</div>${memberships.length?`<div class="trackers">${memberships.map(([id,value])=>`<span class="tracker ${value===true?"inside":value===false?"outside":"unknown"}"><i></i>${escape(this._hass.states[id]?.attributes.friendly_name||id)} · ${value===true?(pl?"w strefie":"inside"):value===false?(pl?"poza strefą":"outside"):(pl?"nieznany":"unknown")}</span>`).join("")}</div>`:""}${profile==="prewarming"?`<div class="prewarm-state"><span>${ready?(pl?"Gotowe — utrzymujemy temperatury Dom do powrotu":"Ready — holding Home temperatures for your return"):(pl?"Grzanie lub chłodzenie do temperatur Dom — pokoje z aktywnym sterowaniem":"Heating or cooling to Home targets — rooms with live control enabled")}</span><strong data-prewarm-countdown></strong></div>`:""}<div class="home-bottom"><span>${memberships.length?(pl?"Poza domem: wszystkie urządzenia poza strefą":"Away: every tracker outside the zone")+` · ${a.away_delay_minutes||0} min`:(pl?"Wybierz osoby lub urządzenia do wykrywania nieobecności.":"Choose people or trackers to enable automatic Away.")}<br>${pl?"Nieznany stan urządzenia nie oznacza nieobecności.":"An unknown tracker never counts as everyone away."}</span><a href="/config/integrations/integration/room_comfort">${pl?"Ustawienia → Tryby domu":"Configure → Home modes"} ↗</a></div><div class="outdoor-global">${a.outdoor_settings?.outdoor_enabled?`${pl?'Globalne limity zewnętrzne':'Global outdoor limits'} · ${pl?'Grzanie':'Heat'} &lt; ${escape(a.outdoor_settings.outdoor_heat_below)}°C · ${pl?'Chłodzenie':'Cool'} &gt; ${escape(a.outdoor_settings.outdoor_cool_above)}°C · ${pl?'Histereza':'Hysteresis'} ${escape(a.outdoor_settings.outdoor_hysteresis)}°C`:(pl?'Globalne limity zewnętrzne wyłączone':'Global outdoor limits off')} · <a href="/config/integrations/integration/room_comfort">${pl?'Ustaw limity':'Configure limits'} ↗</a></div><details class="automation-help"><summary>${pl?"Automatyzacje i blueprinty":"Automations & blueprints"}${icon("arrow")}</summary><p>${pl?"Ustaw harmonogram temperatury Dom, dodaj przycisk powrotu lub powiadomienie o gotowym domu. Nieobecność i Wakacje pozostają pod kontrolą trybów domu.":"Schedule Home targets, connect a return-home button, or get notified when rooms are ready. Away and Vacation keep their own targets."}</p><a href="/config/blueprint/dashboard">${pl?"Otwórz blueprinty":"Open HA blueprints"} ↗</a> · <a href="https://github.com/qmciaq/ha-room-comfort/blob/main/docs/automations.md" target="_blank" rel="noopener">${pl?"Instrukcje i szablony":"Setup guide & templates"} ↗</a></details>${this._error?`<div class="error" role="alert">${escape(this._error)}</div>`:""}</section>`;
      this._countdown();
    }
  }


  class RoomComfortOverview extends HTMLElement {
    constructor() {
      super(); this.attachShadow({mode:"open"}); this._config = {}; this._filter = "all"; this._query = ""; this._cards = new Map();
      this.shadowRoot.addEventListener("click", e => {
        const filter = e.target.closest("[data-filter]");
        if (filter) { this._filter = filter.dataset.filter; this._update(); }
        if (e.target.closest("[data-reset]")) { this._filter = "all"; this._query = ""; this._update(); }
        if (e.target.closest("[data-menu]")) fire(this,"hass-toggle-menu");
      });
      this.shadowRoot.addEventListener("input", e => { if(e.target.matches("input[type=search]")){this._query=e.target.value;this._update();} });
    }
    setConfig(config) { this._config = config || {}; this._shell = false; this._update(); }
    set hass(hass) { this._hass = hass; this._update(); }
    getCardSize() { return 10; }
    getGridOptions() { return {columns:"full", rows:"auto"}; }
    static getConfigElement() { return document.createElement("room-comfort-overview-editor"); }
    static getStubConfig() { return {title:"Room Comfort"}; }
    _update() {
      if (!this._hass) return;
      const language = lang(this._hass,this._config), t = text[language];
      const all = roomEntities(this._hass).filter(e => !this._config.entities || this._config.entities.includes(e.entity_id)).sort((a,b)=>(a.attributes.room_name || a.attributes.friendly_name).localeCompare(b.attributes.room_name || b.attributes.friendly_name,language));
      const heating = all.filter(e=>e.attributes.control_devices && ["heating","boosting"].includes(e.attributes.controller_status)).length;
      const cooling = all.filter(e=>e.attributes.control_devices && e.attributes.controller_status === "cooling").length;
      const needsAttention = all.filter(e=>warning(e,this._hass)).length;
      if (!this._shell || this._language !== language) {
        this._language=language; this._shell=true; this._cards.clear();
        this.shadowRoot.innerHTML=`<style>${sharedStyles}
          :host{display:block}.overview{max-width:1280px;margin:0 auto;padding:32px 32px 50px}.hero{display:flex;align-items:center;justify-content:space-between;gap:20px}.heading .eyebrow{color:var(--rc-muted);margin:0 0 9px}.heading h1{font-size:34px;font-weight:500;letter-spacing:-1.3px;margin:0}.heading p{font-size:13px;color:var(--rc-muted);line-height:1.6;margin:9px 0 0}.add{flex:none}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:28px 0 26px}.stat{padding:17px 19px;border:1px solid var(--rc-line);border-radius:14px;background:var(--rc-bg);display:flex;align-items:center;justify-content:space-between;gap:8px}.stat-label{font-size:11px;color:var(--rc-muted);display:block}.stat strong{display:block;font-size:28px;font-weight:450;letter-spacing:-1px;margin-top:4px}.stat svg{width:23px;height:23px;color:var(--rc-muted)}.stat.heating svg{color:#b65c31}.stat.cooling svg{color:#397e9b}.stat.attention svg{color:#a77b37}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px}.filters{display:flex;gap:5px;flex-wrap:wrap}.filter{border:1px solid transparent;background:transparent;border-radius:9px;padding:8px 12px;font-size:11px;color:var(--rc-muted);min-height:38px}.filter[aria-pressed=true]{background:var(--rc-bg);border-color:var(--rc-line);color:var(--primary-text-color);font-weight:550}.search{position:relative;display:flex;align-items:center;max-width:230px}.search svg{width:15px;height:15px;position:absolute;left:11px;color:var(--rc-muted)}.search input{width:100%;border:1px solid var(--rc-line);background:var(--rc-bg);color:inherit;padding:11px 12px 11px 34px;font-size:11px;border-radius:9px;min-height:40px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:18px;align-items:start}.grid room-comfort-card{min-width:0;max-width:480px}.empty{background:var(--rc-bg);border:1px dashed var(--rc-line);border-radius:18px;margin:20px 0}.empty[hidden],.no-matches[hidden]{display:none}.footer{margin-top:24px;font-size:10px;color:var(--rc-muted);display:flex;justify-content:space-between;gap:12px}.footer a:hover{text-decoration:underline}.menu{display:none}.no-matches{text-align:center;color:var(--rc-muted);padding:30px}.reset{border:0;background:var(--rc-soft);border-radius:9px;padding:9px 16px;font-size:12px}.top-actions{display:flex;align-items:center;gap:8px}@media(min-width:1500px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:720px){.overview{padding:22px 16px 34px}.heading h1{font-size:28px}.hero{align-items:flex-start;gap:10px}.heading p{max-width:220px;font-size:12px}.add{padding:10px;font-size:0;border-radius:50%;width:42px;height:42px;justify-content:center}.add svg{width:20px;height:20px}.stats{gap:8px;margin:23px 0 20px;grid-template-columns:repeat(2,1fr)}.stat{padding:12px 14px}.stat strong{font-size:24px}.stat-label{font-size:10px}.stat svg{width:20px;height:20px}.toolbar{align-items:stretch;flex-direction:column;gap:12px}.filters{gap:3px;display:grid;grid-template-columns:repeat(4,1fr)}.filter{font-size:10px;padding:7px 4px}.search{max-width:none}.search input{font-size:12px}.grid{grid-template-columns:1fr;gap:14px}.grid room-comfort-card{max-width:none}.menu{display:inline-flex;border:0;margin-left:-8px;width:38px;height:38px}.mobile-heading{display:flex;align-items:center;gap:7px}.footer{font-size:9px}}
        </style><section class="overview"><header class="hero"><div class="heading"><div class="mobile-heading"><button class="icon-button menu" data-menu aria-label="Menu">${icon("menu")}</button><p class="eyebrow">${t.overview}</p></div><h1>${escape(this._config.title||t.title)}</h1><p>${t.subtitle}</p></div><a class="primary add" href="/config/integrations/dashboard/add?domain=room_comfort" aria-label="${t.add}">${icon("plus")}${t.add}</a></header><room-comfort-home-controls></room-comfort-home-controls><div class="stats"><div class="stat"><div><span class="stat-label">${t.roomCount}</span><strong data-stat="rooms"></strong></div>${icon("room")}</div><div class="stat heating"><div><span class="stat-label">${t.heating}</span><strong data-stat="heating"></strong></div>${icon("heat")}</div><div class="stat cooling"><div><span class="stat-label">${t.cooling}</span><strong data-stat="cooling"></strong></div>${icon("cool")}</div><div class="stat attention"><div><span class="stat-label">${t.attention}</span><strong data-stat="attention"></strong></div>${icon("alert")}</div></div><div class="toolbar"><div class="filters" role="group" aria-label="${t.all}">${[["all",t.all],["heat",t.heating],["cool",t.cooling],["attention",t.attention]].map(([id,label])=>`<button class="filter" data-filter="${id}" aria-pressed="false">${label}</button>`).join("")}</div><label class="search">${icon("search")}<input type="search" placeholder="${t.search}" aria-label="${t.search}"></label></div><div class="grid"></div><div class="empty" hidden>${icon("room")}<h2>${t.noRooms}</h2><p>${t.noRoomsHint}</p><a class="primary" href="/config/integrations/dashboard/add?domain=room_comfort">${icon("plus")}${t.add}</a></div><div class="no-matches" hidden><p>${t.noMatches}</p><button class="reset" data-reset>${t.reset}</button></div><footer class="footer"><span>Room Comfort · ${VERSION}</span><a href="/config/integrations/integration/room_comfort">${t.settings} ↗</a></footer></section>`;
      }
      this.shadowRoot.querySelector("room-comfort-home-controls").hass=this._hass;
      const stats={rooms:all.length,heating,cooling,attention:needsAttention};
      for(const [key,value] of Object.entries(stats)) this.shadowRoot.querySelector(`[data-stat="${key}"]`).textContent=value;
      this.shadowRoot.querySelectorAll("[data-filter]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.filter===this._filter)));
      const search=this.shadowRoot.querySelector("input[type=search]"); if(search.value!==this._query)search.value=this._query;
      const query=this._query.toLocaleLowerCase(language);
      const visible=all.filter(e=>{
        const name=(e.attributes.room_name||e.attributes.friendly_name||e.entity_id).toLocaleLowerCase(language);
        return name.includes(query) && (this._filter==="all" || (this._filter==="attention"?warning(e,this._hass):e.attributes.control_devices && (this._filter==="heat"?["heating","boosting"].includes(e.attributes.controller_status):e.attributes.controller_status==="cooling")));
      });
      const grid=this.shadowRoot.querySelector(".grid");
      const ids=new Set(visible.map(e=>e.entity_id));
      for(const [id,card] of this._cards){if(!ids.has(id)){card.remove();this._cards.delete(id);}}
      for(const [index,e] of visible.entries()){
        let card=this._cards.get(e.entity_id);
        if(!card){card=document.createElement("room-comfort-card");card.setConfig({entity:e.entity_id,language,show_devices:this._config.show_devices!==false,show_sensor:this._config.show_sensor!==false});this._cards.set(e.entity_id,card);}
        card.hass=this._hass;
        if(grid.children[index]!==card)grid.insertBefore(card,grid.children[index]||null);
      }
      this.shadowRoot.querySelector(".empty").hidden=all.length!==0;
      this.shadowRoot.querySelector(".no-matches").hidden=all.length===0||visible.length!==0;
    }
  }

  class RoomComfortPanel extends RoomComfortOverview {
    constructor(){super();this.style.cssText="height:100%;overflow:auto;background:var(--primary-background-color,#f5f6f2)";}
    set panel(panel){this._panel=panel;}
    set narrow(value){this._narrow=value;}
  }

  class RoomComfortCardEditor extends HTMLElement {
    constructor(){super();this.attachShadow({mode:"open"});this._config={};this.shadowRoot.addEventListener("change",e=>this._change(e));}
    setConfig(config){this._config={...config};this._render();}
    set hass(hass){this._hass=hass;this._render();}
    _change(e){
      const key=e.target.dataset.key;if(!key)return;
      const value=e.target.type==="checkbox"?e.target.checked:e.target.value;
      const config={...this._config,[key]:value};
      if(value===""&&key!=="entity")delete config[key];
      this._config=config;fire(this,"config-changed",{config});
    }
    _render(){
      if(!this._hass)return;
      const t=text[lang(this._hass,this._config)], rooms=roomEntities(this._hass);
      this.shadowRoot.innerHTML=`<style>${sharedStyles}label{display:block;font-size:13px;margin:16px 0}select,input[type=text]{display:block;width:100%;padding:12px;margin:7px 0;border:1px solid var(--rc-line);border-radius:8px;background:var(--rc-bg);color:inherit}.checkbox{display:flex;gap:10px;align-items:center;min-height:44px}.checkbox input{width:19px;height:19px;accent-color:var(--primary-color,#b65c31)}</style><label>${t.entity}<select data-key="entity"><option value="">${t.noSelection}</option>${rooms.map(e=>`<option value="${escape(e.entity_id)}" ${e.entity_id===this._config.entity?"selected":""}>${escape(e.attributes.room_name||e.attributes.friendly_name)} · ${escape(e.entity_id)}</option>`).join("")}</select></label><label>${t.name}<input type="text" data-key="name" value="${escape(this._config.name||"")}"></label><label>${lang(this._hass,this._config)==='pl'?'Układ karty':'Card layout'}<select data-key="layout">${[['full','Full controls'],['compact','Compact controls'],['tile','Status tile']].map(([value,label])=>`<option value="${value}" ${(this._config.layout||(this._config.type==='custom:room-comfort-mini-card'?'compact':this._config.type==='custom:room-comfort-status-card'?'tile':'full'))===value?'selected':''}>${label}</option>`).join('')}</select></label><label class="checkbox"><input type="checkbox" data-key="show_devices" ${this._config.show_devices!==false?"checked":""}>${t.showDevices}</label><label class="checkbox"><input type="checkbox" data-key="show_sensor" ${this._config.show_sensor!==false?"checked":""}>${t.showSensor}</label>`;
    }
  }
  class RoomComfortOverviewEditor extends HTMLElement {
    constructor(){super();this.attachShadow({mode:"open"});this._config={};this.shadowRoot.addEventListener("change",e=>{const config={...this._config,title:e.target.value};this._config=config;fire(this,"config-changed",{config});});}
    setConfig(config){this._config={...config};this._render();}
    set hass(hass){this._hass=hass;this._render();}
    _render(){if(!this._hass)return;this.shadowRoot.innerHTML=`<style>${sharedStyles}label{display:block;margin:16px 0;font-size:13px}input{display:block;padding:12px;width:100%;background:var(--rc-bg);color:inherit;border:1px solid var(--rc-line);border-radius:8px;margin-top:8px}p{font-size:13px;color:var(--rc-muted);line-height:1.6}</style><label>Title<input value="${escape(this._config.title||"Room Comfort")}"></label><p>${text[lang(this._hass,this._config)].subtitle}</p>`;}
  }
  for(const [name,Class] of [["room-comfort-home-controls",RoomComfortHomeControls],["room-comfort-card",RoomComfortCard],["room-comfort-mini-card",RoomComfortMiniCard],["room-comfort-status-card",RoomComfortStatusCard],["room-comfort-overview",RoomComfortOverview],["room-comfort-panel",RoomComfortPanel],["room-comfort-card-editor",RoomComfortCardEditor],["room-comfort-overview-editor",RoomComfortOverviewEditor]]){
    if(!customElements.get(name))customElements.define(name,Class);
  }
  window.customCards=window.customCards||[];
  for(const [type,name,description] of [['room-comfort-mini-card','Room Comfort · Compact','Small room controls for side-by-side dashboard grids.'],['room-comfort-status-card','Room Comfort · Status','One-row room temperature and status; tap for details.']]){
    if(!window.customCards.some(c=>c.type===type))window.customCards.push({type,name,description,preview:true});
  }
  if(!window.customCards.some(c=>c.type==="room-comfort-card"))window.customCards.push({type:"room-comfort-card",name:"Room Comfort",description:"One room: target, radiators, AC boost and cooling.",preview:true,documentationURL:"https://github.com/qmciaq/ha-room-comfort",getEntitySuggestion:(hass,entityId)=>hass.states[entityId]?.attributes.room_comfort===true?{entity:entityId}:null});
  if(!window.customCards.some(c=>c.type==="room-comfort-overview"))window.customCards.push({type:"room-comfort-overview",name:"Room Comfort · All rooms",description:"Every configured room, with filters and live controls.",preview:true});
})();

