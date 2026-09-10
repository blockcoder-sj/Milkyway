"use strict";
let csrf = "";
const message = document.querySelector("#message");
const market = document.querySelector("#market");
let providers = [];
function providerOptions() {
  const provider = providers.find(item => item.id === market.elements.provider.value);
  const choices = (provider?.environments || []).map(item => new Option(item.label, item.id));
  market.elements.environment.replaceChildren(...choices);
  if (choices.some(item => item.value === "paper")) market.elements.environment.value = "paper";
  document.querySelector("#provider-help").textContent = provider?.setup_help || "";
}
market.elements.provider.addEventListener("change", providerOptions);
request("/credentials/providers", "GET").then(value => {
  providers = value.providers;
  market.elements.provider.replaceChildren(...providers.map(item => new Option(item.label, item.id)));
  providerOptions();
}).catch(error => { message.textContent = error.message; });
async function request(path, method, payload) {
  const response = await fetch(path, {method, credentials: "same-origin", cache: "no-store",
    headers: {"Content-Type": "application/json", "X-CSRF-Token": csrf},
    body: payload === undefined ? undefined : JSON.stringify(payload)});
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === "string" ? value.detail : "요청에 실패했습니다");
  return value;
}
async function action(button, run) {
  button.disabled = true;
  message.textContent = "처리 중입니다…";
  try { await run(); } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
}
document.querySelector("#login").addEventListener("submit", event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  form.elements.password.value = "";
  action(form.querySelector("button"), async () => {
    const value = await request("/credentials/login", "POST", payload);
    csrf = value.csrf;
    document.querySelector("#identity").textContent = value.user.email;
    form.hidden = true;
    document.querySelector("#member").hidden = false;
    message.textContent = "로그인했습니다.";
  });
});
document.querySelector("#market").addEventListener("submit", event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form));
  form.elements.api_key.value = form.elements.api_secret.value = "";
  action(form.querySelector("button"), async () => {
    await request("/credentials/market", "PUT", payload);
    message.textContent = "증권사 API 인증과 저장을 완료했습니다. Milkyway에서 페이퍼 계좌를 사용하세요.";
  });
});
document.querySelector("#disconnect").addEventListener("click", event => action(event.currentTarget, async () => {
  await request("/credentials/market", "DELETE");
  message.textContent = "증권사 연결을 삭제했습니다.";
}));
document.querySelector("#logout").addEventListener("click", event => action(event.currentTarget, async () => {
  await request("/credentials/logout", "POST");
  csrf = "";
  document.querySelector("#member").hidden = true;
  document.querySelector("#login").hidden = false;
  message.textContent = "로그아웃했습니다.";
}));
