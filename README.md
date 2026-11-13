# Smart Mini-Store Inventory Assistant

A functional, local inventory application demonstrating supervised learning (Decision Tree regression), unsupervised learning (K-means), and reinforcement learning (tabular Q-learning).

## Start on this computer

Double-click **launch.bat** in the project folder. It starts the local Streamlit app and opens a browser. Stop the server with Ctrl+C in its console when finished.

If the app is already running, open <http://127.0.0.1:8501>.

PowerShell alternative, from the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

## Fresh installation

The verified development environment is Windows with Python 3.14.6. Use Python 3.14 for the supplied dependency lock. An Internet connection is needed for the initial installation, not for normal use afterward.

Clone the repository and open its folder first:

```powershell
git clone https://github.com/JophilGulane/smart-mini-store.git
cd smart-mini-store
```

Then install dependencies, generate the demo data and models, and start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py train-demo
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

`requirements.txt` pins direct dependencies. `requirements-lock.txt` records the complete environment used for verification; use it instead for an exact recreation on a compatible Windows/Python installation.

Databases, trained models, and generated outputs are created locally and are not stored in the repository. No API keys or external accounts are required.

## Workspaces

- **Demonstration** automatically seeds an empty `data/demo.db` with 12 products and 90 completed historical days (1,080 daily observations). The records are clearly labeled synthetic. Reopening or repeating setup preserves existing data.
- **My store** uses an independent, initially empty `data/store.db`. Add your products, record opening balances and stock receipts, and enter sales. There is no account or cloud service.
- All dates and business-day checks use Asia/Manila (UTC+8).
- The RL simulator never changes either workspace's real stock.

Opening the app creates the databases as needed. Working records and demo records are never combined. For automated testing, `MINISTORE_DATA_DIR` can point to a disposable isolated directory.

## Functional inventory workflow

1. Open **Products & Stock > Add product**. Enter name, category, cost, price, opening units, and low-stock threshold.
2. Use **Receive stock** when goods actually arrive. The stock movement is saved.
3. Open **Record Sales**, select the product, and save a positive whole-number quantity. Overselling is rejected. A receipt confirms the deduction.
4. Click **Start another sale** before entering a further sale. Repeated processing of a submission token cannot duplicate the same sale.
5. Open **Dashboard** to inspect current inventory and sales over a chosen date range. Export records using the CSV controls.
6. Edit product details or archive a product from **Products & Stock**. Existing receipts preserve their original price and cost.

Stock and sale records commit together in one SQLite transaction. Money is stored as integer centavos. Stock balances can be reconciled with opening, receipt, and sale movements. Prices on current products do not rewrite historical revenue.

## Historical observations

The ML pages need completed daily history. A newly created product does not have enough history simply because it has current stock.

In **Products & Stock > History & data**:

- Export existing history or download the CSV header template.
- Import CSV with `product_id,date,units_sold,stockout_flag`. Dates use `YYYY-MM-DD`; quantities are nonnegative whole numbers; stockout_flag is optional and defaults to 0. Use 1 if unavailable stock limited sales.
- The importer rejects unknown products, invalid/incomplete dates, duplicates, and invalid quantities. A rejected import writes no rows.
- Imports are analytical observations, not stock transactions. They do not create receipts, revenue, or stock movements.
- For sales recorded inside the app, finalize a completed day after checking all transactions. Explicitly confirm zero-sales observations and select any stockout products. Existing observations are preserved.

Missing dates remain unknown. They are not silently treated as zero demand. Known stockout observations are excluded where the model requires reliable demand proxies.

## Three implemented ML paradigms

### 1. Decision Tree regression

Files: `ml/forecasting.py`, `views/forecasting.py`.

Select a product in **Demand Forecast** and click **Train & evaluate forecast**.

- Features: target weekday, yesterday's units, and preceding seven-day mean. Rolling sales are shifted before calculation.
- Target: units sold that day. Under adequate stock, these sales are a proxy for demand.
- Model: `DecisionTreeRegressor(max_depth=3, min_samples_leaf=5, random_state=42)`.
- Evaluation: earlier 80% of eligible dates for training, later 20% for testing. MAE is average absolute error in units. Compare against the preceding seven-day mean.
- The held-out result is a one-day-ahead evaluation using earlier actual observations. It is not a whole multi-day forecast made at once.
- After evaluation, a separate final tree fits all eligible history for the next-day estimate.
- Require at least 35 raw completed observations, 28 usable feature rows, and seven consecutive non-stockout days for next-day inference.

Show the feature preview, actual/predicted chart, measured errors, and readable tree rules during Q&A. An out-of-date record produces a forecast for the day following its latest history; the UI displays that date explicitly.

### 2. K-means clustering

Files: `ml/clustering.py`, `views/clustering.py`.

Open **Product Groups** and click **Run product clustering**.

