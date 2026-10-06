# Usability Improvements — Problem 9

There are four improvements: two on the frontend and two in the agent/backend. Each one shows up in the running app, and `output/app_check.html` has screenshots.

---

## Frontend 1 — Item Shop filters: category, size, in-stock, sort

**What was added**

- The Products page has a filter bar:
  - Category tabs: All, Hoodies, Crewnecks, Tees, Quarter-Zips, Jackets & Fleece.
  - "My size" buttons (XS–XXL) that show only items with stock in that size.
  - An "In stock only" toggle.
  - A sort menu: Featured, Price low→high, Price high→low, Name.
- Each category tab shows how many items it holds. The bar shows "Showing N of 102" with a one-click "Reset".
- Filters are saved in the URL (e.g. `/products?cat=hoodies&size=M&sort=price-asc`), so Back works and a filtered view can be shared or bookmarked.
- `ProductCard` from the API now includes `sizes_in_stock`, so size filtering happens instantly in the browser without extra requests.

**How it helps Campus Customs**

- 102 items in one grid is a lot to scroll. Shoppers can now go straight to "hoodies in my size that are in stock", which means fewer dead ends and a shorter path to buying.
- Filtering out sold-out sizes means shoppers don't fall for an item and then find their size is gone, which is a common reason people give up and leave.
- Shareable filtered links let staff post things like "Crewnecks under $60" on social media or in emails.

---

## Frontend 2 — Chat quick-replies and "Ask the llama" on product pages

**What was added**

- **Quick-reply chips** in the chat panel that change with the page:
  - On a product page: "Is this in stock in M?", "What colors does it come in?", "Show me similar items".
  - Everywhere else: "What hoodies do you have?", "Gifts under $40", "Crewnecks in navy".
- An **"Ask the llama about this item"** button on every product page. It opens the chat with a question about that item already filled in.
- A pulsing badge on the chat button until the shopper opens the chat for the first time.

**How it helps Campus Customs**

- Many shoppers don't know what a shop chatbot can do. The chips show them the most useful questions (stock, colors, similar items), so they get value from the assistant in one tap.
- Stock and size questions are a top reason people leave a product page. Answering them in place keeps shoppers on the item they were about to buy.
- The badge gets more people to try the chat, and that leads more of them to product cards.

---

## Backend 1 — New tool: `find_alternatives` (save the sale when a size or color is gone)

**What was added**

- A new agent tool, `find_alternatives(product_id?, size?, color?)`. It returns up to 6 similar items that:
  - are in the same garment family (hoodie, crewnecks, tees, quarter-zips, jackets),
  - **are in stock in the requested size**,
  - match the requested color if one is given.
- Results are ranked by shared tags (same college, sport or style) and closeness in price.
- The prompt tells the agent to call it every time a size is sold out or a color isn't offered, and to return the results as product cards.

**How it helps Campus Customs**

- Before, "sorry, XS is sold out" ended the conversation. Now the shopper gets 3–6 in-stock items that fit and look similar, shown as clickable cards, so a lost sale becomes a recommendation.
- Inventory spreads across more products, which helps sell items that are overstocked.

---

## Backend 2 — Price fact-checker, plus faster and cheaper runs

**What was added**

- **Price fact-checker** (`@agent.output_validator` in `agent.py`): before any reply reaches the shopper, the backend finds every dollar amount in it and checks that each one came from a tool result or the shopper's own message (e.g. "under $60").
  - If the agent states a price that isn't backed by data, the run is sent back to the model with a correction request, and it re-checks with its tools.
  - Any `product_ids` that don't exist in the catalogue are also rejected.
  - Fact-check retries are logged in `output/audit_trail.json`.
- **Run limits for speed and cost:**
  - At most 6 model requests and 8 tool calls per message.
  - Only the last 20 messages are sent as history.
  - Search results are capped at 30, with an exact `count`.
  - Product data is shortened so it uses fewer tokens.
  - A per-shopper rate limit of 15 messages per minute protects the API budget from spam.

**How it helps Campus Customs**

- A wrong price in chat is a customer-service problem and can be a legal one. The fact-checker means chat prices always match the register.
- The limits keep each answer quick (a few seconds) and the per-message model cost low and predictable, even when someone tries to flood the chat.
