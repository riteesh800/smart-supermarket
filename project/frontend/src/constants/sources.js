/**
 * Source mapping configurations for each feature across the frontend.
 * Specifies the exact CSV file(s) and only the relevant column(s)
 * used to represent each chart, card, metric, or table.
 */

export const SOURCES = {
  // ─── DASHBOARD OVERVIEW ───
  dashboard: {
    kpiTotalRevenue: [
      { file: 'sales.csv', columns: ['total_price'] }
    ],
    kpiTotalProfit: [
      { file: 'sales.csv', columns: ['total_price', 'quantity'] },
      { file: 'products.csv', columns: ['cost', 'price'] }
    ],
    kpiCustomers: [
      { file: 'customers.csv', columns: ['customer_id'] }
    ],
    kpiTransactions: [
      { file: 'sales.csv', columns: ['sale_id', 'basket_id', 'total_price'] }
    ],
    kpiLowStock: [
      { file: 'inventory.csv', columns: ['current_stock', 'reorder_point'] }
    ],
    kpiTopCategory: [
      { file: 'sales.csv', columns: ['product_id', 'total_price'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ],
    dailyRevenueTrend: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    monthlyRevenue: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    topProducts: [
      { file: 'sales.csv', columns: ['product_id', 'total_price'] },
      { file: 'products.csv', columns: ['product_id', 'name'] }
    ],
    lowStockAlerts: [
      { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
      { file: 'products.csv', columns: ['product_id', 'name'] }
    ]
  },

  // ─── INVENTORY MANAGEMENT ───
  inventory: {
    kpiTotalProducts: [
      { file: 'products.csv', columns: ['product_id'] }
    ],
    kpiLowStock: [
      { file: 'inventory.csv', columns: ['current_stock', 'reorder_point'] }
    ],
    kpiExpiringSoon: [
      { file: 'inventory.csv', columns: ['last_restock_date'] },
      { file: 'products.csv', columns: ['shelf_life_days'] }
    ],
    kpiCategories: [
      { file: 'products.csv', columns: ['category'] }
    ],
    stockByCategory: [
      { file: 'inventory.csv', columns: ['product_id', 'current_stock'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ],
    productDistribution: [
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ],
    expiringSoon: [
      { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'last_restock_date'] },
      { file: 'products.csv', columns: ['product_id', 'name', 'shelf_life_days'] }
    ],
    lowStockAlerts: [
      { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
      { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
    ],
    allProductsTable: [
      { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price', 'cost', 'supplier', 'shelf_life_days', 'unit'] },
      { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'max_stock', 'reorder_point', 'last_restock_date', 'warehouse_location'] }
    ]
  },

  // ─── SALES INSIGHTS ───
  sales: {
    kpiTotalRevenue: [
      { file: 'sales.csv', columns: ['total_price'] }
    ],
    kpiTransactions: [
      { file: 'sales.csv', columns: ['sale_id'] }
    ],
    kpiAvgDailyRevenue: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    kpiTopProduct: [
      { file: 'sales.csv', columns: ['product_id', 'total_price'] },
      { file: 'products.csv', columns: ['product_id', 'name'] }
    ],
    revenueTrend: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price', 'sale_id'] }
    ],
    bestSellers: [
      { file: 'sales.csv', columns: ['product_id', 'quantity', 'total_price'] },
      { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
    ],
    revenueByCategory: [
      { file: 'sales.csv', columns: ['product_id', 'total_price'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ]
  },

  // ─── CUSTOMER ANALYTICS ───
  customers: {
    kpiChampions: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    kpiLoyal: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    kpiPotential: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    kpiAtRisk: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    kpiLost: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    customerSegments: [
      { file: 'customers.csv', columns: ['customer_id'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    rfmScatter: [
      { file: 'customers.csv', columns: ['customer_id', 'first_name', 'last_name', 'membership_tier'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ],
    ageDistribution: [
      { file: 'customers.csv', columns: ['age'] }
    ],
    membershipTiers: [
      { file: 'customers.csv', columns: ['membership_tier'] }
    ],
    retentionChart: [
      { file: 'sales.csv', columns: ['timestamp', 'customer_id', 'total_price'] }
    ],
    topCustomersTable: [
      { file: 'customers.csv', columns: ['customer_id', 'first_name', 'last_name', 'membership_tier'] },
      { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
    ]
  },

  // ─── DEMAND FORECASTING ───
  forecast: {
    demandChart: [
      { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ],
    forecastTable: [
      { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ],
    modelSummary: [
      { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'category'] }
    ]
  },

  // ─── RECOMMENDATIONS & PRICING ───
  recommendations: {
    kpiRestock: [
      { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'name'] }
    ],
    kpiPriceIncrease: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] },
      { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
    ],
    kpiPriceDecrease: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] },
      { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
    ],
    kpiAssociationRules: [
      { file: 'sales.csv', columns: ['basket_id', 'product_id'] }
    ],
    productSuggestions: [
      { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
    ],
    associationRules: [
      { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
      { file: 'products.csv', columns: ['product_id', 'name'] }
    ],
    dynamicPricingTable: [
      { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price'] },
      { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
      { file: 'sales.csv', columns: ['product_id', 'quantity', 'timestamp'] }
    ]
  },

  // ─── DYNAMIC PRICING INTELLIGENCE ───
  pricing: {
    kpiPriceIncreases: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] },
      { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
    ],
    kpiPriceDecreases: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] },
      { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
    ],
    kpiHold: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] }
    ],
    kpiAvgChange: [
      { file: 'products.csv', columns: ['price'] }
    ],
    priceChangeDistribution: [
      { file: 'products.csv', columns: ['price'] },
      { file: 'inventory.csv', columns: ['current_stock'] },
      { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
    ],
    pricingSuggestionsTable: [
      { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price', 'shelf_life_days'] },
      { file: 'inventory.csv', columns: ['product_id', 'current_stock'] },
      { file: 'sales.csv', columns: ['product_id', 'quantity', 'timestamp'] }
    ]
  },

  // ─── ANOMALY DETECTION ───
  anomalies: {
    kpiTotalAnomalies: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    kpiSalesSpikes: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    kpiSalesDrops: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    kpiModel: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    salesTimeline: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
    ],
    anomalyDetailsTable: [
      { file: 'sales.csv', columns: ['timestamp', 'total_price', 'sale_id'] }
    ]
  },

  // ─── SUPPLIER MANAGEMENT ───
  suppliers: {
    kpiTotalSuppliers: [
      { file: 'suppliers.csv', columns: ['supplier_id'] }
    ],
    kpiAvgReliability: [
      { file: 'suppliers.csv', columns: ['reliability_score'] }
    ],
    kpiProductsSupplied: [
      { file: 'suppliers.csv', columns: ['supplier_id'] },
      { file: 'products.csv', columns: ['product_id', 'supplier_id'] }
    ],
    kpiAvgLeadTime: [
      { file: 'suppliers.csv', columns: ['lead_time_days'] }
    ],
    revenueBySupplier: [
      { file: 'suppliers.csv', columns: ['supplier_id', 'name'] },
      { file: 'products.csv', columns: ['supplier_id', 'product_id'] },
      { file: 'sales.csv', columns: ['product_id', 'total_price'] }
    ],
    productsSupplied: [
      { file: 'suppliers.csv', columns: ['supplier_id', 'name'] },
      { file: 'products.csv', columns: ['supplier_id', 'product_id'] }
    ],
    supplierPerformanceTable: [
      { file: 'suppliers.csv', columns: ['supplier_id', 'name', 'contact_email', 'lead_time_days', 'reliability_score'] },
      { file: 'products.csv', columns: ['supplier_id', 'product_id', 'category'] },
      { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] }
    ]
  },

  // ─── SALES HEATMAP & ANALYTICS ───
  heatmap: {
    kpiTotalProfit: [
      { file: 'sales.csv', columns: ['total_price', 'quantity'] },
      { file: 'products.csv', columns: ['cost', 'price'] }
    ],
    kpiOverallMargin: [
      { file: 'sales.csv', columns: ['total_price', 'quantity'] },
      { file: 'products.csv', columns: ['cost', 'price'] }
    ],
    kpiPaymentMethods: [
      { file: 'sales.csv', columns: ['payment_method'] }
    ],
    kpiPeakHours: [
      { file: 'sales.csv', columns: ['timestamp'] }
    ],
    hourlyHeatmap: [
      { file: 'sales.csv', columns: ['timestamp'] }
    ],
    paymentMethods: [
      { file: 'sales.csv', columns: ['payment_method', 'total_price'] }
    ],
    profitMarginByCategory: [
      { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] },
      { file: 'products.csv', columns: ['product_id', 'category', 'cost', 'price'] }
    ],
    categoryProfitBreakdownTable: [
      { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] },
      { file: 'products.csv', columns: ['product_id', 'category', 'cost', 'price'] }
    ]
  }
};
