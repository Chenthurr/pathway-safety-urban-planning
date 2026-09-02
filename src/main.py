"""
City Operations with Pathway AI
Entry point for the Public Safety & Urban Planning system.

Run with:
    python src/main.py --mode public_safety
    python src/main.py --mode urban_planning
    python src/main.py --mode unified

Uses Pathway LLM App patterns:
- VectorStoreServer for live document indexing
- BaseRAGQuestionAnswerer for RAG Q&A
- pw.io.http.rest_connector for REST endpoints
"""
import argparse
import yaml
import os
import pathway as pw

from src.connectors import (
    create_safety_alert_table, create_iot_table,
    create_traffic_table, create_transit_table, create_environment_table
)
from src.safety_pipeline import SafetyAnomalyDetector
from src.planning_pipeline import UrbanPlanningEngine
from src.rag_engine import CityRAGEngine
from src.api_server import CityOperationsAPI


def load_config(mode: str) -> dict:
    """Load YAML configuration."""
    config_files = {
        "public_safety": "config/public_safety.yaml",
        "urban_planning": "config/urban_planning.yaml",
        "unified": "config/app.yaml"
    }
    config_path = config_files.get(mode, "config/app.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_llm_config(config: dict) -> dict:
    """Extract LLM config from YAML."""
    return {
        "model": config.get("$llm_model", "gpt-4o-mini"),
        "embedding_model": config.get("$embedding_model", "text-embedding-3-small"),
        "temperature": 0.2,
        "max_tokens": 1024
    }


def run_public_safety():
    """Run the public safety anomaly detection pipeline."""
    print("🚨 Starting Public Safety System...")
    config = load_config("public_safety")
    llm_config = get_llm_config(config)

    sources = config["sources"]

    # Ingest live data
    alerts = create_safety_alert_table(sources["safety_alerts"]["path"])
    iot = create_iot_table(sources["iot_sensors"]["path"])

    # Build anomaly detector
    detector = SafetyAnomalyDetector(llm_config)

    # Rule-based anomalies
    rule_anomalies = detector.apply_rules(iot, config["anomaly_rules"])

    # Build live RAG index over alerts
    vector_server = detector.build_vector_store(alerts)

    # Create RAG answerer
    rag_answerer = detector.create_rag_answerer(vector_server)

    # Serve API
    server_config = config["server"]
    api = CityOperationsAPI(
        host=server_config["host"],
        port=int(os.getenv("PORT", server_config["port"]))
    )
    api.register_safety_endpoints(rule_anomalies)
    api.register_rag_endpoints(rag_answerer, vector_server)

    print(f"✅ Public Safety API running at http://{server_config['host']}:{server_config['port']}")
    print("   Endpoints:")
    print("     POST /safety/anomalies")
    print("     POST /v2/answer")
    print("     POST /v1/retrieve")
    print("     GET  /v1/statistics")
    print("     GET  /_schema")
    api.run()


def run_urban_planning():
    """Run the urban planning insights pipeline."""
    print("🏙️ Starting Urban Planning System...")
    config = load_config("urban_planning")
    llm_config = get_llm_config(config)

    sources = config["sources"]

    # Ingest live data
    traffic = create_traffic_table(sources["traffic"]["path"])
    transit = create_transit_table(sources["transit"]["path"])
    env = create_environment_table(sources["environment"]["path"])

    # Build planning engine
    engine = UrbanPlanningEngine(llm_config)

    # Compute real-time insights
    traffic_insights = engine.compute_traffic_insights(traffic)
    transit_insights = engine.compute_transit_insights(transit)
    env_insights = engine.compute_environment_insights(env)

    # Generate LLM summary
    summary = engine.generate_llm_summary(traffic_insights, transit_insights, env_insights)

    # Combine all insights
    all_insights = traffic_insights.concat(
        transit_insights
    ).concat(
        env_insights
    ).concat(summary)

    # Serve API
    server_config = config["server"]
    api = CityOperationsAPI(
        host=server_config["host"],
        port=server_config["port"]
    )
    api.register_planning_endpoints(all_insights)

    print(f"✅ Urban Planning API running at http://{server_config['host']}:{server_config['port']}")
    print("   Endpoints:")
    print("     POST /planning/insights")
    print("     GET  /planning/status")
    print("     GET  /_schema")
    api.run()


def run_unified():
    """Run both systems with a unified RAG engine."""
    print("🌐 Starting Unified City Operations System...")
    config = load_config("unified")
    llm_config = get_llm_config(config)

    sources = config["sources"]

    # --- Safety Pipeline ---
    alerts = create_safety_alert_table(sources["safety_alerts"]["path"])
    iot = create_iot_table(sources["iot_sensors"]["path"])

    detector = SafetyAnomalyDetector(llm_config)
    rule_anomalies = detector.apply_rules(iot, config["anomaly_rules"])

    # --- Planning Pipeline ---
    traffic = create_traffic_table(sources["traffic"]["path"])
    transit = create_transit_table(sources["transit"]["path"])
    env = create_environment_table(sources["environment"]["path"])

    engine = UrbanPlanningEngine(llm_config)
    traffic_insights = engine.compute_traffic_insights(traffic)
    transit_insights = engine.compute_transit_insights(transit)
    env_insights = engine.compute_environment_insights(env)

    all_insights = traffic_insights.concat(transit_insights).concat(env_insights)

    # --- Unified RAG ---
    rag_engine = CityRAGEngine(llm_config)
    vector_server = rag_engine.build_unified_index(alerts, all_insights)
    rag_answerer = rag_engine.create_rag_answerer(vector_server)

    # --- Unified API ---
    server_config = config["server"]
    api = CityOperationsAPI(
        host=server_config["host"],
        port=server_config["port"]
    )
    api.register_safety_endpoints(rule_anomalies)
    api.register_planning_endpoints(all_insights)
    api.register_rag_endpoints(rag_answerer, vector_server)

    print("✅ Unified API running")
    print(f"   URL: http://{server_config['host']}:{server_config['port']}")
    print("   Endpoints:")
    print("     POST /safety/anomalies")
    print("     POST /planning/insights")
    print("     GET  /planning/status")
    print("     POST /v2/answer")
    print("     POST /v1/retrieve")
    print("     GET  /v1/statistics")
    print("     GET  /_schema")
    api.run()


def main():
    parser = argparse.ArgumentParser(
        description="City Operations with Pathway AI - LLM App Edition"
    )
    parser.add_argument(
        "--mode",
        choices=["public_safety", "urban_planning", "unified"],
        default="unified",
        help="System mode to run"
    )
    args = parser.parse_args()

    # Set OpenAI API key from environment
    if "OPENAI_API_KEY" not in os.environ:
        print("⚠️  Warning: OPENAI_API_KEY not set. Set it with:")
        print("   export OPENAI_API_KEY=sk-your-key-here")

    if args.mode == "public_safety":
        run_public_safety()
    elif args.mode == "urban_planning":
        run_urban_planning()
    else:
        run_unified()


if __name__ == "__main__":
    main()
