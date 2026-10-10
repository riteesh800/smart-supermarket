/**
 * Shared color system for category and chart colors.
 * Single source of truth — replaces scattered CATEGORY_COLORS / COLORS arrays.
 */

// Pre-defined palette for known categories from the SmartMart dataset.
// Visually distinct, dark-mode optimized colors.
const CATEGORY_PALETTE = {
  'Dairy':        '#00d4ff',
  'Bakery':       '#f59e0b',
  'Beverages':    '#10b981',
  'Snacks':       '#ec4899',
  'Fruits':       '#34d399',
  'Vegetables':   '#6366f1',
  'Meat':         '#ef4444',
  'Seafood':      '#14b8a6',
  'Frozen':       '#7c3aed',
  'Condiments':   '#f97316',
  'Cereal':       '#a78bfa',
  'Personal Care':'#06b6d4',
  'Household':    '#8b5cf6',
  'Baby':         '#fb923c',
  'Pet':          '#22d3ee',
};

// Fallback palette for unknown categories (cycles through these)
const CHART_COLORS = [
  '#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444',
  '#ec4899', '#6366f1', '#14b8a6', '#a78bfa', '#06b6d4',
  '#f97316', '#34d399', '#8b5cf6', '#fb923c', '#22d3ee',
  '#84cc16', '#e879f9', '#2dd4bf', '#fbbf24', '#f43f5e',
];

/**
 * Get a consistent color for a category name.
 * Uses the pre-defined palette for known categories,
 * falls back to a deterministic hash-based selection for unknowns.
 */
export function getCategoryColor(category, index) {
  if (CATEGORY_PALETTE[category]) return CATEGORY_PALETTE[category];
  if (typeof index === 'number') return CHART_COLORS[index % CHART_COLORS.length];
  // Deterministic fallback from string hash
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = ((hash << 5) - hash) + category.charCodeAt(i);
    hash |= 0;
  }
  return CHART_COLORS[Math.abs(hash) % CHART_COLORS.length];
}

/**
 * Get a color by index (for generic chart series).
 */
export function getChartColor(index) {
  return CHART_COLORS[index % CHART_COLORS.length];
}

export { CATEGORY_PALETTE, CHART_COLORS };
