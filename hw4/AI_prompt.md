# AI Prompt Log — AI for Managers, Homework 4

A log of every prompt I typed into my vibe coder (Claude Code) while working through Homework 4.

**Format:** one section per problem. Each section has a problem number and title, at least one prompt written in my own words, and a follow-up prompt where I needed one. My running site, database writes, and screenshots are the evidence of the completed work.

---

## Problem 1 — Prompt log setup

**Prompt:**

> I'm now going to be working on Homework 4 of AI for Managers. First, I need you to create an AI_prompt.md at the start of the assignment. This is going to keep everything updated as I work. It's a file of what I typed into the Vibecoder. I need to describe each problem in my own words.

**Follow-up prompt:**

> There needs to be one section for each problem, including:
>
> * the problem number and title
> * at least one prompt I typed in my own words as much as possible
> * a follow-up prompt if needed
>
> I'm running my site database writes, and screenshots are the evidence. I don't need any extra proof.

---

## Problem 2 — Understand the database and start the harness

**Prompt:**

> Look at the database in data/campus_customs.db to understand the fields of this table. At a minimum, I need to understand the catalogue, inventory, and users. I need to start the file output/harness.md to write down each table and its fields and one short line of why each field matters for the shop or chatbot. I'll need to keep growing this harness file in later problems. This is for problem 2, by the way.

---

## Problem 3 — React frontend, product pages, chat stub, and starter API

**Prompt:**

> Now, for problem 3, I'll need to scaffold a React + Vite + TypeScript frontend for Campus Customs. I'll put a nav bar at the top that links to the main pages:
>
> * Home
> * Products
> * About Us
> * Login
> * Create Account
>
>  I'll need to pull Campus Customs style wording from yalebulldogblue.com for Home and About Us, but I'll write these pages in my own voice.On the products page, I'll show the product images from the catalogue. Use the image paths in the database with the basic product info. I'll then make each product open a single-item package: large image on one side, full product text on the other. Description, price, size/stock when you have them. Clicking a card on the product should take the shopper there.
>
> I need to add a chat inference interface in the bottom right of the site. A floating chat panel is fine. It does not need to talk to an agent yet. A stub that will call my backend later is enough for this problem.
>
> I need a small API soon to read the database. It's fine to start a simple FastAPI app in backend/main.py just to serve products and images, then grow it into the agent backend in problem 5.

---

## Problem 4 — Create account and login flow

**Prompt:**

> I then need to build a normal create account/login flow.
>
> * Create account: I need a first name, last name, email, and password. Confirm password is a nice touch as well.
> * Log in with email and password.
> * A new account should go into the `users` table to make sure they store passwords securely, so no hackers can access them.
>
>  The seed database already has our test users you can use while bundling: email test@campuscustoms.yale.edu, and the password should be password. I can then confirm that you can log in as a user and that creating a brand-new account also works. I'll need to update output/harness.md with how auth works, what I store for users, and how passwords are protected.

---

## Problem 5 — Shop chatbot as a PydanticAI agent behind FastAPI

**Prompt:**

> Now, for problem 5, I'll need to build a shop chatbot as a PydanticAI agent behind FastAPI. I need to plug in the frontend chat widget. Put the API app in backend/main.py. That's the file that I'll run with Uvicorn. I'll keep these agents as the next four files next to it:
>
> * backend/prompts/AI_prompt.md: the system prompt. Grow this same file later.
> * backend/agent.py: the agent entry/wiring.
> * backend/tools.py: the tools the agent can call.
> * backend/models.py: the PydanticAI structure types.
>
>  In main.py, I need to expose a chat route so that the messages from the websites return a reply from the agent, and whatever else I need for the product/auth. I'll need to use the AI model API key from the agent. I'll put campus customs, voice, and safety basics into prompt/AI_prompt.md. I'll expand tools and safety later, but start or update types in models.py for chat replies and product cards as needed. In output/harness.md, note how well the frontend talks to FastAPI and how the agent is loaded (prompt file + model). Need to make sure the backend runs from the backend folder like this: uvicorn main:app --reload --port 8000

---

## Problem 6 — Agent tools that read the real database

**Prompt:**

