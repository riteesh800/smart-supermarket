"""
SmartBot v2 — Intelligent data-aware supermarket assistant.
Features: fuzzy matching, time-period parsing, context memory,
comparative queries, number extraction, category/product-specific analytics.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from difflib import SequenceMatcher
from collections import OrderedDict
from typing import Optional
import re
import sys
import os
import time as _time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
from database import get_db
from auth import get_current_user, User

router = APIRouter(prefix="/api/chat", tags=["chatbot"])

# ── Per-session conversation context with LRU eviction ──
_MAX_SESSIONS = 100
_SESSION_TTL = 1800  # 30 minutes
_sessions: OrderedDict = OrderedDict()


def _get_context(session_id: str) -> dict:
    """Get or create session context. LRU eviction if too many sessions."""
    now = _time.time()
    if session_id in _sessions:
        ctx = _sessions[session_id]
        ctx["last_access"] = now
        _sessions.move_to_end(session_id)
        return ctx
    # Evict expired sessions
    expired = [k for k, v in _sessions.items() if now - v.get("last_access", 0) > _SESSION_TTL]
    for k in expired:
        del _sessions[k]
    # Evict oldest if over max
    while len(_sessions) >= _MAX_SESSIONS:
        _sessions.popitem(last=False)
    ctx = {"last_intent": None, "last_entity": None, "last_data": None, "history": [], "last_access": now}
    _sessions[session_id] = ctx
    return ctx


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


# ── Helpers ──

_SQL_KEYWORDS = {'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'GROUP', 'ORDER', 'LIMIT', 'ON', 'SET', 'VALUES', 'UNION', 'AND', 'OR', 'HAVING', 'USING', 'NATURAL', 'CROSS'}
_DATA_TABLES = ['sales', 'products', 'customers', 'inventory', 'suppliers']


def scope_sql(sql: str) -> str:
    """Rewrite tables in query to be isolated by user_id subqueries."""
    for t in _DATA_TABLES:
        pattern = rf'(\b(?:FROM|JOIN)\s+)({t})(?:\s+([a-zA-Z_][a-zA-Z0-9_]*))?'
        def repl(m):
            prefix = m.group(1)
            tbl = m.group(2)
            alias = m.group(3)
            if alias and alias.upper() not in _SQL_KEYWORDS:
                return f'{prefix}(SELECT * FROM {tbl} WHERE user_id = :_bot_uid) {alias}'
            elif alias:
                return f'{prefix}(SELECT * FROM {tbl} WHERE user_id = :_bot_uid) {tbl} {alias}'
            else:
                return f'{prefix}(SELECT * FROM {tbl} WHERE user_id = :_bot_uid) {tbl}'
        sql = re.sub(pattern, repl, sql, flags=re.IGNORECASE)
    return sql


def query_db(db, sql, params=None, user_id=None):
    if not user_id:
        return []
    p = dict(params or {})
    scoped_sql = scope_sql(sql)
    p["_bot_uid"] = str(user_id)
    result = db.execute(text(scoped_sql), p)
    rows = result.fetchall()
    cols = result.keys()
    return [dict(zip(cols, r)) for r in rows]


def fmt(val):
    """Format currency as ₹."""
    if val is None:
        return "₹0"
    if isinstance(val, float):
        return f"₹{val:,.2f}"
    return f"₹{val:,}"


def pct(val):
    if val is None:
        return "0%"
    return f"{val:.1f}%"


def fuzzy_match(word, candidates, threshold=0.6):
    """Find best fuzzy match from candidates."""
    best, best_score = None, 0
    word_lower = word.lower()
    for c in candidates:
        score = SequenceMatcher(None, word_lower, c.lower()).ratio()
        # Boost for substring match
        if word_lower in c.lower() or c.lower() in word_lower:
            score = max(score, 0.85)
        if score > best_score and score >= threshold:
            best, best_score = c, score
    return best


def extract_number(msg, default=5):
    """Extract a number from message (e.g., 'top 3 products')."""
    m = re.search(r'\b(\d+)\b', msg)
    return int(m.group(1)) if m else default


def extract_time_filter(msg, db=None, user_id=None):
    """Extract time period from message.
    Returns (sql_fragment, params_dict, label, matched_text) or (None, {}, None, None).
    Uses parameterized SQL to prevent injection.
    Adapts to historical dataset date range if current date has no records."""
    msg_lower = msg.lower()
    now = datetime.now()

    # Anchor 'now' to dataset maximum date if historical data is loaded
    if db is not None:
        try:
            max_row = query_db(db, "SELECT MAX(SUBSTR(timestamp, 1, 10)) as max_dt FROM sales", user_id=user_id)
            if max_row and max_row[0].get("max_dt"):
                max_dt_str = str(max_row[0]["max_dt"]).split()[0]
                dt_obj = datetime.strptime(max_dt_str, "%Y-%m-%d")
                if (datetime.now() - dt_obj).days > 60:
                    now = dt_obj
        except Exception:
            pass

    if any(k in msg_lower for k in ["today", "today's"]):
        date = now.strftime("%Y-%m-%d")
        matched = next(k for k in ["today's", "today"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 10) = :tf_date", {"tf_date": date}, "today", matched

    if "yesterday" in msg_lower:
        date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        return "SUBSTR(timestamp, 1, 10) = :tf_date", {"tf_date": date}, "yesterday", "yesterday"

    if any(k in msg_lower for k in ["this week", "current week"]):
        start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        matched = next(k for k in ["this week", "current week"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 10) >= :tf_start", {"tf_start": start}, "this week", matched

    if any(k in msg_lower for k in ["last week", "previous week"]):
        end = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        start = (now - timedelta(days=now.weekday() + 7)).strftime("%Y-%m-%d")
        matched = next(k for k in ["last week", "previous week"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 10) >= :tf_start AND SUBSTR(timestamp, 1, 10) < :tf_end", {"tf_start": start, "tf_end": end}, "last week", matched

    if any(k in msg_lower for k in ["this month", "current month"]):
        month = now.strftime("%Y-%m")
        matched = next(k for k in ["this month", "current month"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 7) = :tf_month", {"tf_month": month}, "this month", matched

    if any(k in msg_lower for k in ["last month", "previous month"]):
        first = now.replace(day=1)
        prev = first - timedelta(days=1)
        month = prev.strftime("%Y-%m")
        matched = next(k for k in ["last month", "previous month"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 7) = :tf_month", {"tf_month": month}, "last month", matched

    if any(k in msg_lower for k in ["this year", "current year"]):
        year = now.strftime("%Y")
        matched = next(k for k in ["this year", "current year"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 4) = :tf_year", {"tf_year": year}, "this year", matched

    if any(k in msg_lower for k in ["last year", "previous year"]):
        year = str(now.year - 1)
        matched = next(k for k in ["last year", "previous year"] if k in msg_lower)
        return "SUBSTR(timestamp, 1, 4) = :tf_year", {"tf_year": year}, "last year", matched

    # "last N days"
    m = re.search(r'last\s+(\d+)\s+days?', msg_lower)
    if m:
        days = int(m.group(1))
        date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        return "SUBSTR(timestamp, 1, 10) >= :tf_date", {"tf_date": date}, f"last {days} days", m.group(0)

    # Specific month name
    months = {"january": "01", "february": "02", "march": "03", "april": "04",
              "may": "05", "june": "06", "july": "07", "august": "08",
              "september": "09", "october": "10", "november": "11", "december": "12",
              "jan": "01", "feb": "02", "mar": "03", "apr": "04",
              "jun": "06", "jul": "07", "aug": "08", "sep": "09",
              "oct": "10", "nov": "11", "dec": "12"}
    for name, num in months.items():
        if name in msg_lower:
            yr_match = re.search(r'20\d{2}', msg_lower)
            year = yr_match.group(0) if yr_match else str(now.year)
            return "SUBSTR(timestamp, 1, 7) = :tf_month", {"tf_month": f"{year}-{num}"}, f"{name.capitalize()} {year}", name

    # Standalone 4-digit year (e.g. 2019, 2021)
    yr_match = re.search(r'\b(19\d{2}|20\d{2})\b', msg_lower)
    if yr_match:
        year = yr_match.group(1)
        return "SUBSTR(timestamp, 1, 4) = :tf_year", {"tf_year": year}, f"year {year}", yr_match.group(0)

    return None, {}, None, None


def get_categories(db, user_id=None):
    """Get all category names from DB isolated by user."""
    data = query_db(db, "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category", user_id=user_id)
    return [d['category'] for d in data if d.get('category')]


def extract_category(msg, db, user_id=None):
    """Extract category from message using fuzzy matching."""
    categories = get_categories(db, user_id=user_id)
    msg_lower = msg.lower()

    # Direct match first
    for cat in categories:
        if cat.lower() in msg_lower:
            return cat

    # Fuzzy match each word
    words = re.findall(r'[a-z]+', msg_lower)
    for word in words:
        if len(word) < 3:
            continue
        match = fuzzy_match(word, categories, threshold=0.65)
        if match:
            return match

    return None


def extract_product_term(msg):
    """Extract product search term from message."""
    # Remove common prefixes
    patterns = [
        r'(?:tell me about|info on|details of|search for|find|how is|how are|sales of|sales for|revenue of|revenue for|show me)\s+(.+)',
        r'(?:about|for|of)\s+(.+?)(?:\s+selling|\s+doing|\s+going|\s*$)',
    ]
    for p in patterns:
        m = re.search(p, msg.lower().strip())
        if m:
            term = m.group(1).strip().rstrip('?!.,')
            # Remove trailing noise words
            term = re.sub(r'\s+(please|thanks|thx|pls|right now|currently)$', '', term)
            if len(term) > 1:
                return term
    return None


# ── Synonyms & Intent Scoring ──

INTENT_KEYWORDS = {
    "greeting": {
        "keywords": ["hi", "hello", "hey", "howdy", "greetings", "yo", "sup", "good morning", "good evening", "good afternoon", "whats up"],
        "weight": 1.0, "pattern": r"^(hi|hello|hey|howdy|greetings|yo|sup|good\s)"
    },
    "help": {
        "keywords": ["help", "what can you do", "commands", "menu", "options", "what do you know", "how to use", "guide", "capabilities"],
        "weight": 1.0, "pattern": r"^(help|what can|how to use|guide)"
    },
    "thanks": {
        "keywords": ["thanks", "thank you", "thx", "ty", "appreciate", "great", "awesome", "cool", "nice", "perfect", "wonderful"],
        "weight": 1.0, "pattern": None
    },
    "total_revenue": {
        "keywords": ["total revenue", "total sales", "overall revenue", "how much revenue", "total earnings", "gross revenue", "total income", "how much we made", "how much money", "revenue so far"],
        "weight": 1.2, "pattern": None
    },
    "monthly_revenue": {
        "keywords": ["monthly revenue", "revenue by month", "sales by month", "month wise revenue", "monthly sales", "month breakdown", "revenue trend"],
        "weight": 1.1, "pattern": None
    },
    "category_revenue": {
        "keywords": ["revenue by category", "category revenue", "sales by category", "category wise", "category breakdown", "category performance", "which category", "best category", "top category"],
        "weight": 1.1, "pattern": None
    },
    "best_sellers": {
        "keywords": ["best seller", "top product", "top selling", "most sold", "best product", "popular product", "highest selling", "what sells", "what sells most", "trending product"],
        "weight": 1.0, "pattern": None
    },
    "worst_sellers": {
        "keywords": ["worst seller", "least sold", "worst product", "lowest selling", "slow moving", "not selling", "poor seller", "bottom product"],
        "weight": 1.0, "pattern": None
    },
    "low_stock": {
        "keywords": ["low stock", "out of stock", "running low", "need restock", "restock", "stock alert", "stock warning", "shortage", "running out"],
        "weight": 1.0, "pattern": None
    },
    "total_products": {
        "keywords": ["how many product", "total product", "number of product", "product count", "count product", "products do we have"],
        "weight": 1.0, "pattern": None
    },
    "total_customers": {
        "keywords": ["how many customer", "total customer", "number of customer", "customer count", "count customer", "customers do we have"],
        "weight": 1.0, "pattern": None
    },
    "top_customers": {
        "keywords": ["top customer", "best customer", "highest spend", "vip customer", "most valuable", "biggest spender", "loyal customer", "premium customer"],
        "weight": 1.0, "pattern": None
    },
    "customer_segments": {
        "keywords": ["segment", "customer segment", "rfm", "champions", "at risk", "customer groups", "customer types", "customer tiers", "membership"],
        "weight": 1.0, "pattern": None
    },
    "inventory_summary": {
        "keywords": ["inventory", "stock level", "stock summary", "warehouse", "stock status", "inventory status", "how much stock", "stock overview"],
        "weight": 0.9, "pattern": None
    },
    "profit": {
        "keywords": ["profit", "margin", "profit margin", "how much profit", "profitability", "net profit", "gross profit", "margins", "cost vs revenue"],
        "weight": 1.1, "pattern": None
    },
    "categories": {
        "keywords": ["categories", "how many categor", "list categor", "what categor", "all categories", "show categories"],
        "weight": 0.9, "pattern": None
    },
    "suppliers": {
        "keywords": ["supplier", "vendor", "who supplies", "supplier list", "supplier performance", "supplier info", "which supplier"],
        "weight": 1.0, "pattern": None
    },
    "payment_methods": {
        "keywords": ["payment", "how do people pay", "payment method", "cash vs card", "digital wallet", "payment breakdown", "payment split", "payment mode"],
        "weight": 1.0, "pattern": None
    },
    "expiring": {
        "keywords": ["expir", "about to expire", "shelf life", "going bad", "perishable", "expire soon", "expiry", "freshness"],
        "weight": 1.0, "pattern": None
    },
    "avg_order": {
        "keywords": ["average order", "avg order", "basket size", "average basket", "avg transaction", "average transaction", "order size", "cart size", "avg basket value"],
        "weight": 1.0, "pattern": None
    },
    "peak_hours": {
        "keywords": ["busiest", "peak hour", "peak time", "when do people shop", "rush hour", "busiest time", "busy hour", "best time", "shopping hours", "when is busy"],
        "weight": 1.0, "pattern": None
    },
    "product_search": {
        "keywords": ["tell me about", "info on", "details of", "search for", "find product", "show me", "look up"],
        "weight": 0.8, "pattern": r"(tell me about|info on|details of|search for|find|look up|show me)\s+"
    },
    "product_sales": {
        "keywords": ["how is .* selling", "sales of", "sales for", "revenue of", "revenue for", "performance of", "how much .* sold"],
        "weight": 1.0, "pattern": r"(how is|how are|sales of|sales for|revenue of|revenue for|performance of)"
    },
    "discounts": {
        "keywords": ["discount", "how much discount", "average discount", "discount rate", "markdown", "promotions", "deals"],
        "weight": 1.0, "pattern": None
    },
    "total_transactions": {
        "keywords": ["how many transaction", "total transaction", "number of transaction", "transaction count", "how many order", "order count", "total orders"],
        "weight": 1.0, "pattern": None
    },
    "compare_categories": {
        "keywords": ["compare", "vs", "versus", "difference between", "better", "which is better"],
        "weight": 1.2, "pattern": r"(compare|vs|versus|difference between)"
    },
    "daily_revenue": {
        "keywords": ["daily revenue", "revenue today", "today sales", "sales today", "today revenue", "daily sales"],
        "weight": 1.1, "pattern": None
    },
    "growth": {
        "keywords": ["growth", "growing", "trend", "increasing", "decreasing", "going up", "going down", "improve", "decline"],
        "weight": 1.0, "pattern": None
    },
    "summary": {
        "keywords": ["summary", "overview", "dashboard", "snapshot", "quick summary", "give me summary", "overall", "big picture", "status"],
        "weight": 0.9, "pattern": None
    },
    "category_detail": {
        "keywords": [],  # Detected by category extraction
        "weight": 0.7, "pattern": None
    },
}


def score_intent(msg):
    """Score all intents and return best match. Uses keyword matching + fuzzy + pattern."""
    msg_lower = msg.lower().strip()
    scores = {}

    for intent, config in INTENT_KEYWORDS.items():
        score = 0

        # Pattern match (highest priority)
        if config.get("pattern"):
            if re.search(config["pattern"], msg_lower):
                score += 3.0

        # Exact keyword/phrase match
        for kw in config["keywords"]:
            if kw in msg_lower:
                # Longer phrases = stronger signal
                score += 2.0 + len(kw.split()) * 0.5

        # Fuzzy word matching
        msg_words = set(re.findall(r'[a-z]+', msg_lower))
        for kw in config["keywords"]:
            kw_words = set(kw.split())
            overlap = msg_words & kw_words
            if overlap:
                score += len(overlap) * 0.5

        # Apply weight
        score *= config.get("weight", 1.0)
        if score > 0:
            scores[intent] = score

    if not scores:
        return "unknown", 0

    best = max(scores, key=scores.get)
    return best, scores[best]


# ── Response Generators ──

def respond(intent, msg, db, session_id="default", user_id=None):
    """Generate response for detected intent."""
    _context = _get_context(session_id)
    # Extract time filter first, then strip it from msg to avoid number conflicts
    time_where, time_params, time_label, time_matched = extract_time_filter(msg, db, user_id=user_id)
    msg_for_number = msg
    if time_matched:
        msg_for_number = msg.lower().replace(time_matched, "").strip()
    n = extract_number(msg_for_number)
    time_suffix = f" ({time_label})" if time_label else ""
    time_clause = f"WHERE {time_where}" if time_where else ""
    time_and = f"AND {time_where}" if time_where else ""

    def tq(sql, extra_params=None):
        """Time-aware query: automatically merges time_params into query_db calls."""
        params = dict(time_params) if time_params else {}
        if extra_params:
            params.update(extra_params)
        return query_db(db, sql, params, user_id=user_id)

    # ── Greeting ──
    if intent == "greeting":
        greetings = [
            "Hey! 👋 I'm **SmartBot**, your store intelligence assistant.\n\nAsk me anything — revenue, stock, customers, products. I understand natural language!\n\nType **help** to see everything I can do.",
            "Hello! 🤖 Ready to crunch your store data. Try asking:\n• \"How's revenue this month?\"\n• \"What's selling best?\"\n• \"Show me low stock items\"",
        ]
        import random
        return {"reply": random.choice(greetings), "type": "text"}

    # ── Thanks ──
    if intent == "thanks":
        responses = [
            "Happy to help! 😊 Ask me anything else about your store data.",
            "You're welcome! 🎉 Got more questions? Fire away!",
            "Anytime! 💪 I'm here whenever you need data insights.",
        ]
        import random
        return {"reply": random.choice(responses), "type": "text"}

    # ── Help ──
    if intent == "help":
        return {
            "reply": "🤖 **SmartBot Capabilities**:\n\n"
                     "💰 **Revenue** — \"total revenue\", \"revenue this month\", \"sales in January\"\n"
                     "🏆 **Products** — \"top 10 products\", \"worst sellers\", \"tell me about milk\"\n"
                     "📦 **Inventory** — \"low stock\", \"expiring soon\", \"inventory summary\"\n"
                     "👥 **Customers** — \"top customers\", \"customer segments\", \"how many customers\"\n"
                     "📊 **Analytics** — \"profit margins\", \"peak hours\", \"payment methods\"\n"
                     "📅 **Time Filters** — Add \"this month\", \"last week\", \"in March\", \"last 30 days\" to any query\n"
                     "🔢 **Quantities** — \"top 3 products\", \"show 10 customers\"\n"
                     "⚖️ **Compare** — \"compare Dairy vs Bakery\"\n"
                     "📈 **Trends** — \"revenue trend\", \"growth\"\n"
                     "🔍 **Search** — \"tell me about cheese\", \"how is milk selling\"\n"
                     "🗂️ **Categories** — Ask about any specific category: \"how is Dairy doing?\"\n\n"
                     "💡 **Tip**: I understand natural language! Just ask naturally.",
            "type": "text"
        }

    # ── Summary / Overview ──
    if intent == "summary":
        rev = tq(f"SELECT SUM(total_price) as revenue, COUNT(*) as txns, COUNT(DISTINCT customer_id) as customers, COUNT(DISTINCT basket_id) as baskets FROM sales {time_clause}")
        prod = tq("SELECT COUNT(*) as cnt, COUNT(DISTINCT category) as cats FROM products")
        low = tq("SELECT COUNT(*) as cnt FROM inventory WHERE current_stock <= reorder_point")
        r, p, l = rev[0], prod[0], low[0]
        profit_suffix = ""
        has_cost_check = tq("SELECT COUNT(*) as cnt FROM products WHERE cost IS NOT NULL AND cost > 0")
        has_cost = has_cost_check[0]['cnt'] > 0
        if has_cost:
            profit_data = tq(f"""
                SELECT SUM(s.total_price) - SUM(s.quantity * p.cost) as profit
                FROM sales s JOIN products p ON s.product_id = p.product_id
                WHERE p.cost IS NOT NULL AND p.cost > 0 {time_and}
            """)
            profit = profit_data[0]['profit'] or 0
        else:
            profit_data = tq(f"""
                SELECT SUM(s.total_price) - SUM(s.quantity * (p.price * 0.65)) as profit
                FROM sales s JOIN products p ON s.product_id = p.product_id
                {time_clause.replace('timestamp', 's.timestamp')}
            """)
            profit = (profit_data[0]['profit'] or 0)
            profit_suffix = " (est.)"
        return {
            "reply": f"📊 **Store Summary{time_suffix}**:\n\n"
                     f"💰 Revenue: **{fmt(r['revenue'])}**\n"
                     f"📈 Profit: **{fmt(profit)}**{profit_suffix}\n"
                     f"🧾 Transactions: **{r['txns']:,}** ({r['baskets']:,} baskets)\n"
                     f"👥 Active Customers: **{r['customers']:,}**\n"
                     f"📦 Products: **{p['cnt']}** across **{p['cats']}** categories\n"
                     f"🚨 Low Stock Alerts: **{l['cnt']}**",
            "type": "metric"
        }

    # ── Total Revenue ──
    if intent == "total_revenue":
        data = tq(f"SELECT SUM(total_price) as revenue, COUNT(*) as txns, COUNT(DISTINCT customer_id) as custs FROM sales {time_clause}")
        r = data[0]
        avg = r['revenue'] / r['txns'] if r['txns'] else 0
        return {"reply": f"💰 **Total Revenue{time_suffix}**: {fmt(r['revenue'])}\n📋 Transactions: {r['txns']:,}\n👥 Unique Customers: {r['custs']:,}\n🧾 Avg per transaction: {fmt(avg)}", "type": "metric"}

    # ── Daily Revenue ──
    if intent == "daily_revenue":
        # Anchor to dataset's max date if historical data is loaded
        today_rows = tq("SELECT MAX(SUBSTR(timestamp, 1, 10)) as max_dt FROM sales")
        today = datetime.now().strftime("%Y-%m-%d")
        if today_rows and today_rows[0].get("max_dt"):
            max_dt_str = str(today_rows[0]["max_dt"]).split()[0]
            try:
                dt_obj = datetime.strptime(max_dt_str, "%Y-%m-%d")
                if (datetime.now() - dt_obj).days > 60:
                    today = max_dt_str
            except ValueError:
                pass
        data = tq("SELECT SUM(total_price) as revenue, COUNT(*) as txns FROM sales WHERE SUBSTR(timestamp, 1, 10) = :today", {"today": today})
        r = data[0]
        if not r['revenue']:
            return {"reply": f"📅 No sales recorded for {today}.", "type": "text"}
        return {"reply": f"📅 **Revenue for {today}**: {fmt(r['revenue'])}\n🧾 Transactions: {r['txns']:,}", "type": "metric"}

    # ── Monthly Revenue ──
    if intent == "monthly_revenue":
        data = tq("""
            SELECT SUBSTR(timestamp, 1, 7) as month, SUM(total_price) as revenue, COUNT(*) as txns
            FROM sales GROUP BY month ORDER BY month DESC LIMIT 6
        """)
        lines = ["📅 **Monthly Revenue Breakdown**:\n"]
        prev = None
        for d in data:
            change = ""
            if prev is not None:
                diff = ((d['revenue'] - prev) / prev * 100) if prev else 0
                arrow = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                change = f" {arrow} {diff:+.1f}%"
            lines.append(f"• **{d['month']}**: {fmt(d['revenue'])} ({d['txns']:,} txns){change}")
            prev = d['revenue']
        _context["last_intent"] = "monthly_revenue"
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Category Revenue ──
    if intent == "category_revenue":
        data = tq(f"""
            SELECT p.category, SUM(s.total_price) as revenue, SUM(s.quantity) as qty
            FROM sales s JOIN products p ON s.product_id = p.product_id
            {time_clause.replace('timestamp', 's.timestamp')}
            GROUP BY p.category ORDER BY revenue DESC
        """)
        total = sum(d['revenue'] for d in data)
        lines = [f"📊 **Revenue by Category{time_suffix}**:\n"]
        for i, d in enumerate(data, 1):
            share = (d['revenue'] / total * 100) if total else 0
            bar = "█" * int(share / 5) + "░" * (20 - int(share / 5))
            lines.append(f"{i}. **{d['category']}**: {fmt(d['revenue'])} ({share:.1f}%)\n   {bar}")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Best Sellers ──
    if intent == "best_sellers":
        limit = min(extract_number(msg, 5), 20)
        data = tq(f"""
            SELECT p.name, p.category, SUM(s.total_price) as revenue, SUM(s.quantity) as qty
            FROM sales s JOIN products p ON s.product_id = p.product_id
            {time_clause.replace('timestamp', 's.timestamp')}
            GROUP BY p.product_id, p.name, p.category ORDER BY revenue DESC LIMIT :lim
        """, {"lim": limit})
        lines = [f"🏆 **Top {limit} Best Sellers{time_suffix}**:\n"]
        for i, d in enumerate(data, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(f"{medal} **{d['name']}** ({d['category']})\n   {fmt(d['revenue'])} • {d['qty']:,} units sold")
        _context["last_intent"] = "best_sellers"
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Worst Sellers ──
    if intent == "worst_sellers":
        limit = min(extract_number(msg, 5), 20)
        data = tq(f"""
            SELECT p.name, p.category, SUM(s.total_price) as revenue, SUM(s.quantity) as qty
            FROM sales s JOIN products p ON s.product_id = p.product_id
            {time_clause.replace('timestamp', 's.timestamp')}
            GROUP BY p.product_id, p.name, p.category ORDER BY revenue ASC LIMIT :lim
        """, {"lim": limit})
        lines = [f"📉 **Bottom {limit} Slowest Sellers{time_suffix}**:\n"]
        for i, d in enumerate(data, 1):
            lines.append(f"{i}. **{d['name']}** ({d['category']}) — {fmt(d['revenue'])}, {d['qty']:,} units")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Low Stock ──
    if intent == "low_stock":
        data = tq("""
            SELECT p.name, p.category, i.current_stock, i.reorder_point, i.max_stock,
                   ROUND(i.current_stock * 100.0 / i.max_stock, 1) as fill_pct
            FROM inventory i JOIN products p ON i.product_id = p.product_id
            WHERE i.current_stock <= i.reorder_point
            ORDER BY i.current_stock ASC LIMIT 10
        """)
        if not data:
            return {"reply": "✅ All products are well-stocked! No alerts right now.", "type": "text"}
        lines = [f"🚨 **{len(data)} Low Stock Items** (need restocking):\n"]
        for d in data:
            urgency = "🔴" if d['current_stock'] < d['reorder_point'] * 0.5 else "🟡"
            lines.append(f"{urgency} **{d['name']}** ({d['category']})\n   Stock: **{d['current_stock']}** / {d['max_stock']} (reorder at {d['reorder_point']}) — {d['fill_pct']}% full")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Inventory Summary ──
    if intent == "inventory_summary":
        data = tq("""
            SELECT COUNT(*) as products,
                   SUM(current_stock) as total_stock,
                   SUM(CASE WHEN current_stock <= reorder_point THEN 1 ELSE 0 END) as low_stock,
                   ROUND(AVG(current_stock * 100.0 / NULLIF(max_stock, 0)), 1) as avg_fill,
                   SUM(CASE WHEN current_stock > max_stock * 0.8 THEN 1 ELSE 0 END) as well_stocked
            FROM inventory
        """)
        r = data[0]
        return {
            "reply": f"📦 **Inventory Overview**:\n\n"
                     f"• **{r['products']}** tracked products\n"
                     f"• **{r['total_stock']:,}** total units in stock\n"
                     f"• Average fill: **{r['avg_fill']}%**\n"
                     f"• 🟢 Well stocked: **{r['well_stocked']}** items\n"
                     f"• 🔴 Need restocking: **{r['low_stock']}** items",
            "type": "metric"
        }

    # ── Total Products ──
    if intent == "total_products":
        data = tq("SELECT COUNT(*) as cnt, COUNT(DISTINCT category) as cats, COUNT(DISTINCT supplier) as sups FROM products")
        r = data[0]
        return {"reply": f"📦 **{r['cnt']}** products across **{r['cats']}** categories from **{r['sups']}** suppliers", "type": "metric"}

    # ── Total Customers ──
    if intent == "total_customers":
        data = tq("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN membership_tier = 'Platinum' THEN 1 ELSE 0 END) as platinum,
                   SUM(CASE WHEN membership_tier = 'Gold' THEN 1 ELSE 0 END) as gold,
                   SUM(CASE WHEN membership_tier = 'Silver' THEN 1 ELSE 0 END) as silver,
                   SUM(CASE WHEN membership_tier = 'Bronze' THEN 1 ELSE 0 END) as bronze
            FROM customers
        """)
        r = data[0]
        return {
            "reply": f"👥 **{r['total']:,}** registered customers\n\n"
                     f"• 💎 Platinum: **{r['platinum']}**\n"
                     f"• 🥇 Gold: **{r['gold']}**\n"
                     f"• 🥈 Silver: **{r['silver']}**\n"
                     f"• 🥉 Bronze: **{r['bronze']}**",
            "type": "metric"
        }

    # ── Top Customers ──
    if intent == "top_customers":
        limit = min(extract_number(msg, 5), 20)
        data = tq(f"""
            SELECT c.first_name || ' ' || c.last_name as name, c.membership_tier,
                   SUM(s.total_price) as spent, COUNT(DISTINCT s.basket_id) as visits,
                   COUNT(s.sale_id) as items_bought
            FROM sales s JOIN customers c ON s.customer_id = c.customer_id
            {time_clause.replace('timestamp', 's.timestamp')}
            GROUP BY s.customer_id, c.first_name, c.last_name, c.membership_tier ORDER BY spent DESC LIMIT :lim
        """, {"lim": limit})
        lines = [f"👑 **Top {limit} Customers{time_suffix}**:\n"]
        for i, d in enumerate(data, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(f"{medal} **{d['name']}** ({d['membership_tier']})\n   Spent: {fmt(d['spent'])} • {d['visits']} visits • {d['items_bought']} items")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Customer Segments ──
    if intent == "customer_segments":
        data = tq("SELECT membership_tier, COUNT(*) as cnt FROM customers GROUP BY membership_tier ORDER BY cnt DESC")
        total = sum(d['cnt'] for d in data)
        lines = ["👥 **Customer Segments**:\n"]
        for d in data:
            share = d['cnt'] / total * 100
            lines.append(f"• **{d['membership_tier']}**: {d['cnt']:,} ({share:.1f}%)")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Profit ──
    if intent == "profit":
        has_cost_check = tq("SELECT COUNT(*) as cnt FROM products WHERE cost IS NOT NULL AND cost > 0")
        has_cost = has_cost_check[0]['cnt'] > 0
        
        if has_cost:
            data = tq(f"""
                SELECT SUM(s.total_price) as revenue,
                       SUM(s.quantity * p.cost) as cost,
                       SUM(s.total_price) - SUM(s.quantity * p.cost) as profit
                FROM sales s JOIN products p ON s.product_id = p.product_id
                WHERE p.cost IS NOT NULL AND p.cost > 0 {time_and}
            """)
            r = data[0]
            revenue = r['revenue'] or 0
            cost = r['cost'] or 0
            profit = r['profit'] or 0
            margin = round(profit / revenue * 100, 1) if revenue else 0
            
            cat_profit = tq(f"""
                SELECT p.category, SUM(s.total_price) as rev,
                       SUM(s.total_price) - SUM(s.quantity * p.cost) as profit
                FROM sales s JOIN products p ON s.product_id = p.product_id
                WHERE p.cost IS NOT NULL AND p.cost > 0 {time_and}
                GROUP BY p.category ORDER BY profit DESC LIMIT 3
            """)
            for c in cat_profit:
                rev_val = c.get('rev') or 0
                prof_val = c.get('profit') or 0
                c['margin'] = round(prof_val / rev_val * 100, 1) if rev_val else 0.0
            note = ""
        else:
            data = tq(f"""
                SELECT SUM(s.total_price) as revenue,
                       SUM(s.quantity * (p.price * 0.65)) as cost,
                       SUM(s.total_price) - SUM(s.quantity * (p.price * 0.65)) as profit
                FROM sales s JOIN products p ON s.product_id = p.product_id
                {time_clause.replace('timestamp', 's.timestamp')}
            """)
            r = data[0]
            revenue = r['revenue'] or 0
            cost = r['cost'] or 0
            profit = r['profit'] or 0
            margin = round(profit / revenue * 100, 1) if revenue else 0
            
            cat_profit = tq(f"""
                SELECT p.category, SUM(s.total_price) - SUM(s.quantity * (p.price * 0.65)) as profit,
                       35.0 as margin
                FROM sales s JOIN products p ON s.product_id = p.product_id
                {time_clause.replace('timestamp', 's.timestamp')}
                GROUP BY p.category ORDER BY profit DESC LIMIT 3
            """)
            note = "\n\n💡 *Note: Product cost data is missing from the dataset. Profit and margins are estimated assuming a 35% average margin (cost = 65% of price).*"

        lines = [
            f"📈 **Profit Analysis{time_suffix}**:\n",
            f"💰 Revenue: {fmt(revenue)}",
            f"💸 Cost: {fmt(cost)}",
            f"✅ **Net Profit: {fmt(profit)}**",
            f"📊 Overall Margin: **{margin}%**\n",
            "🏆 **Most Profitable Categories**:"
        ]
        for c in cat_profit:
            lines.append(f"• **{c['category']}**: {fmt(c['profit'])} ({c['margin']}% margin)")
        if note:
            lines.append(note)
        return {"reply": "\n".join(lines), "type": "metric"}

    # ── Categories ──
    if intent == "categories":
        data = tq("""
            SELECT p.category, COUNT(*) as products,
                   AVG(p.price) as avg_price,
                   SUM(i.current_stock) as total_stock
            FROM products p LEFT JOIN inventory i ON p.product_id = i.product_id
            GROUP BY p.category ORDER BY products DESC
        """)
        lines = [f"📋 **{len(data)} Categories**:\n"]
        for d in data:
            avg_p = round(float(d['avg_price'] or 0), 2)
            lines.append(f"• **{d['category']}** — {d['products']} products, avg ₹{avg_p}, {d['total_stock'] or 0:,} units in stock")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Suppliers ──
    if intent == "suppliers":
        is_pg = (db.bind.dialect.name == "postgresql")
        cat_agg = "STRING_AGG(DISTINCT p.category, ', ')" if is_pg else "GROUP_CONCAT(DISTINCT p.category)"
        data = tq(f"""
            SELECT s.name, s.lead_time_days, s.reliability_score,
                   COUNT(p.product_id) as products, {cat_agg} as categories
            FROM suppliers s LEFT JOIN products p ON p.supplier_id = s.supplier_id OR p.supplier = s.name
            GROUP BY s.supplier_id, s.name, s.lead_time_days, s.reliability_score ORDER BY products DESC
        """)
        if not data:
            return {"reply": "No supplier data available.", "type": "text"}
        lines = ["🚚 **Supplier Overview**:\n"]
        for d in data:
            raw_rel = d['reliability_score'] or 0
            rel = round((raw_rel / 100 if raw_rel > 1 else raw_rel) * 100)
            star = "⭐" if rel >= 95 else "✅" if rel >= 90 else "⚠️" if rel >= 85 else "🔴"
            cats = d['categories'][:40] + "..." if d['categories'] and len(d['categories']) > 40 else (d['categories'] or "N/A")
            lines.append(f"{star} **{d['name']}** — {d['products']} products\n   Reliability: {rel}% • Lead: {d['lead_time_days']}d • Categories: {cats}")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Payment Methods ──
    if intent == "payment_methods":
        data = tq(f"""
            SELECT payment_method, COUNT(*) as cnt, SUM(total_price) as revenue,
                   AVG(total_price) as avg_txn
            FROM sales {time_clause} GROUP BY payment_method ORDER BY revenue DESC
        """)
        total_rev = sum(d['revenue'] for d in data)
        lines = [f"💳 **Payment Methods{time_suffix}**:\n"]
        for d in data:
            share = (d['revenue'] / total_rev * 100) if total_rev else 0
            avg_t = round(float(d['avg_txn'] or 0), 2)
            lines.append(f"• **{d['payment_method']}**: {d['cnt']:,} txns ({share:.1f}%)\n  Revenue: {fmt(d['revenue'])} • Avg: {fmt(avg_t)}")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Expiring ──
    if intent == "expiring":
        is_pg = (db.bind.dialect.name == "postgresql")
        if is_pg:
            data = tq("""
                SELECT p.name, p.category, p.shelf_life_days, i.current_stock, i.last_restock_date,
                       ROUND(p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) as days_left
                FROM inventory i JOIN products p ON i.product_id = p.product_id
                WHERE p.shelf_life_days IS NOT NULL
                  AND (p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) < 14
                  AND (p.shelf_life_days - (CURRENT_DATE - CAST(i.last_restock_date AS DATE))) >= 0
                ORDER BY days_left ASC LIMIT 10
            """)
        else:
            data = tq("""
                SELECT p.name, p.category, p.shelf_life_days, i.current_stock, i.last_restock_date,
                       ROUND(julianday(DATE(i.last_restock_date, '+' || p.shelf_life_days || ' days')) - julianday('now')) as days_left
                FROM inventory i JOIN products p ON i.product_id = p.product_id
                WHERE p.shelf_life_days IS NOT NULL
                HAVING days_left < 14 AND days_left >= 0
                ORDER BY days_left ASC LIMIT 10
            """)
        if not data:
            return {"reply": "✅ No products expiring within 14 days!", "type": "text"}
        lines = [f"⏰ **{len(data)} Products Expiring Soon**:\n"]
        for d in data:
            urgency = "🔴" if d['days_left'] < 3 else "🟡" if d['days_left'] < 7 else "🟢"
            lines.append(f"{urgency} **{d['name']}** — **{int(d['days_left'])}d** left, {d['current_stock']} in stock")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Average Order ──
    if intent == "avg_order":
        data = tq(f"""
            SELECT AVG(basket_total) as avg_basket,
                   AVG(items_count) as avg_items,
                   MAX(basket_total) as max_basket,
                   COUNT(*) as total_baskets
            FROM (
                SELECT basket_id, SUM(total_price) as basket_total, COUNT(*) as items_count
                FROM sales {time_clause} GROUP BY basket_id
            ) sub
        """)
        r = data[0]
        avg_b = round(float(r['avg_basket'] or 0), 2)
        avg_i = round(float(r['avg_items'] or 0), 1)
        max_b = round(float(r['max_basket'] or 0), 2)
        return {
            "reply": f"🛒 **Basket Analytics{time_suffix}**:\n\n"
                     f"• Average basket value: **{fmt(avg_b)}**\n"
                     f"• Average items per basket: **{avg_i}**\n"
                     f"• Largest basket: {fmt(max_b)}\n"
                     f"• Total baskets: {r['total_baskets']:,}",
            "type": "metric"
        }

    # ── Peak Hours ──
    if intent == "peak_hours":
        data = tq(f"""
            SELECT CAST(SUBSTR(timestamp, 12, 2) AS INTEGER) as hour,
                   COUNT(*) as cnt, SUM(total_price) as revenue
            FROM sales {time_clause} GROUP BY hour ORDER BY cnt DESC LIMIT 5
        """)
        lines = [f"🕐 **Peak Shopping Hours{time_suffix}**:\n"]
        for i, d in enumerate(data):
            h = d['hour']
            period = "AM" if h < 12 else "PM"
            display = h if h <= 12 else h - 12
            if display == 0: display = 12
            fire = "🔥" if i == 0 else "📊"
            lines.append(f"{fire} **{display}:00 {period}** — {d['cnt']:,} transactions ({fmt(d['revenue'])})")
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Product Search ──
    if intent == "product_search":
        term = extract_product_term(msg)
        if not term:
            return {"reply": "🔍 What product? Try: \"tell me about milk\" or \"find cheese\"", "type": "text"}
        data = tq("""
            SELECT p.product_id, p.name, p.category, p.price, p.cost, p.supplier, p.shelf_life_days,
                   i.current_stock, i.reorder_point, i.max_stock, i.warehouse_location
            FROM products p LEFT JOIN inventory i ON p.product_id = i.product_id
            WHERE LOWER(p.name) LIKE :term LIMIT 5
        """, {"term": f"%{term}%"})
        if not data:
            return {"reply": f"🔍 No products found matching \"**{term}**\". Try a different search.", "type": "text"}
        lines = [f"🔍 **Found {len(data)} product(s) for \"{term}\"**:\n"]
        for d in data:
            stock = d['current_stock'] or 0
            reorder = d['reorder_point'] or 0
            status = "🟢 In Stock" if stock > reorder else "🔴 Low Stock" if stock > 0 else "⭕ Out of Stock"
            margin = ""
            if d['cost'] and d['cost'] > 0:
                m = (d['price'] - d['cost']) / d['price'] * 100
                margin = f" • Margin: {m:.1f}%"
            lines.append(
                f"**{d['name']}** ({d['category']})\n"
                f"   💰 Price: {fmt(d['price'])} • Cost: {fmt(d['cost'])}{margin}\n"
                f"   📦 {status} ({stock}/{d['max_stock'] or '?'}) • 📍 {d['warehouse_location'] or 'N/A'}\n"
                f"   🚚 Supplier: {d['supplier'] or 'N/A'} • Shelf Life: {d['shelf_life_days'] or '?'}d"
            )
        _context["last_entity"] = term
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Product Sales Performance ──
    if intent == "product_sales":
        term = extract_product_term(msg)
        if not term:
            return {"reply": "Which product? Try: \"how is milk selling?\"", "type": "text"}
        data = tq(f"""
            SELECT p.name, p.category, SUM(s.total_price) as revenue, SUM(s.quantity) as qty,
                   COUNT(DISTINCT s.basket_id) as baskets, COUNT(DISTINCT s.customer_id) as customers,
                   AVG(s.discount) as avg_discount
            FROM sales s JOIN products p ON s.product_id = p.product_id
            WHERE LOWER(p.name) LIKE :term {time_and}
            GROUP BY p.product_id, p.name, p.category ORDER BY revenue DESC LIMIT 3
        """, {"term": f"%{term}%"})
        if not data:
            return {"reply": f"No sales data found for \"**{term}**\"{time_suffix}.", "type": "text"}
        lines = [f"📊 **Sales for \"{term}\"{time_suffix}**:\n"]
        for d in data:
            disc = round(d['avg_discount'] * 100, 1) if d['avg_discount'] else 0
            lines.append(
                f"**{d['name']}** ({d['category']})\n"
                f"   💰 Revenue: **{fmt(d['revenue'])}** • {d['qty']:,} units\n"
                f"   🛒 {d['baskets']} baskets • 👥 {d['customers']} customers • 🏷️ Avg discount: {disc}%"
            )
        return {"reply": "\n".join(lines), "type": "list"}

    # ── Compare Categories ──
    if intent == "compare_categories":
        cats = extract_compared_categories(msg, db, user_id=user_id)
        if not cats or len(cats) < 2:
            return {"reply": "⚖️ Which categories? Try: \"compare Dairy vs Bakery\"", "type": "text"}
        cat1, cat2 = cats[0], cats[1]
        
        has_cost_check = tq("SELECT COUNT(*) as cnt FROM products WHERE cost IS NOT NULL AND cost > 0")
        has_cost = has_cost_check[0]['cnt'] > 0
        
        cost_expr = "p.cost" if has_cost else "p.price * 0.65"
        note = "" if has_cost else "\n\n💡 *Margins estimated (cost = 65% of price) because cost data is missing.*"
        
        data = tq(f"""
            SELECT p.category, SUM(s.total_price) as revenue, SUM(s.quantity) as qty,
                   COUNT(DISTINCT s.basket_id) as baskets,
                   COUNT(DISTINCT p.product_id) as products,
                   SUM(s.quantity * {cost_expr}) as total_cost
            FROM sales s JOIN products p ON s.product_id = p.product_id
            WHERE p.category IN (:c1, :c2)
            {time_and}
            GROUP BY p.category
        """, {"c1": cat1, "c2": cat2})
        for d in data:
            rev_val = d.get('revenue') or 0
            cost_val = d.get('total_cost') or 0
            d['margin'] = round((rev_val - cost_val) / rev_val * 100, 1) if rev_val else 0.0
        if len(data) < 2:
            return {"reply": f"Not enough data to compare **{cat1}** and **{cat2}**.", "type": "text"}
        d1 = next(d for d in data if d['category'] == cat1)
        d2 = next(d for d in data if d['category'] == cat2)
        winner_rev = cat1 if d1['revenue'] > d2['revenue'] else cat2
        winner_margin = cat1 if (d1['margin'] or 0) > (d2['margin'] or 0) else cat2
        return {
            "reply": f"⚖️ **{cat1} vs {cat2}{time_suffix}**:\n\n"
                     f"| Metric | {cat1} | {cat2} |\n"
                     f"|--------|--------|--------|\n"
                     f"| Revenue | {fmt(d1['revenue'])} | {fmt(d2['revenue'])} |\n"
                     f"| Units Sold | {d1['qty']:,} | {d2['qty']:,} |\n"
                     f"| Products | {d1['products']} | {d2['products']} |\n"
                     f"| Margin | {d1['margin']}% | {d2['margin']}% |\n"
                     f"| Baskets | {d1['baskets']:,} | {d2['baskets']:,} |"
                     f"\n\n🏆 Revenue winner: **{winner_rev}**\n"
                     f"📈 Higher margin: **{winner_margin}**"
                     f"{note}",
            "type": "list"
        }

    # ── Growth / Trend ──
    if intent == "growth":
        data = tq("""
            SELECT SUBSTR(timestamp, 1, 7) as month, SUM(total_price) as revenue
            FROM sales GROUP BY month ORDER BY month DESC LIMIT 3
        """)
        if len(data) >= 2:
            curr, prev = data[0], data[1]
            change = ((curr['revenue'] - prev['revenue']) / prev['revenue'] * 100) if prev['revenue'] else 0
            direction = "📈 **Growing**" if change > 0 else "📉 **Declining**" if change < 0 else "➡️ **Flat**"
            return {
                "reply": f"📊 **Revenue Trend**:\n\n"
                         f"• Current month ({curr['month']}): {fmt(curr['revenue'])}\n"
                         f"• Previous month ({prev['month']}): {fmt(prev['revenue'])}\n\n"
                         f"{direction}: **{change:+.1f}%** month-over-month",
                "type": "metric"
            }
        return {"reply": "Not enough monthly data to calculate trend.", "type": "text"}

    # ── Discounts ──
    if intent == "discounts":
        data = tq(f"""
            SELECT AVG(CASE WHEN discount > 0 THEN discount ELSE NULL END) as avg_disc,
                   SUM(CASE WHEN discount > 0 THEN 1 ELSE 0 END) as disc_cnt,
                   COUNT(*) as total_cnt,
                   COUNT(CASE WHEN discount > 0 THEN 1 END) as disc_txns,
                   SUM(CASE WHEN discount > 0 THEN unit_price * quantity * discount ELSE 0 END) as total_saved
            FROM sales {time_clause}
        """)
        r = data[0]
        avg_disc_val = round(float(r['avg_disc'] or 0) * 100, 1)
        total_cnt = r['total_cnt'] or 0
        disc_cnt = r['disc_cnt'] or 0
        disc_pct_val = round((disc_cnt / total_cnt * 100), 1) if total_cnt else 0.0
        return {
            "reply": f"🏷️ **Discount Analysis{time_suffix}**:\n\n"
                     f"• Average discount: **{avg_disc_val}%**\n"
                     f"• Transactions with discounts: **{disc_pct_val}%** ({r['disc_txns'] or 0:,} txns)\n"
                     f"• Total customer savings: **{fmt(r['total_saved'] or 0)}**",
            "type": "metric"
        }

    # ── Total Transactions ──
    if intent == "total_transactions":
        data = tq(f"""
            SELECT COUNT(*) as txns, COUNT(DISTINCT basket_id) as baskets,
                   COUNT(DISTINCT customer_id) as customers,
                   COUNT(DISTINCT product_id) as products
            FROM sales {time_clause}
        """)
        r = data[0]
        return {
            "reply": f"🧾 **Transaction Stats{time_suffix}**:\n\n"
                     f"• Total transactions: **{r['txns']:,}**\n"
                     f"• Unique baskets: **{r['baskets']:,}**\n"
                     f"• Unique customers: **{r['customers']:,}**\n"
                     f"• Products sold: **{r['products']}**",
            "type": "metric"
        }

    # ── Category Detail (fallback when category detected) ──
    if intent == "category_detail":
        cat = extract_category(msg, db, user_id=user_id)
        if not cat:
            return None  # Let it fall through
            
        has_cost_check = tq("SELECT COUNT(*) as cnt FROM products WHERE cost IS NOT NULL AND cost > 0")
        has_cost = has_cost_check[0]['cnt'] > 0
        cost_expr = "p.cost" if has_cost else "p.price * 0.65"
        note = "" if has_cost else "\n\n💡 *Margin estimated (cost = 65% of price) because cost data is missing.*"
        
        data = tq(f"""
            SELECT SUM(s.total_price) as revenue, SUM(s.quantity) as qty,
                   COUNT(DISTINCT p.product_id) as products,
                   COUNT(DISTINCT s.customer_id) as customers,
                   AVG(p.price) as avg_price,
                   SUM(s.quantity * {cost_expr}) as total_cost
            FROM sales s JOIN products p ON s.product_id = p.product_id
            WHERE p.category = :cat
        """, {"cat": cat})
        r = data[0]
        r_rev = float(r.get('revenue') or 0)
        r_cost = float(r.get('total_cost') or 0)
        r['avg_price'] = round(float(r['avg_price'] or 0), 2)
        r['margin'] = round((r_rev - r_cost) / r_rev * 100, 1) if r_rev else 0.0

        # Top 3 products in category
        top = tq("""
            SELECT p.name, SUM(s.total_price) as revenue
            FROM sales s JOIN products p ON s.product_id = p.product_id
            WHERE p.category = :cat
            GROUP BY p.product_id, p.name ORDER BY revenue DESC LIMIT 3
        """, {"cat": cat})
        top_lines = "\n".join(f"   {i}. **{t['name']}** — {fmt(t['revenue'])}" for i, t in enumerate(top, 1))

        return {
            "reply": f"📂 **{cat} Category Deep Dive**:\n\n"
                     f"💰 Revenue: **{fmt(r['revenue'])}**\n"
                     f"📊 Margin: **{r['margin']}%**\n"
                     f"📦 Products: **{r['products']}** • Avg price: {fmt(r['avg_price'])}\n"
                     f"🛒 Units sold: **{r['qty']:,}** • 👥 Customers: **{r['customers']:,}**\n\n"
                     f"🏆 **Top Products**:\n{top_lines}"
                     f"{note}",
            "type": "metric"
        }

    return None


def extract_compared_categories(msg, db, user_id=None):
    """Extract two categories from a comparison query."""
    categories = get_categories(db, user_id=user_id)
    found = []
    msg_lower = msg.lower()

    for cat in categories:
        if cat.lower() in msg_lower:
            found.append(cat)

    if len(found) >= 2:
        return found[:2]

    # Try fuzzy matching words
    words = re.findall(r'[a-z]+', msg_lower)
    for word in words:
        if len(word) < 3 or word in ["compare", "vs", "versus", "and", "between", "with", "the"]:
            continue
        match = fuzzy_match(word, categories, threshold=0.65)
        if match and match not in found:
            found.append(match)

    return found[:2] if len(found) >= 2 else found


# ── Main Endpoint ──

@router.post("")
def chat(
    body: ChatMessage,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    user_id = current_user.id if current_user else None
    raw_session = body.session_id or "default"
    session_id = f"{user_id}:{raw_session}" if user_id else f"anon:{raw_session}"
    msg = body.message.strip()

    if not msg:
        return {"reply": "Say something! I'm listening 👂", "type": "text"}

    if not current_user:
        intent, score = score_intent(msg)
        if intent in ["greeting", "help"]:
            response = respond(intent, msg, db, session_id=session_id, user_id=None)
            if response:
                return response
        return {
            "reply": "🔒 Please sign in to your account to query and view your store's data, metrics, and insights.",
            "type": "text"
        }

    # Score intents
    intent, score = score_intent(msg)

    # If low confidence, try category detection as fallback
    if score < 1.5:
        cat = extract_category(msg, db, user_id=user_id)
        if cat:
            intent = "category_detail"
            score = 2.0

    # Try product search as fallback for very low scores
    if score < 1.0:
        # Check if it looks like a product name query
        products = query_db(db, "SELECT name FROM products WHERE LOWER(name) LIKE :term LIMIT 1",
                           {"term": f"%{msg.lower()[:20]}%"}, user_id=user_id)
        if products:
            intent = "product_search"
            score = 2.0

    # Generate response
    response = respond(intent, msg, db, session_id=session_id, user_id=user_id)

    if response:
        # Define intent-specific suggestions & chart data
        suggestions = []
        chart_type = None
        chart_data = None
        
        # 1. Map intent suggestions
        if intent == "greeting":
            suggestions = ["total revenue", "best sellers", "low stock items", "customer segments"]
        elif intent == "help":
            suggestions = ["total revenue", "peak hours", "inventory summary"]
        elif intent == "summary":
            suggestions = ["monthly revenue", "sales by category", "profit Analysis"]
        elif intent in ["total_revenue", "daily_revenue", "monthly_revenue"]:
            suggestions = ["sales by category", "profit margins", "average order"]
        elif intent == "category_revenue":
            suggestions = ["compare categories", "best sellers", "monthly revenue"]
        elif intent in ["best_sellers", "worst_sellers"]:
            suggestions = ["revenue by category", "low stock", "profit margins"]
        elif intent in ["low_stock", "inventory_summary", "total_products"]:
            suggestions = ["expiring soon", "suppliers overview", "total revenue"]
        elif intent in ["total_customers", "top_customers", "customer_segments"]:
            suggestions = ["customer segments", "top customers", "average order"]
        elif intent == "profit":
            suggestions = ["revenue by category", "average order", "discount analysis"]
        elif intent == "categories":
            suggestions = ["revenue by category", "compare categories", "inventory summary"]
        elif intent == "suppliers":
            suggestions = ["low stock", "expiring soon"]
        elif intent == "payment_methods":
            suggestions = ["peak hours", "average order"]
        elif intent == "expiring":
            suggestions = ["inventory summary", "low stock"]
        elif intent == "avg_order":
            suggestions = ["payment methods", "profit margins"]
        elif intent == "peak_hours":
            suggestions = ["payment methods", "total revenue"]
        elif intent in ["product_search", "product_sales"]:
            suggestions = ["best sellers", "low stock", "total products"]
        elif intent == "compare_categories":
            suggestions = ["revenue by category", "profit margins"]
        elif intent == "growth":
            suggestions = ["monthly revenue", "total revenue"]
        elif intent == "discounts":
            suggestions = ["profit margins", "average order"]
        elif intent == "total_transactions":
            suggestions = ["peak hours", "average order"]
        elif intent == "category_detail":
            suggestions = ["compare categories", "best sellers", "total revenue"]

        # 2. Add chart data for specific intents strictly isolated by user_id
        try:
            if intent == "monthly_revenue":
                chart_type = "line"
                chart_db = query_db(db, """
                    SELECT SUBSTR(timestamp, 1, 7) as label, SUM(total_price) as value
                    FROM sales GROUP BY label ORDER BY label DESC LIMIT 6
                """, user_id=user_id)
                chart_data = list(reversed([{"label": d["label"], "value": round(d["value"], 2)} for d in chart_db if d["value"]]))
            elif intent == "category_revenue":
                chart_type = "bar"
                chart_db = query_db(db, """
                    SELECT p.category as label, SUM(s.total_price) as value
                    FROM sales s JOIN products p ON s.product_id = p.product_id
                    GROUP BY label ORDER BY value DESC
                """, user_id=user_id)
                chart_data = [{"label": d["label"], "value": round(d["value"], 2)} for d in chart_db if d["value"]]
            elif intent == "customer_segments":
                chart_type = "pie"
                chart_db = query_db(db, "SELECT membership_tier as label, COUNT(*) as value FROM customers GROUP BY label ORDER BY value DESC", user_id=user_id)
                chart_data = [{"label": d["label"], "value": d["value"]} for d in chart_db if d["value"]]
            elif intent == "peak_hours":
                chart_type = "line"
                chart_db = query_db(db, """
                    SELECT CAST(SUBSTR(timestamp, 12, 2) AS INTEGER) as hr, COUNT(*) as cnt
                    FROM sales GROUP BY hr ORDER BY hr ASC
                """, user_id=user_id)
                chart_data = []
                for d in chart_db:
                    h = d["hr"]
                    label = f"{h if h <= 12 else h-12}{'AM' if h < 12 else 'PM'}"
                    if h == 0: label = "12AM"
                    if h == 12: label = "12PM"
                    chart_data.append({"label": label, "value": d["cnt"]})
            elif intent == "payment_methods":
                chart_type = "bar"
                chart_db = query_db(db, "SELECT payment_method as label, SUM(total_price) as value FROM sales GROUP BY payment_method ORDER BY value DESC", user_id=user_id)
                chart_data = [{"label": d["label"], "value": round(float(d["value"] or 0), 2)} for d in chart_db if d["value"]]
            elif intent == "profit":
                chart_type = "bar"
                has_cost_check = query_db(db, "SELECT COUNT(*) as cnt FROM products WHERE cost IS NOT NULL AND cost > 0", user_id=user_id)
                has_cost = has_cost_check[0]['cnt'] > 0 if has_cost_check else False
                cost_expr = "p.cost" if has_cost else "p.price * 0.65"
                chart_db = query_db(db, f"""
                    SELECT p.category as label, 
                           SUM(s.total_price) as rev,
                           SUM(s.quantity * {cost_expr}) as cost
                    FROM sales s JOIN products p ON s.product_id = p.product_id
                    GROUP BY p.category
                """, user_id=user_id)
                chart_data = []
                for d in chart_db:
                    rev_val = float(d.get("rev") or 0)
                    cost_val = float(d.get("cost") or 0)
                    margin_val = round((rev_val - cost_val) / rev_val * 100, 1) if rev_val else 0.0
                    chart_data.append({"label": d["label"], "value": margin_val})
                chart_data.sort(key=lambda x: x["value"], reverse=True)
        except Exception as e:
            # Silently log/fallback if query fails
            print(f"Chart data error: {e}")

        # Update response dict
        response["suggestions"] = suggestions
        if chart_type and chart_data:
            response["chart_type"] = chart_type
            response["chart_data"] = chart_data

        # Update context
        _ctx = _get_context(session_id)
        _ctx["last_intent"] = intent
        _ctx["history"].append({"role": "user", "text": msg})
        _ctx["history"].append({"role": "bot", "text": response["reply"][:100]})
        # Keep history short
        if len(_ctx["history"]) > 20:
            _ctx["history"] = _ctx["history"][-20:]
        return response

    # Fallback — smart suggestions based on what they said
    suggestions = []
    msg_lower = msg.lower()
    if any(w in msg_lower for w in ["sell", "sale", "buy", "purchase"]):
        suggestions = ["total revenue", "best sellers", "sales by category"]
    elif any(w in msg_lower for w in ["stock", "product", "item"]):
        suggestions = ["inventory summary", "low stock", "total products"]
    elif any(w in msg_lower for w in ["customer", "people", "buyer", "shopper"]):
        suggestions = ["total customers", "top customers", "customer segments"]
    elif any(w in msg_lower for w in ["money", "cost", "price", "earn", "spend"]):
        suggestions = ["profit margins", "total revenue", "average order"]
    else:
        suggestions = ["total revenue", "top products", "low stock", "customer segments"]

    suggestion_text = "\n".join(f"• \"{s}\"" for s in suggestions)
    return {
        "reply": f"🤔 I'm not sure what you mean by that. Try asking:\n{suggestion_text}\n\nOr type **help** for all my capabilities!",
        "type": "text"
    }
