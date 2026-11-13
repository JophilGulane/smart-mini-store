# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary:** a student developer demonstrating a capstone-style project to an instructor or panel, on a laptop, in a live walkthrough and Q&A.
- **Secondary:** a single mini-store operator using the same local app to keep products, stock, and sales.
- **Evaluators:** instructors who need to see that supervised, unsupervised, and reinforcement learning are implemented honestly and understandably.

## Product Purpose

A local, single-user inventory assistant for a mini-store. It records products, stock receipts, and sales, then demonstrates three machine-learning paradigms on that recorded data: Decision Tree demand forecasting, K-means product grouping, and tabular Q-learning restocking. Success is a credible, self-explanatory demonstration: the numbers are real measurements, the limits are stated, and every workflow completes without an account or a network connection.

## Positioning

A working inventory ledger and a working ML lab in one local app. Every result comes from the user's own recorded history, every model run is saved with its timestamps and data cutoff, and the app reports when a learned policy does not beat a simple rule instead of hiding it.

## Operating Context

- Runs locally with Streamlit on Windows (verified with Python 3.14) and opens through `launch.bat`.
- Two isolated SQLite workspaces: a clearly labeled synthetic **Demonstration** and an initially empty **My store**.
- Dates and business-day checks use Asia/Manila (UTC+8).
- Presented live on a laptop, sometimes projected; the audience watches the presenter operate the app and asks about model behavior afterward.
- No login, no cloud service, no API keys, no internet needed after install.
- 34 automated checks cover transactions, ML correctness, and the Streamlit screens; the README documents the workflow and limits.

## Capabilities and Constraints

- Six screens: Dashboard, Products & Stock, Record Sales, Demand Forecast, Product Groups, Restocking Simulator.
- Stock and sales commit atomically; money is stored as integer centavos; sale prices and costs are immutable per receipt.
- Demo workspace seeds 12 products and 90 completed historical days; workspaces never mix.
- ML pages require completed daily history, not merely current stock: 35 observations for forecasts and RL, complete 30-day windows for clustering.
- The restocking simulator never changes real stock; its suggestions are advisory.
- The verified 3,000-episode Q-learning run did not outperform the simple restocking rules and the UI must keep saying so.
- Streamlit 1.67 with Plotly 7.1; the app must keep working offline.
- Known stockouts are excluded where reliable demand is needed; missing days are unknown, not zero.

## Brand Commitments

- Name: **Smart Mini-Store**, presented in-app as **Mini-Store**.
- Voice: plain, factual, instructor-safe. Never overclaim; name the limitation next to the result.
- Synthetic demo data is always labeled.
- Philippine peso (PHP) and the Manila business date are explicit, not implied.

## Evidence on Hand

- Generated demo data and trained model artifacts are produced locally by `manage.py`; none ship in the repository.
- Measured evaluation outputs are written to `output/evaluation/` when training runs.
- No customer testimonials, benchmarks, or commercial claims exist, and none may be fabricated.

## Product Principles

1. **The task comes first.** A routine sale, receipt, or stock check should never be buried under explanation.
2. **Show the measurement, name the limit.** Model results carry their cutoff, sample size, and comparison, in the same view.
3. **Every state is honest.** Empty, stale, insufficient-data, and out-of-stock states explain what to do next.
4. **One system, six screens.** Navigation, language, spacing, and data presentation stay consistent from dashboard to simulator.
5. **Calm is a feature.** A dense screen is fine; a noisy one is not. The presenter should always know where they are and what changed.

## Accessibility & Inclusion

- Readable at projector distance: strong contrast, tabular numerals, status conveyed by text as well as color.
- Full keyboard operation of forms and navigation; visible focus rings.
- No interaction dependent on hover alone.