- One row per product, with mean and population standard deviation of daily units sold.
- Use the same latest completed 30-day window for every eligible product.
- Require at least three products with complete non-stockout windows and distinct feature vectors.
- Apply `StandardScaler` before `KMeans(n_clusters=3, n_init=10, random_state=42)`.
- No true cluster labels are supplied. Descriptive volume names are assigned after fitting, by comparing group means; they are relative descriptions, not validated business classes.
- The chart, assignments, group statistics, scaled features, and optional silhouette score are visible. Silhouette is not classification accuracy.

### 3. Tabular Q-learning

Files: `ml/restocking_env.py`, `ml/q_learning.py`, `ml/evaluation.py`, `views/simulator.py`.

Open **Restocking Simulator**, select a product with at least 35 suitable observations and selling price above cost, then click **Train restocking agent**.

- State: current stock (0..30) and weekday (Monday..Sunday): at most 217 states.
- Action: order 0, 5, 10, or 15 units. Orders exceeding capacity are masked.
- Episode: one week, starting with zero inventory. Deliveries are immediate; remaining goods carry into the next day.
- Demand: Poisson samples from weekday means estimated on the earliest 80% of usable history. Future sampled demand is not available to the policy before ordering.
- Reward: revenue minus purchase cost, holding cost, and unmet-demand penalty. On Sunday, remaining inventory is valued at unit cost.
- Training: 3,000 episodes by default; epsilon-greedy exploration, alpha=0.1, gamma=0.95, training seed=42. Episode count is configurable.
- A terminal update uses reward alone. Nonterminal updates bootstrap from feasible next actions.
- Evaluation freezes Q-values and disables exploration. Compare 200 fresh sampled weeks by default (seed=314159), with identical demand weeks for all policies.
- Baselines: a fixed daily order selected from training mean demand and a reorder-to-target rule. Both obey the same action quantities and capacity.

The app displays learning progress, the actual Q-table, a day-by-day decision log, reward variation, and stock/service outcomes. Reward includes a service penalty, so it differs from inventory-adjusted profit. The undiscounted evaluation reward is reported separately from the discounted training objective.

**The verified 3,000-episode demonstration did not outperform the simple restocking rules.** The app reports measured results honestly. It demonstrates actual learning, not a guaranteed business improvement. Fresh simulated weeks test the assumed environment, not real-world effectiveness.

## Reproduce the supplied results

```powershell
.\.venv\Scripts\python.exe manage.py setup-demo
.\.venv\Scripts\python.exe manage.py train-demo --episodes 3000 --weeks 200
.\.venv\Scripts\python.exe -m pytest -q
```

`setup-demo` seeds only an empty demo database. `train-demo` preserves transactions, trains forecasts for all eligible demo products, fits product groups, and trains the Bottled water restocking agent. On the generated, unmodified seed data it writes measured results to `output/evaluation/` and saved models to `models/demo/`. Seed dates follow the local business date, so later setup dates can produce different numerical results.

If demo history or product economics have been changed, the measured outputs can change. If the named demonstration product has been renamed/archived or its history removed, use the individual training pages instead. Model records include timestamps, signatures, parameters, and cutoffs. Changed input records/settings make corresponding UI results stale until retrained. Only locally produced model files are loaded; uploaded serialized models are not supported.

## Verification

The implementation includes 34 automated checks covering transaction rollback, persistence, duplicate sale protection, monetary/quantity validation, immutable receipt prices, history imports, zero/stockout observations, forecasting leakage, chronological metrics, clustering inputs, inventory conservation, terminal Q-updates, masked actions, deterministic training, frozen evaluation, all six screens, live ML buttons, and a sale through Streamlit controls.

The initial verified run passed all 34 checks. Run the test command above to verify your own installation.

## Code layout

| Path | Purpose |
|---|---|
| `streamlit_app.py` | Application entry point and workspace navigation |
| `core/` | SQLite storage, inventory operations, daily history, demo generation, model artifacts |
| `ml/forecasting.py` | Decision Tree training, evaluation, and next-day inference |
| `ml/clustering.py` | Standardization and K-means product groups |
| `ml/restocking_env.py` | Simulated inventory transitions and rewards |
| `ml/q_learning.py` | Tabular Q-learning training |
| `ml/evaluation.py` | Frozen-policy comparison on identical demand weeks |
| `views/` | The six application screens |
| `tests/` | Core correctness and Streamlit interaction checks |
| `manage.py` | Reproducible demo setup and training commands |

## Limits and data care

This is a classroom, single-user local application, not a production accounting or point-of-sale system. It has no login, tax calculation, refunds, supplier lead times, expiration, payment processing, or automatic purchases. Costs and prices in the demo are illustrative.

Known stockouts are excluded, but unrecorded stockouts can still bias sales forecasts. A short history may not support meaningful clusters. RL results depend on a simplified distribution and reward design. Confirm instructor acceptance of synthetic data before using it as the final academic dataset; CSV import supports suitable observed history.

Back up local SQLite databases before manual file operations. The app does not provide a destructive reset button. Keep real store data out of source control and submission packages.
