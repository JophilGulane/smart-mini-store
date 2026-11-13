"""Reproducible classroom demo setup and measured evaluation exports."""
import argparse
import json
from pathlib import Path
import time
from core.database import ROOT, initialize, today
from core.demo_data import seed_demo
from core.inventory import products
from core.history import history
from core.artifacts import save_run
from ml.forecasting import train_forecast, predict_next
from ml.clustering import cluster_products
from ml.q_learning import train_agent
from ml.restocking_env import Settings
from ml.evaluation import evaluate_agent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup-demo", "train-demo"])
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--weeks", type=int, default=200)
    args = parser.parse_args()
    path = ROOT/"data"/"demo.db"
    initialize(path)
    seeded = seed_demo(path)
    print("Demo database seeded." if seeded else "Existing demo database preserved.", flush=True)
    if args.command == "setup-demo":
        return
    output = ROOT/"output"/"evaluation"
    output.mkdir(parents=True, exist_ok=True)
    items, hist = products(path, True), history(path)
    forecasts = []
    for row in items.itertuples():
        sub = history(path, row.id)
        result = train_forecast(sub)
        save_run(path, "forecast", result, row.id)
        result["predictions"].to_csv(output/f"forecast-{row.id}.csv", index=False)
        forecasts.append({"product_id": row.id, "product": row.name, **result["metrics"], "next_prediction": predict_next(result, sub)["units"]})
    clustered = cluster_products(hist, items)
    save_run(path, "clusters", clustered)
    clustered["assignments"].to_csv(output/"product-groups.csv", index=False)
    selected = items.loc[items.name.eq("Bottled water 500 ml")].iloc[0]
    settings = Settings(selected.cost_centavos/100, selected.price_centavos/100)
    start = time.perf_counter()
    agent = train_agent(history(path, selected.id), settings, args.episodes)
    duration = time.perf_counter()-start
    save_run(path, "q_learning", agent, selected.id)
    evaluated = evaluate_agent(agent, args.weeks)
    agent["curve"].to_csv(output/"training-curve.csv", index=False)
    for key in ("summary", "samples", "log"):
        evaluated[key].to_csv(output/f"restocking-{key}.csv", index=False)
    summary = {"business_date": str(today()), "data_source": "synthetic demonstration data",
               "products": len(items), "observations": len(hist), "forecasts": forecasts,
               "clustering": clustered["metrics"], "rl_product": selected["name"],
               "rl_training": agent["metrics"], "rl_runtime_seconds": duration,
               "rl_evaluation_weeks": args.weeks, "rl_evaluation_seed": evaluated["seed"],
               "rl_comparison": evaluated["summary"].to_dict("records")}
    (output/"results.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"products": len(items), "history_rows": len(hist), "rl_training_seconds": round(duration, 2), "evaluation": evaluated["summary"].to_dict("records")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
