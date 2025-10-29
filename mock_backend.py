#!/usr/bin/env python3
"""
Simple mock backend for testing frontend integration
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        path = urlparse(self.path).path
        
        if path == '/api/v1/domains':
            response = {
                "domains": [
                    {
                        "name": "finance",
                        "total_dags": 25,
                        "health_score": 85.5,
                        "status_distribution": {
                            "success": 20,
                            "failed": 3,
                            "running": 1,
                            "queued": 1
                        }
                    },
                    {
                        "name": "ecosystem", 
                        "total_dags": 15,
                        "health_score": 75.2,
                        "status_distribution": {
                            "success": 10,
                            "failed": 4,
                            "running": 1,
                            "queued": 0
                        }
                    }
                ]
            }
        elif path == '/api/v1/analysis/failures':
            response = {
                "dag_health_summary": {
                    "total_dags": 294,
                    "domains": 8,
                    "health_metrics": {
                        "average_health_score": 82.3,
                        "total_runs": 1247,
                        "failed_runs": 43,
                        "success_rate": 96.6
                    }
                },
                "analysis": {
                    "summary": "System is performing well with 96.6% success rate. Recent failures are primarily in ecosystem and finance domains due to data availability issues.",
                    "patterns": [
                        "Data source connectivity issues in ecosystem domain",
                        "DBT test failures in finance domain", 
                        "File transfer timeouts during peak hours"
                    ],
                    "action_items": [
                        "Investigate data source connections for ecosystem DAGs",
                        "Review DBT test configurations for finance workflows",
                        "Consider increasing timeout values for file transfers"
                    ]
                },
                "failed_dags": [
                    {
                        "dag_id": "finance_erp__invest_extraction",
                        "domain_tag": "finance",
                        "failure_count": 3,
                        "last_failure": "2025-10-29T15:30:00Z"
                    }
                ],
                "logs": [
                    {
                        "dag_id": "finance_erp__invest_extraction", 
                        "task_id": "dbt_pre_invest_run_test",
                        "execution_date": "2025-10-29T15:30:00Z",
                        "log_content": "ERROR: Database connection timeout during test execution"
                    }
                ]
            }
        else:
            response = {"error": "Not found"}
            
        self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), MockHandler)
    print("Mock backend running on http://localhost:8000")
    print("Try: http://localhost:8000/api/v1/domains")
    print("Try: http://localhost:8000/api/v1/analysis/failures")
    server.serve_forever()