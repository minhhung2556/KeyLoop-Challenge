export const COMPACT_CARD =
  "rounded-2xl bg-card p-4 shadow-sm border border-border";

export const COMPACT_PANEL =
  "rounded-2xl bg-card shadow-sm border border-border overflow-hidden";

export const COMPACT_CARD_TITLE = "text-base font-semibold text-foreground";

export const COMPACT_CARD_DESC = "text-sm text-muted-foreground mt-0.5";

export const COMPACT_LABEL = "text-sm font-medium text-muted-foreground";

export const COMPACT_META = "text-sm font-medium text-muted-foreground";

export const COMPACT_SECTION_LABEL =
  "text-sm font-semibold uppercase tracking-wide text-muted-foreground";

export const COMPACT_BODY = "text-sm text-foreground";

export const COMPACT_EMPTY_TEXT = "text-sm text-muted-foreground";

export const COMPACT_SECTION_GAP = "space-y-3";

export const BENTO_GRID_GAP = "gap-3 lg:gap-4";

// Monochrome bars with one accent highlight for primary data
export const CHART_PALETTE = [
  "#00b5d8",
  "#cbd5e1",
  "#94a3b8",
  "#64748b",
  "#475569",
  "#334155",
];

export const CHART_LINE_PRIMARY = "#00b5d8";
export const CHART_LINE_SECONDARY = "#94a3b8";
export const CHART_LINE_TERTIARY = "#0d9488";
export const CHART_LINE_QUATERNARY = "#6366f1";
export const CHART_BAR_PRIMARY = "#00b5d8";
export const CHART_BAR_SECONDARY = "#cbd5e1";

export const SUMMARY_PILL_CLASS = "rounded-xl bg-muted text-center";
export const SUMMARY_PILL_LABEL_CLASS =
  "text-sm font-semibold uppercase tracking-wide text-muted-foreground";
export const SUMMARY_PILL_VALUE_CLASS =
  "text-base font-bold tabular-nums text-foreground";

export function getCardClassName(compact, className = "") {
  const base = compact
    ? COMPACT_CARD
    : "rounded-3xl bg-card p-6 shadow-sm border border-border";
  return className ? `${base} ${className}` : base;
}

export function getChartHeight(
  compact,
  defaultHeight = "h-80",
  compactHeight = "h-52",
) {
  return compact ? compactHeight : defaultHeight;
}

export const NEUTRAL_CHART_COLORS = CHART_PALETTE;
