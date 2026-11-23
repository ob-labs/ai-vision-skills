"use strict"

const { randomBytes } = require("node:crypto")
const { chromium, expect: playwrightExpect } = require("@playwright/test")

const expect = playwrightExpect.configure({ timeout: 20_000 })
const demoTimeout = 70_000
const toolName = "retrieve_policy"
let stage = "validate local origin"

function requireCondition(condition, message) {
  if (!condition) throw new Error(message)
}

function localOrigin() {
  const args = process.argv.slice(2)
  const url = args.length === 1 && URL.parse(args[0])
  requireCondition(
    url && url.protocol === "http:" && url.hostname === "127.0.0.1" && url.port &&
      url.pathname === "/" && !url.search && !url.hash && !url.username && !url.password,
    "Usage: node scripts/live_quickstart_browser.cjs http://127.0.0.1:PORT",
  )
  return url.origin
}

function waitForApi(page, origin, path, method, timeout) {
  return page.waitForResponse((response) => {
    const url = new URL(response.url())
    return url.origin === origin && url.pathname === path && response.request().method() === method
  }, { timeout })
}

async function readData(response, label) {
  requireCondition(response.ok(), `${label} returned HTTP ${response.status()}`)
  const { code, data } = await response.json()
  requireCondition(code === 0 && data, `${label} did not return success data`)
  return data
}

async function register(page, origin) {
  const [csrf, registration] = await Promise.all([
    waitForApi(page, origin, "/api/v1/auth/csrf", "GET"),
    page.goto(`${origin}/register`),
  ])
  requireCondition(registration?.ok() && csrf.ok() && await csrf.finished() === null,
    "The registration page could not initialize CSRF protection")

  const email = `aiv-quickstart-${randomBytes(12).toString("hex")}@example.test`
  const password = `AivQuickstart8-${randomBytes(24).toString("base64url")}`
  await page.locator('input[name="name"]').fill("Quickstart CI")
  await page.locator('input[name="email"]').fill(email)
  await page.locator('input[name="password"]').fill(password)
  const [response] = await Promise.all([
    waitForApi(page, origin, "/api/v1/auth/register", "POST"),
    page.locator('button[type="submit"]').click(),
  ])
  requireCondition(response.status() === 201, `Registration returned HTTP ${response.status()}`)
  const { user, personal_space: space } = await readData(response, "Registration")
  requireCondition(user?.email === email && user.user_uuid && space?.space_id && space.type === 1,
    "Registration did not create a personal Space for the new account")
  await expect(page).toHaveURL((url) => url.origin === origin && url.pathname === "/dashboard")
  return space.space_id
}

async function chooseDemo(page, origin, spacePath, label, action) {
  const dialog = page.getByRole("dialog", { name: "用示例体验", exact: true })
  await dialog.getByText(label, { exact: true }).click()
  await expect(dialog.getByRole("radio", { name: label, exact: true })).toBeChecked()
  const [response] = await Promise.all([
    waitForApi(page, origin, `${spacePath}/onboarding/demo`, "POST", demoTimeout),
    dialog.getByRole("button", { name: action, exact: true }).click(),
  ])
  const receipt = await readData(response, "Built-in example")
  await expect(dialog).toHaveCount(0, { timeout: demoTimeout })
  return receipt
}

async function exampleUrl(page, origin, spaceId, agentId, parameter, value) {
  await expect(page).toHaveURL((url) => {
    const routeSpace = url.searchParams.get("spaceId")
    return url.origin === origin && url.pathname === "/trace" &&
      (routeSpace === null || routeSpace === spaceId) && url.searchParams.get("agent_uuid") === agentId &&
      url.searchParams.get(parameter) === value
  })
  return page.url()
}

async function openDetail(page, origin, url, path, label) {
  const [response, navigation] = await Promise.all([
    waitForApi(page, origin, path, "GET"),
    page.goto(url),
  ])
  requireCondition(navigation?.ok(), `${label} page failed to load`)
  return readData(response, label)
}

