"""City Operations Pathway application entry point."""
import argparse
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
import yaml
import pathway as pw

from src.connectors import create_safety_alert_table, create_iot_table, create_traffic_table, create_transit_table, create_environment_table
from src.safety_pipeline import SafetyAnomalyDetector
from src.planning_pipeline import UrbanPlanningEngine
from src.rag_engine import CityRAGEngine
from src.api_server import CityOperationsAPI

PATHWAY_READY = threading.Event()


def load_config(mode: str) -> dict:
    paths = {"public_safety": "config/public_safety.yaml", "urban_planning": "config/urban_planning.yaml", "unified": "config/app.yaml"}
    with open(paths.get(mode, paths["unified"]), encoding="utf-8") as f:
        return yaml.safe_load(f)


def llm_config(config: dict) -> dict:
    return {"model": config.get("$llm_model", "gpt-4o-mini"), "embedding_model": config.get("$embedding_model", "text-embedding-3-small"), "temperature": 0.2, "max_tokens": 1024}


class ProxyHandler(BaseHTTPRequestHandler):
    def _handle(self):
        if self.path == "/healthz":
            body = b'{"status":"ok","pathway_ready":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        internal = os.environ["PATHWAY_INTERNAL_URL"] + self.path
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() not in {"host", "content-length"}}
        try:
            with urlopen(Request(internal, data=data, headers=headers, method=self.command), timeout=120) as response:
                body = response.read()
                self.send_response(response.status)
                for k, v in response.headers.items():
                    if k.lower() not in {"transfer-encoding", "connection", "content-length"}:
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception as exc:
            body = ('{"error":"Pathway backend unavailable","detail":"%s"}' % str(exc).replace('"', "'")).encode()
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    do_GET = _handle
    do_POST = _handle
    do_OPTIONS = _handle
    def log_message(self, format, *args):
        return


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
    insights = planner.compute_traffic_insights(traffic).concat_reindex(
        planner.compute_transit_insights(transit),
        planner.compute_environment_insights(environment),
    )

    rag = CityRAGEngine(cfg)
    vector_server = rag.build_unified_index(alerts, insights)
    answerer = rag.create_rag_answerer(vector_server)

    public_port = int(os.getenv("PORT", "10000"))
    internal_port = public_port + 1
    os.environ["PATHWAY_INTERNAL_URL"] = f"http://127.0.0.1:{internal_port}"
    api = CityOperationsAPI(host="127.0.0.1", port=internal_port)
    api.register_safety_endpoints(anomalies)
    api.register_planning_endpoints(insights)
    api.register_rag_endpoints(answerer)

    def run_pathway():
        try:
            pw.run()
        except Exception as exc:
            print(f"Pathway runtime failed: {exc}", flush=True)

    threading.Thread(target=run_pathway, daemon=True).start()
    print(f"Pathway API internal listener: 127.0.0.1:{internal_port}", flush=True)
    print(f"Public API listener: 0.0.0.0:{public_port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", public_port), ProxyHandler).serve_forever()


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
