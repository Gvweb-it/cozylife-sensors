const API_BASE = "https://api-us.doiting.com/api";
const USER_AGENT = "DoHomeX/1.20.4 (iPhone; iOS 17.3.1; Scale/3.00)";

const email = process.env.COZYLIFE_EMAIL;
const password = process.env.COZYLIFE_PASSWORD;
// Italy uses 380 in CozyLife's country_number_code field.
const countryNumberCode = process.env.COZYLIFE_COUNTRY_CODE || "380";
const latitude = process.env.COZYLIFE_LAT || "41.9";
const longitude = process.env.COZYLIFE_LNG || "12.5";

if (!email || !password) {
  console.error("Set COZYLIFE_EMAIL and COZYLIFE_PASSWORD, then run this script.");
  process.exit(2);
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      "user-agent": USER_AGENT,
      ...(options.headers || {}),
    },
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${JSON.stringify(data)}`);
  }
  return data;
}

function makeLoginBody() {
  return {
    mail: email,
    passwd: password,
    lang: "en",
    platform: "ios",
    imei: "354627900145865",
    lat: latitude,
    lng: longitude,
    country_number_code: countryNumberCode,
    package_name: "am.doit.cozylife",
    user_term_version: "1.0.1",
    user_privacy_version: "1.0.0",
    package_version: "1.20.4",
  };
}

function qs(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, item);
    } else {
      search.append(key, String(value));
    }
  }
  return search.toString();
}

function decodeState(state = {}) {
  const temperatureRaw = Number(state["8"]);
  const humidityRaw = Number(state["4"]);
  const batteryRaw = Number(state["9"]);

  return {
    temperature_c: Number.isFinite(temperatureRaw) ? temperatureRaw / 10 : null,
    humidity_pct: Number.isFinite(humidityRaw) ? humidityRaw : null,
    battery_pct: Number.isFinite(batteryRaw) ? batteryRaw / 10 : null,
    online: state.online ?? null,
    raw: state,
  };
}

async function main() {
  const login = await request("/app/user/login", {
    method: "POST",
    body: JSON.stringify(makeLoginBody()),
  });

  if (login.ret !== "1" || !login.info?.token) {
    console.error(`Login failed: ${JSON.stringify(login)}`);
    process.exit(1);
  }

  const token = login.info.token;
  const devices = await request(
    `/v2/app/device_with_group/list?${qs({ token, count: 10000, page: 1 })}`
  );

  const list = devices.info?.device_bind?.list || [];
  console.log(`Devices: ${list.length}`);

  const ids = list.map((device) => device.device_id).filter(Boolean);
  const states = ids.length
    ? await request(`/app/v2/device/states?${qs({ token, "device_ids[]": ids })}`)
    : { info: [] };

  for (const item of states.info || []) {
    const device = list.find((candidate) => candidate.device_id === item.device_id);
    console.log(
      JSON.stringify(
        {
          name: device?.device_name,
          id: item.device_id,
          product_id: device?.device_product_id,
          model_name: device?.device_model_name,
          firmware_chip: device?.firmware_chip,
          firmware_version: device?.firmware_version,
          ...decodeState(item.state),
        },
        null,
        2
      )
    );
  }
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