> Now, for problem 6, I need to give the agent tools that can look up real information from campus_customs.db:
>
> * the product description
> * price
> * how many are in stock
> * by size when the customer asks
>
>  This agent must also use the database. It should not invent prices, quality, or quantities. If a size is out of stock, say so clearly. I'll expand prompt/AI_prompt.md so the agent knows to call these tools for price and stock questions. I'll add any update return types in models.py. In outputs/harness.md, I'll need to list each tool and explain which model fields I chose to look up results and why.

---

## Problem 7 — Chat search results as product cards on the page

**Prompt:**

> Now I'll add a feature to the site which allows customers, when they're asked about a type of item (for example, "What hoodies do you have?"), to have the agent search the catalogue on the website. Both the catalogue and the website should dynamically show those matching items as product cards:
>
> * image
> * name
> * price
> * short info
>
>  This is an API contract. The agent returns structured product matches, and then the frontend renders them on the website. After the dynamic product cards are loaded by the new feature, I'll make sure the same single-item package behaviour I built in problem 3 still works. Each product card, including the ones the chat just put on the page, should still open the detail view (large image plus full info) when clicked. Then I'll update prompt/Prompt.md and output/harness.md so that it's clear how search results reach this page.

---

## Problem 8 — Saved chat history, customer context, and page context

**Prompt:**

> When a shopper is logged in, I'll need to save their chat history in the database in an appropriate table and reload it when they return. The agent should know who's chatting (name and email), put that in the agent deps (or equivalently, a clear pattern), and /all tools the agent can call. Also pass enough page context that, if someone is on a product page and asks, "Do you have it in pink?", the agent knows which item they mean.
>
> Hint: I can put the code into the agent context. Guests can still chat, but the history only needs to persist for logged-in users. Document this in output/harness.md for how a user's chat history is stored, what customer fields the agent sees, and how the page context is passed.

---

## Problem 9 — Usability improvements

**Prompt:**

> Now that the core shop works, make sure it does. I need to improve it, and I need to choose and implement two frontend usability improvements and two agent/backend usability improvements. The frontend improvements are things that can make the site look better and easier to use, and the backend improvements are things that make the agent output better, more accurate, and safer. These could be new tools or things that make it run faster and cheaper. I need to write output/usability.md before or as I build this. For each of the improvements, say what was added and what helps the campus custom shop or business. Then make sure all improvements actually show up in the running app. This is for problem 9.

---

## Problem 10 — Creative storefront design

**Prompt:**

> I'll then need to add a creative design so the site feels like a real campus custom storefront with fonts, colours, hierarchy, motion, product presentation, and chat feel. I'll get more points for a more imaginative design. I'll then need to write output/design.md: what I changed and how it should help customers stick around and buy. I need to make this part concrete and short.

---

## Problem 11 — Live app check page with screenshots

**Prompt:**

> I'll then need to test the live site and document it in output/app_check.html, a page that I can double-click open. Include screenshots and short captions for:
>
> * the chat checking the inventory level of an item (on a stock/price from the DB)
> * the dynamic search result cards appearing after a category question
> * one of the usability features I added in problem 9
>
>  I'll then need to make the HTML easy to grade: headings for each check, screenshots, or one or two sentences of what the screenshot provides. I need to put the screenshot images into output/app_check_images/ and link them from app_check.html with relative paths. For example, app_check_images/inventory.png.

---

## Problem 12 — Audit trail, safety rules, and finished harness

**Prompt:**

> Keep the append-only output/audit_trail.json of agent loop activity: time, tool name, short arg/result, stop reason. Need to not wipe this between runs. Also, think of some safety rules to give the agent to put them in prompts/AI_prompt.md and finish output/harness.md so that it's clear how the system works:
>
> * Model fields in models.py and why I chose them
> * Tools and abilities
> * Safety rules
> * Specs like loop limits, result caps
> * Models
> * How to run front plus back

---

## Problem 13 — Package as hw4 and publish to GitHub

**Prompt:**

> I then need to put the code in a folder named `hw4` and push it to a public GitHub repository. I'll then need to submit this, so let me know when this is done.

**Follow-up prompt:**

> Now that it's in the folder HW4, I need to push it to a public GitHub repo. On Canvas, I'll need to submit the repo URL, so give me this:
>
> * I don't need to upload the zip for this homework.
> * I don't need to put real .env, campuscustoms.db, or product images in the GitHub repo.
> * Use .gitignore to include .env.example with placeholders only.

---