async function checkQuickstart(context, origin) {
  const page = await context.newPage()
  await page.addLocatorHandler(page.locator(".product-guide-offer"), (offer) =>
    offer.getByRole("button", { name: "跳过引导", exact: true }).click())

  stage = "register and select a personal Space"
  const spaceId = await register(page, origin)
  const spacePath = `/api/v1/spaces/${encodeURIComponent(spaceId)}`
  const modelConnectionsUrl = `${origin}${spacePath}/diagnose/model-connections`
  const models = await readData(await context.request.get(modelConnectionsUrl, { maxRedirects: 0 }), "Model connections")
  requireCondition(Array.isArray(models.items) && models.items.length === 0,
    "The new Space already has a configured model connection")

  stage = "import the multi-turn example from Help"
  await page.getByRole("button", { name: "帮助", exact: true }).click()
  await page.getByRole("menuitem", { name: "用示例体验", exact: true }).click()
  const demo = await chooseDemo(page, origin, spacePath, "多轮会话与费用", "创建并导入")
  const { agent_uuid: agentId } = demo
  const { session_id: sessionId, turns } = demo.scenarios.session
  const { trace_id: traceId, span_id: spanId } = demo.scenarios.mcp
  requireCondition(agentId && sessionId && traceId && spanId && turns?.length === 3 &&
    new Set(turns.map((turn) => turn.trace_id)).size === 3,
  "The built-in example did not return one Session with three distinct turns and an MCP Span")
  const sessionUrl = await exampleUrl(page, origin, spaceId, agentId, "sessionId", sessionId)
  await expect(page.getByTestId("native-session-detail")).toBeVisible()

  stage = "open the MCP example in the same Space"
  await page.getByRole("button", { name: "演示示例", exact: true }).click()
  const mcp = await chooseDemo(page, origin, spacePath, "MCP 调用与重试", "打开场景")
  requireCondition(mcp.agent_uuid === agentId && mcp.scenarios.session.session_id === sessionId &&
    mcp.scenarios.mcp.trace_id === traceId && mcp.scenarios.mcp.span_id === spanId,
  "Opening the MCP example did not reuse the imported data")
  const traceUrl = await exampleUrl(page, origin, spaceId, agentId, "traceId", traceId)
  await expect(page.getByTestId("native-trace-detail")).toHaveAttribute("data-guide-state", "ready")

  // Open the actual deep links in a fresh page. This forces readback from
  // the application's API without relying on the import receipt for results.
  const readback = await context.newPage()
  stage = "read back the persisted Session and its three turns"
  const session = await openDetail(readback, origin, sessionUrl,
    `${spacePath}/signoz/session/${encodeURIComponent(sessionId)}/detail`, "Session")
  requireCondition(session.sessionId === sessionId && session.traceCount === 3 && session.traceIds?.length === 3 &&
    turns.every((turn) => session.traceIds.includes(turn.trace_id)),
  "Session readback did not return the exact three imported turns")
  const sessionPanel = readback.getByTestId("native-session-detail")
  await expect(sessionPanel).toBeVisible()
  await expect(sessionPanel.locator('[data-product-guide="demo-data"]')).toBeVisible()
  await expect(sessionPanel.getByTestId("native-session-turn")).toHaveCount(3)

  stage = "read back the persisted Trace and exact MCP Span"
  const trace = await openDetail(readback, origin, traceUrl,
    `${spacePath}/signoz/trace/${encodeURIComponent(traceId)}/detail`, "Trace")
  requireCondition(trace.traceId === traceId && trace.spans?.some((span) => span.span_id === spanId),
    "Trace readback did not contain the exact imported Span")
  const tracePanel = readback.getByTestId("native-trace-detail")
  await expect(tracePanel).toHaveAttribute("data-guide-state", "ready")
  await expect(tracePanel).toHaveAttribute("data-guide-trace", traceId)
  await expect(tracePanel).toHaveAttribute("data-guide-selected", spanId)
  await expect(tracePanel.locator('[data-product-guide="demo-data"]')).toBeVisible()
  await expect(tracePanel.locator('[data-product-guide="mcp-span"]')).toContainText(toolName)

  return { personalSpace: true, sessionTurns: session.traceCount, traceReadBack: true, toolSpan: toolName, modelConnections: models.items.length }
}

async function main() {
  const origin = localOrigin()
  stage = "launch Chromium"
  const browser = await chromium.launch()
  try {
    const context = await browser.newContext({ locale: "zh-CN", serviceWorkers: "block", viewport: { width: 1440, height: 1000 } })
    context.setDefaultTimeout(20_000)
    try {
      await context.route("**/*", (route) =>
        new URL(route.request().url()).origin === origin ? route.continue() : route.abort())
      await context.addInitScript(() => localStorage.setItem("language", "zh-CN"))
      console.log(JSON.stringify(await checkQuickstart(context, origin)))
    } finally {
      await context.close()
    }
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  const message = String(error.message ?? error)
    .replace(/aiv-quickstart-[a-f0-9]+@example\.test/g, "[test email]")
    .replace(/AivQuickstart8-[A-Za-z0-9_-]+/g, "[test password]")
    .split("\n").slice(0, 10).join("\n")
  console.error(`${stage} failed\n${message}`)
  process.exitCode = 1
})
