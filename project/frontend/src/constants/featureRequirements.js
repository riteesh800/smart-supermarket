/**
 * Feature Data Requirements Definition
 *
 * Defines the dataset and column/data-type requirements needed to unlock
 * each feature in SmartMart AI. Used to display rich, informative hover cards
 * whenever a user hovers over a locked feature.
 */

export const FEATURE_DATA_REQUIREMENTS = {
  dashboard: {
    id: 'dashboard',
    flag: 'enable_dashboard',
    title: 'Dashboard Overview',
    icon: '📊',
    summary: 'Executive supermarket intelligence showing store-wide revenue, profit margins, active customers, low-stock warnings, and top-selling products.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Retail checkout records containing item quantities, prices, and timestamps.',
      alternative: 'Can be auto-loaded via the built-in demo dataset.'
    },
    columns: [
      { name: 'sale_id', type: 'String / ID', required: true, example: 'S000001', desc: 'Unique transaction line item code' },
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0028', desc: 'Product SKU reference code' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Number of units sold' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '65.32', desc: 'Total sale amount (or unit_price)' },
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Transaction date and time' },
      { name: 'customer_id', type: 'String / ID', required: false, example: 'C0925', desc: 'Customer account reference' },
      { name: 'discount', type: 'Float / Decimal', required: false, example: '0.0', desc: 'Discount percentage or amount' },
    ]
  },

  inventory: {
    id: 'inventory',
    flag: 'enable_inventory',
    title: 'Inventory Management',
    icon: '📦',
    summary: 'Warehouse stock tracking, real-time low-stock alerts, safety reorder thresholds, shelf distribution, and expiry monitoring.',
    dataset: {
      name: 'Inventory Stock Levels',
      filename: 'inventory.csv',
      icon: '📋',
      description: 'Warehouse stock counts, safety limits, and aisle storage locations.',
      alternative: 'Can also be auto-generated from products.csv.'
    },
    columns: [
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0001', desc: 'Product identifier code' },
      { name: 'current_stock', type: 'Integer', required: true, example: '68', desc: 'Current available stock on hand' },
      { name: 'max_stock', type: 'Integer', required: true, example: '200', desc: 'Maximum warehouse shelf capacity' },
      { name: 'reorder_point', type: 'Integer', required: true, example: '18', desc: 'Minimum safety threshold triggering reorder' },
      { name: 'warehouse_location', type: 'String / Text', required: false, example: 'Pune DC - Aisle 18 Shelf B', desc: 'Storage bin or aisle location' },
      { name: 'last_restock_date', type: 'Date / DateTime', required: false, example: '2026-09-06', desc: 'Last replenishment date' },
    ]
  },

  sales: {
    id: 'sales',
    flag: 'enable_sales',
    title: 'Sales Insights',
    icon: '🛍️',
    summary: 'Deep sales analytics with daily/monthly revenue trends, payment tender distributions, category revenue rankings, and item velocity.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Transaction bills and receipts with payment methods and prices.',
      alternative: 'Can be loaded with custom CSV or built-in demo dataset.'
    },
    columns: [
      { name: 'sale_id', type: 'String / ID', required: true, example: 'S000001', desc: 'Unique transaction receipt ID' },
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0028', desc: 'Product reference code' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Units purchased per item' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '65.32', desc: 'Final charged amount' },
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Date & time of sale' },
      { name: 'payment_method', type: 'String / Text', required: true, example: 'Debit Card', desc: 'Payment method (Cash, UPI, Card)' },
      { name: 'unit_price', type: 'Float / Currency', required: false, example: '32.66', desc: 'Base price per item' },
      { name: 'discount', type: 'Float / Decimal', required: false, example: '0.0', desc: 'Discount applied to sale' },
    ]
  },

  customers: {
    id: 'customers',
    flag: 'enable_customers',
    title: 'Customer Analytics',
    icon: '👥',
    summary: 'Demographic age and gender clustering, loyalty membership tiers, RFM customer segmentation, top spenders, and retention cohorts.',
    dataset: {
      name: 'Customer Profiles',
      filename: 'customers.csv',
      icon: '👥',
      description: 'Customer contact directory, demographic profiles, and loyalty tiers.',
      alternative: 'Also enabled if sales.csv includes customer_id.'
    },
    columns: [
      { name: 'customer_id', type: 'String / ID', required: true, example: 'C0001', desc: 'Unique loyalty customer identifier' },
      { name: 'first_name', type: 'String / Text', required: true, example: 'Pankaj', desc: 'Customer full or first name' },
      { name: 'email', type: 'String / Text', required: true, example: 'pankaj.mehta@example.com', desc: 'Customer contact email' },
      { name: 'membership_tier', type: 'String / Text', required: true, example: 'Silver', desc: 'Loyalty tier (Bronze, Silver, Gold, Platinum)' },
      { name: 'age', type: 'Integer', required: true, example: '37', desc: 'Age for demographic segmentation' },
      { name: 'gender', type: 'String / Text', required: true, example: 'M', desc: 'Gender identifier (M, F, Other)' },
      { name: 'loyalty_points', type: 'Integer', required: false, example: '2007', desc: 'Accumulated loyalty reward points' },
      { name: 'phone', type: 'String / Text', required: false, example: '+91 7306040784', desc: 'Mobile contact number' },
      { name: 'zip_code', type: 'String / Text', required: false, example: '600040', desc: 'Postal code for regional mapping' },
    ]
  },

  suppliers: {
    id: 'suppliers',
    flag: 'enable_suppliers',
    title: 'Suppliers & Logistics',
    icon: '🚚',
    summary: 'Vendor performance directory, average delivery lead times, reliability performance scoring, and supplier contact logistics.',
    dataset: {
      name: 'Suppliers & Logistics',
      filename: 'suppliers.csv',
      icon: '🚚',
      description: 'Vendor directory with delivery performance and contact info.',
      alternative: 'Also enabled if products.csv has a supplier column.'
    },
    columns: [
      { name: 'supplier_id', type: 'String / ID', required: true, example: 'SUP001', desc: 'Unique supplier identification code' },
      { name: 'name', type: 'String / Text', required: true, example: 'Amul (GCMMF)', desc: 'Supplier / vendor company name' },
      { name: 'contact_email', type: 'String / Text', required: true, example: 'orders@amul.coop', desc: 'Supplier business contact email' },
      { name: 'lead_time_days', type: 'Integer', required: true, example: '2', desc: 'Average fulfillment lead time in days' },
      { name: 'reliability_score', type: 'Float / Decimal', required: true, example: '0.96', desc: 'Reliability rating (0.0 to 1.0 or %)' },
    ]
  },

  forecast: {
    id: 'forecast',
    flag: 'enable_forecast',
    title: 'Demand Forecast',
    icon: '📈',
    summary: 'Machine learning time-series forecasting (Prophet / Moving Average) predicting upcoming customer demand and inventory replenishment needs.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Historical timestamped transactions used to train predictive models.',
      alternative: 'Requires historical transaction timestamps.'
    },
    columns: [
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Historical timestamp for time-series trends' },
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0028', desc: 'Product SKU to forecast' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Units sold per transaction for velocity calculations' },
      { name: 'category', type: 'String / Text', required: false, example: 'Dairy', desc: 'Product category for department-level forecasting' },
      { name: 'total_price', type: 'Float / Currency', required: false, example: '65.32', desc: 'Monetary transaction volume' },
    ]
  },

  recommendations: {
    id: 'recommendations',
    flag: 'enable_recommendations',
    title: 'Recommendations & Bundling',
    icon: '🤖',
    summary: 'AI Market Basket Analysis (Apriori association rules) discovering co-purchased items, cross-sell promotions, and high-affinity bundles.',
    dataset: {
      name: 'Market Basket Sales',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Transactions grouped by basket / order ID.',
      alternative: 'Needs basket_id or sale_id to group simultaneous purchases.'
    },
    columns: [
      { name: 'basket_id', type: 'String / ID', required: true, example: 'B000001', desc: 'Order / cart ID grouping items bought together' },
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0028', desc: 'Product SKU included in the basket' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Quantity of the item in the basket' },
      { name: 'timestamp', type: 'DateTime', required: false, example: '2026-04-19 20:40:02', desc: 'Checkout timestamp' },
    ]
  },

  pricing: {
    id: 'pricing',
    flag: 'enable_pricing',
    title: 'Dynamic Pricing',
    icon: '💲',
    summary: 'Price elasticity of demand estimation, revenue optimization simulations, and automated unit price recommendations.',
    dataset: {
      name: 'Sales Transactions & Products',
      filename: 'sales.csv & products.csv',
      icon: '💲',
      description: 'Historical sale prices paired with wholesale product costs.',
      alternative: 'Uses product catalog cost and sales transaction prices.'
    },
    columns: [
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0028', desc: 'Product identifier code' },
      { name: 'unit_price', type: 'Float / Currency', required: true, example: '32.66', desc: 'Historical selling price (or total_price)' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Demand volume at given price' },
      { name: 'cost', type: 'Float / Currency', required: true, example: '20.00', desc: 'Wholesale unit cost (in products.csv for margin modeling)' },
      { name: 'category', type: 'String / Text', required: false, example: 'Dairy', desc: 'Product category' },
    ]
  },

  heatmap: {
    id: 'heatmap',
    flag: 'enable_heatmap',
    title: 'Sales Heatmap',
    icon: '🔥',
    summary: '7x24 store traffic and revenue density matrix identifying peak shopping hours and busiest days of the week.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Timestamped sales records with hours and minutes.',
      alternative: 'Needs datetime timestamp format.'
    },
    columns: [
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Sale datetime containing hour and day (YYYY-MM-DD HH:MM:SS)' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '65.32', desc: 'Sales revenue amount generated' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Total items sold during the hour' },
      { name: 'basket_id', type: 'String / ID', required: false, example: 'B000001', desc: 'Transaction cart identifier' },
    ]
  },

  anomalies: {
    id: 'anomalies',
    flag: 'enable_anomalies',
    title: 'Anomalies & Fraud Detection',
    icon: '⚠️',
    summary: 'Statistical Z-score and Isolation Forest outlier detection highlighting unusual transaction sizes, heavy discounts, and off-hour sales.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Transaction logs evaluated for revenue and volume outliers.',
      alternative: 'Works directly with standard sales.csv.'
    },
    columns: [
      { name: 'sale_id', type: 'String / ID', required: true, example: 'S000001', desc: 'Unique transaction identifier' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '65.32', desc: 'Total charged amount to check for price anomalies' },
      { name: 'quantity', type: 'Integer', required: true, example: '2', desc: 'Units purchased to check for bulk volume anomalies' },
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Transaction timestamp for time-of-day anomalies' },
      { name: 'discount', type: 'Float / Decimal', required: false, example: '0.0', desc: 'Discount percentage or amount' },
      { name: 'customer_id', type: 'String / ID', required: false, example: 'C0925', desc: 'Customer account ID' },
    ]
  },

  // Additional flags supported in Data Setup status
  enable_profit: {
    id: 'profit',
    flag: 'enable_profit',
    title: 'Profit Margin Analytics',
    icon: '💰',
    summary: 'Analyzes gross margins and net profitability across products and categories.',
    dataset: {
      name: 'Sales & Products Catalog',
      filename: 'sales.csv & products.csv',
      icon: '💰',
      description: 'Sales volume paired with wholesale unit cost.',
    },
    columns: [
      { name: 'product_id', type: 'String / ID', required: true, example: 'P0001', desc: 'Product SKU' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '54.60', desc: 'Selling price revenue' },
      { name: 'quantity', type: 'Integer', required: true, example: '1', desc: 'Units sold' },
      { name: 'cost', type: 'Float / Currency', required: true, example: '28.51', desc: 'Wholesale product cost (in products.csv)' },
    ]
  },

  enable_demographics: {
    id: 'demographics',
    flag: 'enable_demographics',
    title: 'Demographic Insights',
    icon: '👥',
    summary: 'Age brackets, gender breakdowns, and loyalty tiers of your supermarket shopper base.',
    dataset: {
      name: 'Customer Profiles',
      filename: 'customers.csv',
      icon: '👥',
      description: 'Customer age, gender, and membership records.',
    },
    columns: [
      { name: 'customer_id', type: 'String / ID', required: true, example: 'C0001', desc: 'Customer identifier' },
      { name: 'age', type: 'Integer', required: true, example: '37', desc: 'Age in years' },
      { name: 'gender', type: 'String / Text', required: true, example: 'M', desc: 'Gender (M/F/Other)' },
      { name: 'membership_tier', type: 'String / Text', required: true, example: 'Silver', desc: 'Loyalty tier' },
    ]
  },

  enable_retention: {
    id: 'retention',
    flag: 'enable_retention',
    title: 'Retention & Churn Analytics',
    icon: '🔄',
    summary: 'Customer repeat visit frequency, churn risk scores, and cohort retention over time.',
    dataset: {
      name: 'Sales Transactions',
      filename: 'sales.csv',
      icon: '🛍️',
      description: 'Sales records linked with customer IDs and timestamps.',
    },
    columns: [
      { name: 'customer_id', type: 'String / ID', required: true, example: 'C0925', desc: 'Customer account ID' },
      { name: 'timestamp', type: 'DateTime', required: true, example: '2026-04-19 20:40:02', desc: 'Purchase date & time' },
      { name: 'total_price', type: 'Float / Currency', required: true, example: '65.32', desc: 'Purchase amount' },
    ]
  }
};

/**
 * Helper to get requirement data by either item ID (e.g. 'dashboard')
 * or flag name (e.g. 'enable_dashboard').
 */
export function getFeatureRequirement(keyOrFlag) {
  if (!keyOrFlag) return null;
  if (FEATURE_DATA_REQUIREMENTS[keyOrFlag]) {
    return FEATURE_DATA_REQUIREMENTS[keyOrFlag];
  }
  // Try matching by flag
  const match = Object.values(FEATURE_DATA_REQUIREMENTS).find(
    (item) => item.flag === keyOrFlag || item.id === keyOrFlag
  );
  if (match) return match;

  // Clean flag prefix (e.g. enable_dashboard -> dashboard)
  const cleaned = keyOrFlag.replace(/^enable_/, '');
  return FEATURE_DATA_REQUIREMENTS[cleaned] || null;
}
