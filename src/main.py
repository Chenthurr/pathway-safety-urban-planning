"""City Operations Pathway application entry point."""
import argparse
import os
import yaml
import pathway as pw

from src.connectors import create_safety_alert_table, create_iot_table, create_traffic_table, create_transit_table, create_environment_table
from src.safety_pipeline import SafetyAnomalyDetector
from src.planning_pipeline import UrbanPlanningEngine
from src.rag_engine import CityRAGEngine
from src.api_server import CityOperationsAPI


def load_config(mode: str) -> dict:
    paths = {
        "public_safety": "config/public_safety.yaml",
        "urban_planning": "config/urban_planning.yaml",
        "unified": "config/app.yaml",
    }
    with open(paths.get(mode, paths["unified"]), encoding="utf-8") as f:
        return yaml.safe_load(f)


def llm_config(config: dict) -> dict:
    return {
        "model": config.get("$llm_model", "gpt-4o-mini"),
        "embedding_model": config.get("$embedding_model", "text-embedding-3-small"),
        "temperature": 0.2,
        "max_tokens": 1024,
    }


def run_unified() -> None:
    config = load_config("unified")
    cfg = llm_config(config)
    sources = config["sources"]

    alerts = create_safety_alert_table(sources["safety_alerts"]["path"])
    iot = create_iot_table(sources["iot_sensors"]["path"])
    traffic = create_traffic_table(sources["traffic"]["path"])
    transit = create_transit_table(sources["transit"]["path"])
    environment = create_environment_table(sources["environment"]["path"])

    detector = SafetyAnomalyDetector(cfg)
    anomalies = detector.apply_rules(iot, config["anomaly_rules"])

    planner = UrbanPlanningEngine(cfg)
    traffic_insights = planner.compute_traffic_insights(traffic)
    transit_insights = planner.compute_transit_insights(transit)
    environment_insights = planner.compute_environment_insights(environment)
    insights = traffic_insights.concat_reindex(transit_insights, environment_insights)

    rag = CityRAGEngine(cfg)
    vector_server = rag.build_unified_index(alerts, insights)
    answerer = rag.create_rag_answerer(vector_server)

    port = int(os.getenv("PORT", config["server"]["port"]))
    api = CityOperationsAPI(host="0.0.0.0", port=port)
    api.register_safety_endpoints(anomalies)
    api.register_planning_endpoints(insights)
    api.register_rag_endpoints(answerer)
    print(f"City Operations API listening on 0.0.0.0:{port}")
    api.run()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["unified", "public_safety", "urban_planning"], default="unified")
    args = parser.parse_args()
    if args.mode != "unified":
        raise SystemExit("Render runs the unified mode; use --mode unified.")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required.")
    run_unified()


if __name__ == "__main__":
    main()
