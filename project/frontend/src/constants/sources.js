/**
 * Feature Metadata and Source Mapping Configuration
 *
 * For each feature across all panels in SmartMart AI:
 * - title: Human-readable feature name
 * - whatItShows: Plain English (2-4 lines) explaining what the feature is and what it gives
 * - howItCalculated: Exact formula and logic using dynamic column tokens {table:column}
 * - useCase: Business purpose and practical decision value
 * - sources: Referenced dataset file(s) and columns used (columns are resolved dynamically)
 */

export const SOURCES = {
  // ─────────────────────────────────────────────
  // 1. DASHBOARD OVERVIEW
  // ─────────────────────────────────────────────
  dashboard: {
    kpiTotalRevenue: {
      title: 'Total Gross Revenue',
      whatItShows: 'This feature is the main sales tracker of your supermarket. It shows the total cash earned from all customer purchases after discounts. It gives you a clear look at total income so you know whether your store is meeting its daily and monthly revenue targets.',
      howItCalculated: 'Calculated by taking the grand sum of {sales:total_price} across all completed sales transactions: Σ({sales:total_price}). If line-item discounts were applied, it reflects the net amount charged to the shopper.',
      useCase: 'Primary top-line financial KPI used to monitor store cash flow, track performance against daily sales targets, and assess overall business growth.',
      sources: [
        { file: 'sales.csv', columns: ['total_price'] }
      ]
    },
    kpiTotalProfit: {
      title: 'Total Gross Profit',
      whatItShows: 'This feature is the true earnings metric of your store. It subtracts the wholesale cost you paid for goods from the retail prices customers paid. It gives you your real take-home profit so you know if your margins are healthy after covering product costs.',
      howItCalculated: 'Calculated by joining sales with products on product identifier and computing: Σ({sales:total_price} - ({sales:quantity} × {products:cost})). For products with wholesale cost data, it measures net merchandise profit.',
      useCase: 'Essential for evaluating true store profitability beyond top-line revenue, ensuring merchandise margins adequately cover operating overheads.',
      sources: [
        { file: 'sales.csv', columns: ['total_price', 'quantity'] },
        { file: 'products.csv', columns: ['cost', 'price'] }
      ]
    },
    kpiCustomers: {
      title: 'Active Customer Base',
      whatItShows: 'This feature is a counter of your store community. It shows the total number of unique shoppers and registered loyalty club members who have bought items. It gives you the size of your customer base so you know whether your store is attracting and keeping shoppers.',
      howItCalculated: 'Calculated as the distinct count of customer identifiers: COUNT(DISTINCT {customers:customer_id}) across the customer directory.',
      useCase: 'Tracks customer base expansion, loyalty club enrollment penetration, and total addressable repeat shoppers for promotional reach.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] }
      ]
    },
    kpiTransactions: {
      title: 'Total Transactions',
      whatItShows: 'This feature measures checkout register activity. It shows the total count of completed receipts and shopping baskets processed at your billing counters. It gives you an exact picture of customer traffic and cashier workload across the day.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {sales:sale_id}) or COUNT(DISTINCT {sales:basket_id}) across all recorded sale rows in the transaction ledger.',
      useCase: 'Measures register footfall throughput, cashier operational workload, and checkout lane traffic volume.',
      sources: [
        { file: 'sales.csv', columns: ['sale_id', 'basket_id', 'total_price'] }
      ]
    },
    kpiLowStock: {
      title: 'Low Stock Item Warnings',
      whatItShows: 'This feature is an urgent inventory warning alert. It counts all products where remaining warehouse units are below their safe minimum reorder level. It gives you an early warning so you can reorder before shelves run empty and customers leave unhappy.',
      howItCalculated: 'Calculated by evaluating inventory records: COUNT(*) where {inventory:current_stock} <= {inventory:reorder_point}.',
      useCase: 'Immediate supply chain alert that prevents out-of-stock events and shelf voids by signaling replenishment purchase orders.',
      sources: [
        { file: 'inventory.csv', columns: ['current_stock', 'reorder_point'] }
      ]
    },
    kpiTopCategory: {
      title: 'Leading Merchandise Category',
      whatItShows: 'This feature highlights your store top revenue engine. It identifies which aisle or department (such as Dairy, Produce, or Beverages) generated the highest total sales. It gives you immediate clarity on which department is bringing in the most money so you can give it prime shelf space.',
      howItCalculated: 'Aggregates {sales:total_price} grouped by {products:category} via item identifier join, finding MAX(SUM({sales:total_price})).',
      useCase: 'Informs merchandising executives which department drives the most cash flow, guiding prime floor space and shelf allocation.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    },
    dailyRevenueTrend: {
      title: 'Daily Revenue Trajectory',
      whatItShows: 'This feature is a visual day-by-day sales graph. It plots your daily revenue from day to day to reveal sales ups and downs over time. It gives you clear visibility into busy days like weekends versus slower weekdays so you can schedule staff and restock accordingly.',
      howItCalculated: 'Groups transactions by DATE({sales:timestamp}) and calculates aggregate SUM({sales:total_price}) for each consecutive calendar day.',
      useCase: 'Identifies weekly sales cycles, weekend shopping surges, and day-of-week demand trends to optimize staffing and stock replenishment.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    monthlyRevenue: {
      title: 'Monthly Revenue Comparison',
      whatItShows: 'This feature is a high-level monthly income comparison. It compares total money made month by month across the year. It gives you seasonal growth trends and long-term financial patterns so you know whether your business is expanding over time.',
      howItCalculated: 'Groups transactions by STRFTIME("%Y-%m", {sales:timestamp}) and calculates aggregate SUM({sales:total_price}) per calendar month.',
      useCase: 'Supports high-level executive financial planning, seasonal revenue forecasting, and month-over-month growth auditing.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    topProducts: {
      title: 'Top Performing Products',
      whatItShows: 'This feature is a leaderboard of your top bestselling items. It ranks individual products based on total sales money and units sold. It gives you a clear list of your store most popular items so you can keep them well-stocked and placed at eye level.',
      howItCalculated: 'Joins sales with product catalog on item ID, groups by {sales:product_id} and {products:name}, computes SUM({sales:total_price}), and ranks descending.',
      useCase: 'Ensures store managers never run out of flagship revenue-driving items and highlights candidates for prominent aisle-end cap displays.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price'] },
        { file: 'products.csv', columns: ['product_id', 'name'] }
      ]
    },
    lowStockAlerts: {
      title: 'Low Stock Priority Workbench',
      whatItShows: 'This feature is an actionable reordering checklist. It displays products that are running dangerously low on stock along with the exact deficit needed to refill shelves. It gives inventory managers an instant priority list to place vendor orders before items run out completely.',
      howItCalculated: 'Filters where {inventory:current_stock} <= {inventory:reorder_point}, joined with {products:name}, calculating shortage ({inventory:reorder_point} - {inventory:current_stock}).',
      useCase: 'Empowers inventory procurement clerks to quickly initiate bulk vendor purchase orders before shelves empty.',
      sources: [
        { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
        { file: 'products.csv', columns: ['product_id', 'name'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 2. INVENTORY MANAGEMENT
  // ─────────────────────────────────────────────
  inventory: {
    kpiTotalProducts: {
      title: 'Total Catalog SKUs',
      whatItShows: 'This feature counts your entire product catalog. It shows the total number of distinct items and varieties available in your supermarket. It gives you a measure of product variety so you know how broad your merchandise selection is for shoppers.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {products:product_id}) across all active records in the products database.',
      useCase: 'Measures catalog breadth, assortment variety, and supermarket inventory diversification across merchandise lines.',
      sources: [
        { file: 'products.csv', columns: ['product_id'] }
      ]
    },
    kpiLowStock: {
      title: 'Low Stock Warnings',
      whatItShows: 'This feature is a real-time count of items needing replenishment. It tallies all products whose warehouse stock has fallen below the safety reorder point. It gives you quick notification to order stock so everyday essentials stay on the shelves.',
      howItCalculated: 'Evaluated as COUNT(*) from inventory where {inventory:current_stock} <= {inventory:reorder_point}.',
      useCase: 'Prevents stockouts on high-turnover staples, reducing lost sales and preserving customer satisfaction.',
      sources: [
        { file: 'inventory.csv', columns: ['current_stock', 'reorder_point'] }
      ]
    },
    kpiExpiringSoon: {
      title: 'Perishables Expiring Soon',
      whatItShows: 'This feature is a perishable food safety tracker. It counts items that will expire within the next 7 days based on when they arrived and their shelf life. It gives you time to put them on discount or use them quickly before they spoil and cause financial losses.',
      howItCalculated: 'Calculated by evaluating ({inventory:last_restock_date} + {products:shelf_life_days} days) - CurrentDate <= 7 days for items with {inventory:current_stock} > 0.',
      useCase: 'Reduces food waste and shrinkage costs by enabling prompt markdowns, clearance bundles, or prepared food conversion.',
      sources: [
        { file: 'inventory.csv', columns: ['last_restock_date'] },
        { file: 'products.csv', columns: ['shelf_life_days'] }
      ]
    },
    kpiCategories: {
      title: 'Merchandise Departments',
      whatItShows: 'This feature shows the number of store departments. It counts distinct categories like Bakery, Dairy, Produce, and Snacks. It gives you a simple view of store organization so you can balance shelf space and categorize suppliers easily.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {products:category}) from the master products catalog.',
      useCase: 'Organizes store aisle zoning, vendor categorization, and merchandise group performance analysis.',
      sources: [
        { file: 'products.csv', columns: ['category'] }
      ]
    },
    stockByCategory: {
      title: 'Stock Units by Department',
      whatItShows: 'This feature shows how physical units are distributed across departments. It displays a bar chart comparing total warehouse items stored in each category. It gives you visibility into storage use so you can avoid overloading warehouse space with slow-moving goods.',
      howItCalculated: 'Joins inventory with products on item ID, groups by {products:category}, and calculates SUM({inventory:current_stock}).',
      useCase: 'Ensures warehouse space and capital investment are allocated appropriately without over-stocking slow-turn departments.',
      sources: [
        { file: 'inventory.csv', columns: ['product_id', 'current_stock'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    },
    productDistribution: {
      title: 'Product Variety Distribution',
      whatItShows: 'This feature shows product variety per category as a pie or donut chart. It reveals what percentage of your store total SKUs belong to each department. It gives buyers insight into whether any category has too few options or too many duplicate items.',
      howItCalculated: 'Computes COUNT({products:product_id}) per {products:category} divided by total store SKUs × 100%.',
      useCase: 'Assists category managers in balancing product assortment and identifying under-represented grocery categories.',
      sources: [
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    },
    expiringSoon: {
      title: 'Expiry Monitoring Workbench',
      whatItShows: 'This feature is a detailed watchlist for perishable food. It lists each expiring product with days remaining until expiration and units left in stock. It gives floor managers actionable items to mark down with clearance stickers or sell immediately before they go bad.',
      howItCalculated: 'Joins inventory and products, calculating DaysRemaining = {products:shelf_life_days} - (Today - {inventory:last_restock_date}), filtering where DaysRemaining <= 7.',
      useCase: 'Enables department supervisors to affix discount stickers, rotate stock (FIFO), or initiate promotional sales to clear perishable stock.',
      sources: [
        { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'last_restock_date'] },
        { file: 'products.csv', columns: ['product_id', 'name', 'shelf_life_days'] }
      ]
    },
    lowStockAlerts: {
      title: 'Safety Stock Reorder Matrix',
      whatItShows: 'This feature is an automatic replenishment guide. It lists out-of-stock and low-stock items with current stock, threshold, and recommended reorder quantities. It gives procurement clerks ready-to-use reorder quantities so they can submit supplier orders without manual math.',
      howItCalculated: 'Filters where {inventory:current_stock} <= {inventory:reorder_point}, joined with {products:name} and {products:category}, prioritizing by largest deficit.',
      useCase: 'Provides automated purchase order quantities ({inventory:max_stock} - {inventory:current_stock}) for swift vendor reordering.',
      sources: [
        { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
        { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
      ]
    },
    allProductsTable: {
      title: 'Master Inventory & Catalog Directory',
      whatItShows: 'This feature is your complete store inventory master spreadsheet. It shows every product name, category, price, cost, profit margin, stock count, and warehouse shelf location. It gives managers a single searchable place to look up details, do audits, and update stock.',
      howItCalculated: 'Complete multi-column join between {products:product_id} and {inventory:product_id}, computing unit margin ({products:price} - {products:cost}) and stock ratios.',
      useCase: 'Central operational directory for inventory audits, warehouse bin lookups, manual stock adjustments, and supplier tracking.',
      sources: [
        { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price', 'cost', 'supplier', 'shelf_life_days', 'unit'] },
        { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'max_stock', 'reorder_point', 'last_restock_date', 'warehouse_location'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 3. SALES INSIGHTS
  // ─────────────────────────────────────────────
  sales: {
    kpiTotalRevenue: {
      title: 'Total Gross Sales',
      whatItShows: 'This feature shows the grand total of money collected at checkouts. It aggregates every rupee or dollar paid by customers across all registers. It gives you a clear high-level financial summary to evaluate store revenue performance against business targets.',
      howItCalculated: 'Calculated by summing all completed transaction values: SUM({sales:total_price}) across the entire sales ledger.',
      useCase: 'Benchmark financial indicator for daily revenue audits, executive reporting, and sales growth tracking.',
      sources: [
        { file: 'sales.csv', columns: ['total_price'] }
      ]
    },
    kpiTransactions: {
      title: 'Transaction Volume',
      whatItShows: 'This feature counts total customer checkout sessions. It tracks every bill printed and payment made at the store. It gives you an exact measurement of customer footfall and checkout counter productivity throughout the day.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {sales:sale_id}) across all transaction records.',
      useCase: 'Measures store customer traffic volume, register workload, and average transaction cadence.',
      sources: [
        { file: 'sales.csv', columns: ['sale_id'] }
      ]
    },
    kpiAvgDailyRevenue: {
      title: 'Average Daily Revenue',
      whatItShows: 'This feature shows typical revenue generated on an average business day. It divides total sales by the number of operational days. It gives you an everyday baseline so you can immediately spot whether a particular day performed above or below expectations.',
      howItCalculated: 'Calculated as SUM({sales:total_price}) divided by COUNT(DISTINCT DATE({sales:timestamp})).',
      useCase: 'Establishes an operational benchmark to assess daily sales targets and measure promotional lifts.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    kpiTopProduct: {
      title: 'Top Grossing Product',
      whatItShows: 'This feature shows the number-one revenue champion in your store. It pinpoints the single item that has brought in the most sales cash overall. It gives you instant knowledge of your flagship item so you can make sure it is never out of stock.',
      howItCalculated: 'Groups sales by {sales:product_id}, joins with {products:name}, sums {sales:total_price}, and selects the top item.',
      useCase: 'Identifies the supermarket flagship hero product to ensure zero out-of-stocks and priority merchandising.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price'] },
        { file: 'products.csv', columns: ['product_id', 'name'] }
      ]
    },
    revenueTrend: {
      title: 'Daily Revenue & Volume Trend',
      whatItShows: 'This feature charts daily revenue together with transaction volume over time. It shows lines for money earned and customer count on the same timeline. It gives you insight into whether revenue grew because more people visited or because customers bought larger baskets.',
      howItCalculated: 'Groups by DATE({sales:timestamp}), calculating daily SUM({sales:total_price}) and COUNT(DISTINCT {sales:sale_id}).',
      useCase: 'Helps managers evaluate whether revenue growth is driven by increased customer volume or larger basket sizes.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price', 'sale_id'] }
      ]
    },
    bestSellers: {
      title: 'Top 10 Best Sellers',
      whatItShows: 'This feature ranks the top 10 bestselling products in the store. It shows each item name, category, units sold, and revenue generated. It gives merchandising managers quick insight into customer favorites so they can plan bundles and supplier discounts.',
      howItCalculated: 'Groups by {sales:product_id}, joins {products:name} and {products:category}, calculating SUM({sales:quantity}) and SUM({sales:total_price}), ordered descending.',
      useCase: 'Guides replenishment priorities, end-cap feature displays, and supplier volume rebate negotiations.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'quantity', 'total_price'] },
        { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
      ]
    },
    revenueByCategory: {
      title: 'Category Revenue Share',
      whatItShows: 'This feature displays sales revenue contribution broken down by department. It shows which categories contribute what percentage to overall sales. It gives leadership the data needed to allocate aisle space and marketing budget to the most profitable sections.',
      howItCalculated: 'Joins sales with product catalog, groups by {products:category}, sums {sales:total_price}, and computes percentage of total revenue.',
      useCase: 'Guides executive department space allocation and informs supplier vendor margin reviews.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 4. CUSTOMER ANALYTICS
  // ─────────────────────────────────────────────
  customers: {
    kpiChampions: {
      title: 'Champions Segment',
      whatItShows: 'This feature counts your most valuable VIP shoppers. It finds customers who visit frequently, bought very recently, and spend the most money. It gives you your top customer list so you can reward them with exclusive perks and keep them loyal for life.',
      howItCalculated: 'RFM segmentation scoring: Recency >= 4, Frequency >= 4, and Monetary >= 4 based on {sales:timestamp}, {sales:customer_id}, and {sales:total_price}.',
      useCase: 'Target group for exclusive VIP loyalty perks, personalized concierge service, and early access to premium promotions.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    kpiLoyal: {
      title: 'Loyal Customers Segment',
      whatItShows: 'This feature counts your dependable repeat shoppers. It identifies customers who visit on a regular schedule and steadily spend money. It gives you a core audience for loyalty point multipliers and cross-category recommendations.',
      howItCalculated: 'RFM segmentation scoring: Frequency >= 3 and Recency >= 3 with consistent transaction spend in {sales:total_price}.',
      useCase: 'Prime candidates for membership tier upgrades, cross-category recommendations, and customer advocacy programs.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    kpiPotential: {
      title: 'Potential Loyalists',
      whatItShows: 'This feature tracks promising newer shoppers with good basket sizes. It identifies customers who shopped recently and spend well but have not visited enough times yet. It gives you the best targets for welcome-back coupons to turn them into habitual shoppers.',
      howItCalculated: 'RFM segmentation scoring: Recency >= 4, Frequency 2-3, and above-median spend in {sales:total_price}.',
      useCase: 'Ideal recipients for welcome-back bonus points, personalized coupons, and targeted digital app notifications.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    kpiAtRisk: {
      title: 'At Risk Customers',
      whatItShows: 'This feature is a customer churn warning alert. It highlights shoppers who used to buy frequently and spend heavily, but have not visited in a long time. It gives marketers a timely alert to send win-back discount vouchers before these customers are lost forever.',
      howItCalculated: 'RFM segmentation scoring: Recency <= 2 but historical Frequency >= 3 and high Monetary lifetime spend in {sales:total_price}.',
      useCase: 'Immediate trigger for automated win-back discount vouchers and customer satisfaction check-in surveys to stop customer churn.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    kpiLost: {
      title: 'Lost / Dormant Shoppers',
      whatItShows: 'This feature counts inactive customer accounts. It identifies people who have stopped visiting the supermarket and have not made a purchase in many months. It gives you a measurement of customer churn and a list for automated low-cost re-engagement emails.',
      howItCalculated: 'RFM segmentation scoring: Recency <= 1 and low frequency/monetary metrics across {sales:timestamp} records.',
      useCase: 'Helps calculate annual customer churn rates and run cost-effective automated re-activation campaigns.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    customerSegments: {
      title: 'RFM Behavioral Segmentation',
      whatItShows: 'This feature shows your entire customer base divided into 5 behavior groups. It categorizes shoppers by how recently they bought, how often they shop, and how much they spend. It gives you a strategic overview to plan tailored marketing offers for every customer type.',
      howItCalculated: 'Quantile ranking (1-5) on customer Recency (days since last {sales:timestamp}), Frequency (transaction count), and Monetary (sum of {sales:total_price}).',
      useCase: 'Gives management a structured framework for targeted marketing, preventing churn and maximizing customer lifetime value.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    rfmScatter: {
      title: 'Recency vs Lifetime Spend Matrix',
      whatItShows: 'This feature maps every individual customer on a visual 2D scatter graph. It plots how many days have passed since their last visit against how much total money they have spent. It gives managers a quick visual way to spot high-spenders who are slipping away.',
      howItCalculated: 'X-axis = days since last transaction {sales:timestamp}, Y-axis = SUM({sales:total_price}), colored by loyalty tier from {customers:membership_tier}.',
      useCase: 'Visually identifies high-value VIP shoppers drifting into churn territory for urgent personalized outreach.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id', 'first_name', 'last_name', 'membership_tier'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    },
    ageDistribution: {
      title: 'Customer Age Demographics',
      whatItShows: 'This feature shows the age breakdown of your shoppers. It groups customers into age ranges like young adults, families, and seniors. It gives category buyers the demographic data needed to curate products that match what their dominant age groups want to buy.',
      howItCalculated: 'Buckets {customers:age} into demographic ranges and calculates aggregate COUNT(*) per age group.',
      useCase: 'Helps category buyers curate products tailored to the dominant age groups (e.g. ready-to-eat meals vs organic wellness).',
      sources: [
        { file: 'customers.csv', columns: ['age'] }
      ]
    },
    membershipTiers: {
      title: 'Loyalty Tier Breakdown',
      whatItShows: 'This feature shows how shoppers are distributed across loyalty levels. It displays the share of members in Bronze, Silver, Gold, and Platinum tiers. It gives you insight into whether your loyalty rewards motivate customers to spend more to level up.',
      howItCalculated: 'Groups by {customers:membership_tier} and calculates member count and percentage share.',
      useCase: 'Monitors loyalty tier progression and gauges the effectiveness of loyalty gamification rewards.',
      sources: [
        { file: 'customers.csv', columns: ['membership_tier'] }
      ]
    },
    retentionChart: {
      title: 'Monthly Cohort Retention',
      whatItShows: 'This feature tracks customer loyalty over months. It shows what percentage of shoppers who joined in a given month continue returning to shop in future months. It gives you the true test of supermarket customer stickiness and repeat shopping habits.',
      howItCalculated: 'Groups customers by acquisition month (first {sales:timestamp}) and calculates percentage active in each subsequent calendar month.',
      useCase: 'Gold standard metric for assessing supermarket brand loyalty and measuring long-term customer stickiness.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'customer_id', 'total_price'] }
      ]
    },
    topCustomersTable: {
      title: 'Top Spending Customer Directory',
      whatItShows: 'This feature is a hall of fame directory of your highest-paying patrons. It ranks shoppers by total spend and shows their loyalty tier and visit counts. It gives store managers names and details to offer personalized greetings, gifts, and VIP customer service.',
      howItCalculated: 'Groups by {customers:customer_id}, summing {sales:total_price} and counting {sales:sale_id}, sorted descending.',
      useCase: 'Allows store general managers to personally recognize top VIP patrons with exclusive courtesy benefits.',
      sources: [
        { file: 'customers.csv', columns: ['customer_id', 'first_name', 'last_name', 'membership_tier'] },
        { file: 'sales.csv', columns: ['customer_id', 'timestamp', 'total_price'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 5. DEMAND FORECASTING
  // ─────────────────────────────────────────────
  forecast: {
    demandChart: {
      title: '30-Day Predictive Demand Curve',
      whatItShows: 'This feature uses AI machine learning to look into the future. It predicts how many product units customers will buy every day over the next 30 days with confidence bands. It gives inventory planners future visibility so they can stock up before demand surges.',
      howItCalculated: 'Trained time-series model (Ridge Regression / ARIMA / Prophet) on daily aggregated {sales:quantity} grouped by DATE({sales:timestamp}) and {products:category}, producing predicted values (y_hat) and 95% confidence intervals.',
      useCase: 'Allows inventory managers to proactively order goods ahead of predicted surges, avoiding costly stockouts.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    },
    forecastTable: {
      title: 'Daily Projected Demand Table',
      whatItShows: 'This feature is an itemized day-by-day forecast table. It lists exact predicted unit sales alongside low and high estimates for each upcoming date. It gives warehouse logistics teams exact numbers to plan delivery trucks and daily staffing schedules.',
      howItCalculated: 'Tabulates daily model inference outputs: predicted units, lower bound (y_hat - 1.96 × SE), and upper bound (y_hat + 1.96 × SE).',
      useCase: 'Provides daily purchasing targets for warehouse logistics and helps schedule warehouse unloading teams.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    },
    modelSummary: {
      title: 'Forecasting Model Diagnostics',
      whatItShows: 'This feature is a performance report card for the forecasting AI. It displays error scores (like MAE and RMSE) and overall trend directions. It gives managers confidence that the AI predictions are statistically reliable before spending money on inventory.',
      howItCalculated: 'Backtested on validation holdout set: MAE = (1/n) Σ|y - y_hat|, RMSE = sqrt((1/n) Σ(y - y_hat)^2) evaluated against actual {sales:quantity}.',
      useCase: 'Assures procurement leaders of model statistical accuracy before committing purchasing budgets.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'quantity', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'category'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 6. RECOMMENDATIONS & PRICING
  // ─────────────────────────────────────────────
  recommendations: {
    kpiRestock: {
      title: 'Urgent Restock Triggers',
      whatItShows: 'This feature counts high-velocity items running out quickly. It identifies products whose daily sales rate will drain current stock within days. It gives purchasing managers an instant restock alert to place reorders before store shelves run dry.',
      howItCalculated: 'Evaluates run-out days: {inventory:current_stock} / DailyVelocity(SUM({sales:quantity}) / 30 days) and flags items with < 5 days coverage.',
      useCase: 'Automated purchasing shortlist to protect store revenue on high-velocity items.',
      sources: [
        { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'name'] }
      ]
    },
    kpiPriceIncrease: {
      title: 'Margin Expansion Opportunities',
      whatItShows: 'This feature spots smart price hike opportunities. It finds popular products with high demand and limited stock where raising the price slightly will not hurt sales. It gives store managers an easy way to boost profit margins on high-demand goods.',
      howItCalculated: 'Algorithmic heuristic: high 30-day velocity from {sales:quantity}, price elasticity < 0.8, and low available stock in {inventory:current_stock}.',
      useCase: 'Captures additional gross margin on inelastic, fast-moving items where demand exceeds supply.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] },
        { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
      ]
    },
    kpiPriceDecrease: {
      title: 'Clearance Markdown Opportunities',
      whatItShows: 'This feature highlights overstocked or slow-selling products that need price cuts. It finds items sitting on shelves too long or nearing expiration dates. It gives you clearance discount suggestions to clear shelf space and recover working cash.',
      howItCalculated: 'Algorithmic heuristic: low 30-day sales in {sales:quantity}, high warehouse stock in {inventory:current_stock}, or approaching shelf life.',
      useCase: 'Frees up warehouse storage capacity, accelerates cash flow, and eliminates perishable waste.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] },
        { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
      ]
    },
    kpiAssociationRules: {
      title: 'Market Basket Association Rules',
      whatItShows: 'This feature counts discovered product pairings from checkout baskets. It reveals statistically proven habits where customers buy item A together with item B. It gives merchandisers proven bundle opportunities like pairing coffee with creamer or chips with salsa.',
      howItCalculated: 'Mined via Apriori / FP-Growth algorithms on {sales:basket_id} and {sales:product_id} with Support >= 0.01 and Confidence >= 0.2.',
      useCase: 'Drives cross-merchandising, combo pack promotions, and strategic aisle layout optimization.',
      sources: [
        { file: 'sales.csv', columns: ['basket_id', 'product_id'] }
      ]
    },
    productSuggestions: {
      title: 'Frequently Bought Together Suggestions',
      whatItShows: 'This feature shows top product recommendations based on real customer shopping carts. It displays items that frequently end up in the same basket with strong connection scores. It gives store teams clear guidance on which items to place side-by-side on shelves.',
      howItCalculated: 'Computes Lift = Support(A,B) / (Support(A) × Support(B)) using transactions grouped by {sales:basket_id}.',
      useCase: 'Used to place complementary products side-by-side on store shelves and create promotional bundles.',
      sources: [
        { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'name', 'category'] }
      ]
    },
    associationRules: {
      title: 'Market Basket Rule Mining Matrix',
      whatItShows: 'This feature is a comprehensive table of mined shopping basket affinity rules. It shows the trigger item, the related item, and how strongly they are connected. It gives promotional managers mathematical backing to design winning combo deals.',
      howItCalculated: 'Calculates rule metrics: Support = P(A & B), Confidence = P(B|A), and Lift = Confidence / P(B) across checkout baskets in {sales:basket_id}.',
      useCase: 'Actionable intelligence for retail marketers to design high-converting promotional bundle campaigns.',
      sources: [
        { file: 'sales.csv', columns: ['basket_id', 'product_id'] },
        { file: 'products.csv', columns: ['product_id', 'name'] }
      ]
    },
    dynamicPricingTable: {
      title: 'Dynamic Pricing Recommendation Matrix',
      whatItShows: 'This feature is an automated pricing action grid. It lists current prices, recommended new prices, percentage change, and the exact business reason for the change. It gives buyers data-backed price adjustments to maximize profits without guessing.',
      howItCalculated: 'Balances current catalog price {products:price}, recent sales velocity from {sales:quantity}, and current warehouse stock {inventory:current_stock}.',
      useCase: 'Empowers merchandising buyers to optimize prices scientifically to maximize store-wide gross margin.',
      sources: [
        { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price'] },
        { file: 'inventory.csv', columns: ['product_id', 'current_stock', 'reorder_point'] },
        { file: 'sales.csv', columns: ['product_id', 'quantity', 'timestamp'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 7. DYNAMIC PRICING INTELLIGENCE
  // ─────────────────────────────────────────────
  pricing: {
    kpiPriceIncreases: {
      title: 'Price Increase Candidates',
      whatItShows: 'This feature counts products eligible for price increases. It identifies items with high demand and low inventory where raising the price will boost margin safely. It gives retailers quick profit-growth opportunities on popular goods.',
      howItCalculated: 'Filtered where SuggestedPrice > {products:price} based on sales velocity from {sales:quantity} and stock level {inventory:current_stock}.',
      useCase: 'Captures extra revenue on fast-selling products where customer willingness to pay is high.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] },
        { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
      ]
    },
    kpiPriceDecreases: {
      title: 'Price Markdown Candidates',
      whatItShows: 'This feature counts products that need promotional markdowns. It spots slow-selling items with excess warehouse units that need price cuts to sell faster. It gives store managers recommendations to liquidate stock and free up working capital.',
      howItCalculated: 'Filtered where SuggestedPrice < {products:price} due to slow movement in {sales:quantity} or high stock in {inventory:current_stock}.',
      useCase: 'Liquidates dead stock and frees up operating cash flow before perishable goods spoil.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] },
        { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
      ]
    },
    kpiHold: {
      title: 'Price Equilibrium (Hold)',
      whatItShows: 'This feature counts products that are already priced perfectly. It confirms items where sales velocity and stock are in healthy balance so no price change is needed. It gives managers reassurance that their core pricing is working well.',
      howItCalculated: 'Count of items where SuggestedPrice equals current catalog {products:price} within a ±1% tolerance band.',
      useCase: 'Confirms pricing stability on healthy-moving items that achieve balanced supply and demand.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] }
      ]
    },
    kpiAvgChange: {
      title: 'Average Price Delta %',
      whatItShows: 'This feature shows the overall net price change percentage across all products. It averages out all recommended increases and decreases. It gives managers a summary indicator to make sure their overall store pricing remains competitive in the local market.',
      howItCalculated: 'Calculated as AVG((SuggestedPrice - {products:price}) / {products:price} × 100%) across all evaluated SKUs.',
      useCase: 'Gauges overall store pricing index and ensures price adjustments remain competitive.',
      sources: [
        { file: 'products.csv', columns: ['price'] }
      ]
    },
    priceChangeDistribution: {
      title: 'Price Adjustment Distribution',
      whatItShows: 'This feature breaks down price recommendations into Increase, Decrease, and Hold categories. It shows the distribution of suggested price changes as visual bars. It gives management a bird-eye view to ensure markdowns are balanced by margin-boosting increases.',
      howItCalculated: 'Tallies total SKUs falling into Increase, Decrease, and Hold buckets based on calculated suggested prices.',
      useCase: 'Provides merchandising executives with a clear view of how price changes balance across the store.',
      sources: [
        { file: 'products.csv', columns: ['price'] },
        { file: 'inventory.csv', columns: ['current_stock'] },
        { file: 'sales.csv', columns: ['quantity', 'timestamp'] }
      ]
    },
    pricingSuggestionsTable: {
      title: 'Algorithmic Pricing Workbench',
      whatItShows: 'This feature is your interactive pricing control center. It lists each item with current price, AI suggested price, stock coverage, and one-click apply buttons. It gives pricing managers a safe, audited workbench to approve price updates instantly.',
      howItCalculated: 'Combines product price {products:price}, shelf life {products:shelf_life_days}, current stock {inventory:current_stock}, and sales velocity from {sales:quantity}.',
      useCase: 'Central workbench for pricing managers to review, audit, and approve dynamic price changes.',
      sources: [
        { file: 'products.csv', columns: ['product_id', 'name', 'category', 'price', 'shelf_life_days'] },
        { file: 'inventory.csv', columns: ['product_id', 'current_stock'] },
        { file: 'sales.csv', columns: ['product_id', 'quantity', 'timestamp'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 8. ANOMALY DETECTION
  // ─────────────────────────────────────────────
  anomalies: {
    kpiTotalAnomalies: {
      title: 'Total Detected Anomalies',
      whatItShows: 'This feature is an automatic fraud and error detector. It counts all unusual transaction events that broke normal sales patterns. It gives store managers an alert to investigate billing errors, system glitches, or unexpected sales rushes.',
      howItCalculated: 'Detected via Isolation Forest and statistical Z-score analysis flagging transaction points deviating > 2.5σ in {sales:total_price} and hourly velocity.',
      useCase: 'Early detection of register errors, fraudulent transactions, unexpected demand surges, or system outages.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    kpiSalesSpikes: {
      title: 'Abnormal Sales Spikes',
      whatItShows: 'This feature highlights sudden unusual bursts in sales revenue. It counts periods where money collected shot far above normal ceilings. It gives managers notice of sudden viral item demand, bulk restaurant purchases, or unexpected rush hours.',
      howItCalculated: 'Anomaly events where recorded sales {sales:total_price} > Upper Threshold (μ + 2.5σ).',
      useCase: 'Identifies sudden viral product demand, bulk commercial purchasing, or promotional windfalls.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    kpiSalesDrops: {
      title: 'Abnormal Sales Drops',
      whatItShows: 'This feature flags sudden severe drops in sales revenue. It counts periods where money collected plummeted far below expected floors. It gives managers immediate alerts to check for POS register breakdowns, power cuts, bad weather, or missing staff.',
      howItCalculated: 'Anomaly events where recorded sales {sales:total_price} < Lower Threshold (μ - 2.5σ).',
      useCase: 'Alerts management to POS system crashes, power failures, severe weather disruptions, or supply stockouts.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    kpiModel: {
      title: 'Anomaly Model Architecture',
      whatItShows: 'This feature shows the machine learning configuration used to catch outliers. It displays the Isolation Forest algorithm name and the 3% sensitivity rate. It gives technical assurance that outlier detection is active and tuned to avoid false alarms.',
      howItCalculated: 'Configured Isolation Forest model with 3% contamination threshold analyzing {sales:total_price} and transaction timestamps.',
      useCase: 'Documents statistical tuning parameters to balance sensitivity and minimize false alarms.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    salesTimeline: {
      title: 'Revenue Timeline with Anomaly Highlights',
      whatItShows: 'This feature is an interactive timeline graph with highlighted alert dots. It shows normal daily sales in cyan and highlights abnormal surge or drop days in vivid red. It gives managers a visual timeline to see when irregularities happened and how long they lasted.',
      howItCalculated: 'Plots chronological SUM({sales:total_price}) over {sales:timestamp} with overlaid anomaly markers from the ML model.',
      useCase: 'Enables store managers to visually pinpoint exactly when unusual revenue patterns occurred.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price'] }
      ]
    },
    anomalyDetailsTable: {
      title: 'Anomaly Investigation Audit Log',
      whatItShows: 'This feature is a forensic investigation table for unusual events. It details each abnormal date, expected sales range, actual money made, and the percentage deviation. It gives auditors and managers the exact records needed to review cashier logs and resolve variances.',
      howItCalculated: 'Chronological list of flagged points, computing percentage deviation = (Actual - Expected) / Expected × 100% using {sales:total_price}.',
      useCase: 'Operational audit log for financial reconciliations, register auditing, and inventory variance investigations.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp', 'total_price', 'sale_id'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 9. SUPPLIER MANAGEMENT
  // ─────────────────────────────────────────────
  suppliers: {
    kpiTotalSuppliers: {
      title: 'Active Wholesale Suppliers',
      whatItShows: 'This feature counts your registered supplier network. It shows the total number of wholesale distributors and vendors currently delivering goods to your store. It gives you a clear measure of supply chain diversity so you are not dependent on just one or two vendors.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {suppliers:supplier_id}) from active vendor records.',
      useCase: 'Monitors vendor network diversification to mitigate supply chain disruption risk.',
      sources: [
        { file: 'suppliers.csv', columns: ['supplier_id'] }
      ]
    },
    kpiAvgReliability: {
      title: 'Average Supplier Reliability',
      whatItShows: 'This feature grades vendor performance across your store. It averages delivery reliability scores measuring on-time, accurate, and undamaged deliveries. It gives purchasing managers a benchmark score to hold suppliers accountable to their service agreements.',
      howItCalculated: 'Calculated as AVG({suppliers:reliability_score}) across all active supplier partners.',
      useCase: 'Service-level agreement (SLA) benchmark ensuring suppliers meet supermarket fulfillment commitments.',
      sources: [
        { file: 'suppliers.csv', columns: ['reliability_score'] }
      ]
    },
    kpiProductsSupplied: {
      title: 'Catalog Sourced Products',
      whatItShows: 'This feature counts catalog items tied to an authorized supplier. It shows how many store SKUs have an active supplier assigned for reordering. It gives inventory managers visibility into catalog coverage so no product is left without a restock supplier.',
      howItCalculated: 'Calculated as COUNT({products:product_id}) where {products:supplier_id} is assigned in catalog records.',
      useCase: 'Verifies catalog vendor coverage and identifies unassigned SKUs that lack a replenishment supplier.',
      sources: [
        { file: 'suppliers.csv', columns: ['supplier_id'] },
        { file: 'products.csv', columns: ['product_id', 'supplier_id'] }
      ]
    },
    kpiAvgLeadTime: {
      title: 'Average Order Lead Time',
      whatItShows: 'This feature tracks delivery speed in days. It calculates the average number of days between submitting a purchase order and receiving goods at the loading dock. It gives inventory planners the exact buffer days needed to set safe reorder points.',
      howItCalculated: 'Calculated as AVG({suppliers:lead_time_days}) across all registered supplier records.',
      useCase: 'Critical parameter used to calibrate safety stock reorder thresholds in {inventory:reorder_point}.',
      sources: [
        { file: 'suppliers.csv', columns: ['lead_time_days'] }
      ]
    },
    revenueBySupplier: {
      title: 'Revenue Generated by Supplier',
      whatItShows: 'This feature compares how much customer money is generated by each supplier goods. It displays sales revenue attributable to each vendor products. It gives buyers strong leverage when negotiating bulk discounts and contract renewals.',
      howItCalculated: 'Joins {sales:product_id} with {products:product_id} and {suppliers:supplier_id}, summing {sales:total_price} grouped by {suppliers:name}.',
      useCase: 'Crucial for supplier contract renewals, volume discount negotiations, and partnership tiering.',
      sources: [
        { file: 'suppliers.csv', columns: ['supplier_id', 'name'] },
        { file: 'products.csv', columns: ['supplier_id', 'product_id'] },
        { file: 'sales.csv', columns: ['product_id', 'total_price'] }
      ]
    },
    productsSupplied: {
      title: 'Product Lines per Supplier',
      whatItShows: 'This feature shows how many unique product lines each vendor provides. It reveals which suppliers provide the widest assortment to your supermarket. It gives management insight into vendor reliance and helps identify chances to consolidate orders.',
      howItCalculated: 'Groups by {suppliers:name} and counts distinct {products:product_id} linked via {products:supplier_id}.',
      useCase: 'Identifies vendor concentration risk and highlights opportunities to consolidate purchasing.',
      sources: [
        { file: 'suppliers.csv', columns: ['supplier_id', 'name'] },
        { file: 'products.csv', columns: ['supplier_id', 'product_id'] }
      ]
    },
    supplierPerformanceTable: {
      title: 'Supplier Performance Scorecard',
      whatItShows: 'This feature is your complete vendor scorecard directory. It lists each supplier contact info, lead time, reliability score, and total revenue contribution. It gives purchasing teams a complete tool to evaluate vendors, place orders, and replace poor performers.',
      howItCalculated: 'Multi-table join across {suppliers:supplier_id}, {products:supplier_id}, and aggregated {sales:total_price} and {sales:quantity}.',
      useCase: 'Strategic procurement directory used to review vendor SLAs, initiate purchase orders, and replace underperforming suppliers.',
      sources: [
        { file: 'suppliers.csv', columns: ['supplier_id', 'name', 'contact_email', 'lead_time_days', 'reliability_score'] },
        { file: 'products.csv', columns: ['supplier_id', 'product_id', 'category'] },
        { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] }
      ]
    }
  },

  // ─────────────────────────────────────────────
  // 10. SALES HEATMAP & ANALYTICS
  // ─────────────────────────────────────────────
  heatmap: {
    kpiTotalProfit: {
      title: 'Total Gross Profit',
      whatItShows: 'This feature shows the net gross margin earned across all sales. It subtracts wholesale product costs from total customer sales revenue. It gives you the true earnings left over after paying suppliers to help you gauge business health.',
      howItCalculated: 'Calculated as Σ({sales:total_price} - ({sales:quantity} × {products:cost})) by matching {sales:product_id} to {products:product_id}.',
      useCase: 'Core profitability indicator measuring actual bottom-line merchandise returns beyond top-line revenue.',
      sources: [
        { file: 'sales.csv', columns: ['total_price', 'quantity'] },
        { file: 'products.csv', columns: ['cost', 'price'] }
      ]
    },
    kpiOverallMargin: {
      title: 'Overall Gross Margin %',
      whatItShows: 'This feature shows the percentage of sales kept as profit margin. It reveals what percentage of every rupee or dollar earned remains after paying wholesale product costs. It gives managers a benchmark percentage to compare against grocery industry standards.',
      howItCalculated: 'Calculated as (Total Gross Profit / Total Revenue) × 100% = (Σ({sales:total_price} - {sales:quantity} × {products:cost}) / Σ({sales:total_price})) × 100%.',
      useCase: 'Retail profitability health check benchmarking store margins against grocery industry standards (typically 20-30%).',
      sources: [
        { file: 'sales.csv', columns: ['total_price', 'quantity'] },
        { file: 'products.csv', columns: ['cost', 'price'] }
      ]
    },
    kpiPaymentMethods: {
      title: 'Active Payment Methods',
      whatItShows: 'This feature counts customer payment types accepted at checkouts. It tallies distinct payment channels used, such as UPI, Cards, and Cash. It gives managers confirmation that registers accept all modern payment methods customer prefer.',
      howItCalculated: 'Calculated as COUNT(DISTINCT {sales:payment_method}) across all completed transaction records.',
      useCase: 'Ensures register checkout lanes accommodate customer payment preferences (Cash, UPI, Cards).',
      sources: [
        { file: 'sales.csv', columns: ['payment_method'] }
      ]
    },
    kpiPeakHours: {
      title: 'Peak Shopping Hours',
      whatItShows: 'This feature pinpoints the single busiest shopping hour of the day. It identifies the clock hour that records the highest volume of customer checkouts. It gives floor managers the exact time window when maximum cashiers and baggers must be on duty.',
      howItCalculated: 'Extracts HOUR({sales:timestamp}) across all sales receipts and determines the peak hour window with maximum transaction counts.',
      useCase: 'Essential for optimizing cashier shift scheduling, bagger staffing, and shelf restocking times.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp'] }
      ]
    },
    hourlyHeatmap: {
      title: 'Hourly Sales Traffic Heatmap',
      whatItShows: 'This feature is a 2D color traffic grid of shopping activity. It maps every hour of the day (0-23) against every day of the week, coloring busier hours in bright colors. It gives managers an instant visual guide to rush hours and slow periods for smart staff scheduling.',
      howItCalculated: 'Groups transactions by DAYOFWEEK({sales:timestamp}) and HOUR({sales:timestamp}), calculating transaction counts and revenue normalized to color intensity.',
      useCase: 'Enables store managers to identify rush hours and quiet periods to plan staffing shifts and dynamic promotional discounts.',
      sources: [
        { file: 'sales.csv', columns: ['timestamp'] }
      ]
    },
    paymentMethods: {
      title: 'Payment Method Share',
      whatItShows: 'This feature shows customer payment choices as a breakdown chart. It reveals what percentage of revenue is paid via UPI, Cash, Credit Card, or Debit Card. It gives finance teams information to negotiate bank transaction fees and manage cash security.',
      howItCalculated: 'Groups by {sales:payment_method}, computing SUM({sales:total_price}) and percentage share of total store revenue.',
      useCase: 'Assists with bank settlement reconciliation, merchant interchange fee reduction, and cash handling security.',
      sources: [
        { file: 'sales.csv', columns: ['payment_method', 'total_price'] }
      ]
    },
    profitMarginByCategory: {
      title: 'Profit Margin by Category',
      whatItShows: 'This feature compares profit margin percentages across all departments. It shows which categories make high margins and which operate on slim margins. It gives merchandisers clear guidance on promoting high-margin items to increase overall profits.',
      howItCalculated: 'Groups by {products:category}, calculating (SUM({sales:total_price} - {sales:quantity} × {products:cost}) / SUM({sales:total_price})) × 100%.',
      useCase: 'Highlights high-margin departments (e.g. Bakery, Deli) vs low-margin volume staples to guide the promotional mix.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] },
        { file: 'products.csv', columns: ['product_id', 'category', 'cost', 'price'] }
      ]
    },
    categoryProfitBreakdownTable: {
      title: 'Category Financial Performance Table',
      whatItShows: 'This feature is a department accounting breakdown table. It lists each category with total sales revenue, wholesale cost paid, net profit, and profit margin percentage. It gives department heads exact financial numbers to evaluate vendor deals and retail markups.',
      howItCalculated: 'Joins {sales:product_id} with {products:product_id}, grouping by {products:category}, computing revenue SUM({sales:total_price}), cost SUM({sales:quantity} × {products:cost}), and net margin.',
      useCase: 'Department P&L reference for category managers to assess procurement pricing and retail markup strategies.',
      sources: [
        { file: 'sales.csv', columns: ['product_id', 'total_price', 'quantity'] },
        { file: 'products.csv', columns: ['product_id', 'category', 'cost', 'price'] }
      ]
    }
  }
};
