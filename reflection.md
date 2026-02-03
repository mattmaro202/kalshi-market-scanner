# Reflection

## My Approach

I chose the Kalshi prediction market scanner over sports odds because I have hands-on experience with trading systems and market data from building projects like LedgerLock and various trading bots. Prediction markets are also more interesting from an analytical perspective - bid-ask spreads reveal market efficiency and liquidity issues that are valuable for traders.

My strategy was to start with the API integration first, make sure authentication worked, then build out the filtering and display logic incrementally. I used Claude Code to handle the initial setup and API research, letting it explore the Kalshi documentation while I focused on defining clear requirements upfront. The key was being specific about what I needed (24-hour filter, spread calculation, error handling) rather than asking vague questions.

## Course Corrections & Iterations

The biggest course correction came when the initial implementation tried to fetch all active markets before filtering - this was hanging because Kalshi has thousands of markets. Claude Code recognized this performance issue and optimized the approach to use API-level filtering with min_close_ts and max_close_ts parameters, which brought the response time down dramatically. This was a good example of where letting the AI iterate and optimize made sense rather than micromanaging every detail.

Another iteration was around the spread calculation - initially the code was using fallback logic for missing price fields, but after inspecting the actual API response structure, we simplified it to directly use the yes_bid, yes_ask, no_bid, no_ask fields that Kalshi provides. The error handling also evolved from basic try-catch to specific handling for 401/403 errors with helpful messages.

## What I'd Do Differently

With more time, I'd add real-time monitoring with websockets to track spread changes as markets approach close, a database to store historical spread data for pattern analysis, and a web dashboard for easier visualization. Unit tests and proper logging would make it more production-ready. But for a 2-3 hour take-home focused on shipping working code under time pressure, I prioritized getting the core functionality working reliably and demonstrating clear problem-solving in the development process. The goal was to show I can use AI tools effectively to build something that works, not to build a perfect production system.
