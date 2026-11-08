const DIVIDER = "─".repeat(60);
const SECTION_DIVIDER = "─".repeat(32);

function logOk(message) {
  console.log(`  ✅ ${message}`);
}

function logFail(message) {
  console.error(`  ❌ ${message}`);
}

function logWarn(message) {
  console.warn(`  ⚠️ ${message}`);
}

function logInfo(message) {
  console.log(`  ℹ️ ${message}`);
}

function logSection(title) {
  console.log(`🧪 ${title}`);
  console.log(SECTION_DIVIDER);
}

function logBanner(title, fields = {}) {
  console.log(`🧪 ${title}`);
  console.log(DIVIDER);
  for (const [label, value] of Object.entries(fields)) {
    console.log(`  ${String(label).padEnd(12)}: ${value}`);
  }
  console.log(DIVIDER);
  console.log("");
}

function logResult(ok, message) {
  console.log(DIVIDER);
  if (ok) {
    console.log(`✅ Result: PASS${message ? ` (${message})` : ""}`);
    return;
  }
  console.error(`❌ Result: FAIL${message ? ` (${message})` : ""}`);
}

module.exports = {
  DIVIDER,
  SECTION_DIVIDER,
  logBanner,
  logSection,
  logOk,
  logFail,
  logWarn,
  logInfo,
  logResult,
};
