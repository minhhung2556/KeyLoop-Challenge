import path from "node:path";
import { Transform } from "node:stream";
import { logFail, logOk, logWarn } from "./log-style.mjs";

/** @typedef {import('node:test/reporters').TestEvent} TestEvent */

const DETAIL_INDENT = "     ";
const MAX_STACK_LINES = 12;

/** @param {string | undefined} file */
function formatLocation(file, line, column) {
  if (!file) {
    return null;
  }
  const rel = path.isAbsolute(file) ? path.relative(process.cwd(), file) : file;
  const loc = rel.replace(/\\/g, "/");
  if (line != null && column != null) {
    return `${loc}:${line}:${column}`;
  }
  if (line != null) {
    return `${loc}:${line}`;
  }
  return loc;
}

/**
 * @param {Error | undefined} error
 * @param {Set<string>} seenMessages
 */
function collectErrorMessages(error, seenMessages) {
  /** @type {string[]} */
  const lines = [];
  let current = error;
  while (current) {
    const message = current.message?.trim();
    if (message && !seenMessages.has(message)) {
      seenMessages.add(message);
      lines.push(message);
    }
    current = current.cause instanceof Error ? current.cause : undefined;
  }
  return lines;
}

/**
 * @param {Error | undefined} error
 * @param {Set<string>} seenMessages
 */
function collectStackLines(error, seenMessages) {
  /** @type {string[]} */
  const out = [];
  const stack = error?.stack;
  if (!stack) {
    return out;
  }
  for (const line of stack.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }
    if (seenMessages.has(trimmed)) {
      continue;
    }
    if (trimmed === error?.message?.trim()) {
      continue;
    }
    if (
      trimmed.includes("node:internal") ||
      trimmed.includes("node:test") ||
      trimmed.startsWith("at Object.<anonymous>")
    ) {
      continue;
    }
    out.push(trimmed);
    if (out.length >= MAX_STACK_LINES) {
      break;
    }
  }
  return out;
}

/** @param {string[]} lines */
function logDetailLines(lines) {
  for (const line of lines) {
    console.error(`${DETAIL_INDENT}${line}`);
  }
}

/** @param {TestEvent["data"]} data */
function normalizeTestFile(data) {
  if (!data.file) {
    return "";
  }
  return path
    .relative(process.cwd(), path.resolve(data.file))
    .replace(/\\/g, "/");
}

/** @param {TestEvent["data"]} data */
function streamFileKey(data) {
  return normalizeTestFile(data);
}

export default class EmojiTestReporter extends Transform {
  constructor() {
    super({ objectMode: true });
    /** @type {Map<string, { stdout: string[]; stderr: string[] }>} */
    this._streams = new Map();
  }

  /** @param {TestEvent["data"]} data */
  _getStreamBucket(data) {
    const key = streamFileKey(data);
    let bucket = this._streams.get(key);
    if (!bucket) {
      bucket = { stdout: [], stderr: [] };
      this._streams.set(key, bucket);
    }
    return bucket;
  }

  /** @param {TestEvent["data"]} data */
  _discardStreamBucket(data) {
    this._streams.delete(streamFileKey(data));
  }

  /** @param {TestEvent["data"]} data */
  _flushStreamBucket(data) {
    const key = streamFileKey(data);
    const bucket = this._streams.get(key);
    this._streams.delete(key);
    if (!bucket) {
      return;
    }
    const stdout = bucket.stdout.join("").trim();
    const stderr = bucket.stderr.join("").trim();
    if (stdout) {
      logDetailLines(["stdout:", ...stdout.split("\n")]);
    }
    if (stderr) {
      logDetailLines(["stderr:", ...stderr.split("\n")]);
    }
  }

  /** @param {TestEvent["data"]} data */
  _logFailureDetails(data) {
    const error = data.details?.error;
    const seenMessages = new Set();
    const messageLines = collectErrorMessages(error, seenMessages);
    const location = formatLocation(data.file, data.line, data.column);
    const detailLines = [];
    if (messageLines.length) {
      detailLines.push(...messageLines);
    }
    if (location) {
      detailLines.push(`at ${location}`);
    }
    detailLines.push(...collectStackLines(error, seenMessages));
    if (detailLines.length) {
      logDetailLines(detailLines);
    }
    this._flushStreamBucket(data);
  }

  /** @param {TestEvent} event */
  _transform(event, _encoding, callback) {
    switch (event.type) {
      case "test:pass":
        this._discardStreamBucket(event.data);
        logOk(event.data.name);
        break;
      case "test:fail":
        logFail(event.data.name);
        this._logFailureDetails(event.data);
        break;
      case "test:skip":
        this._discardStreamBucket(event.data);
        logWarn(`${event.data.name} (skipped)`);
        break;
      case "test:stdout": {
        const bucket = this._getStreamBucket(event.data);
        bucket.stdout.push(event.data.message ?? "");
        break;
      }
      case "test:stderr": {
        const bucket = this._getStreamBucket(event.data);
        bucket.stderr.push(event.data.message ?? "");
        break;
      }
      default:
        break;
    }
    callback();
  }
}
