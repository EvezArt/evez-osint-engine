#!/usr/bin/env python3
"""
EVEZ OSINT API Server — HTTP endpoint for suspect inference analysis
Runs on port 18791. Exposes the AEMDAS pipeline via REST.
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suspect_matrix import SuspectInferenceEngine, SuspectNode, NetworkEdge, VERSION

PORT = int(os.environ.get('OSINT_PORT', 18791))
DB_PATH = os.environ.get('OSINT_DB', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'osint_usage.db'))

class OSINTHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self._send_json(200, {
                'service': 'EVEZ OSINT API',
                'version': VERSION,
                'author': 'Steven Crawford-Maggard (EVEZ)',
                'endpoints': {
                    'GET /': 'This info',
                    'GET /health': 'Health check',
                    'GET /stats': 'Database statistics',
                    'POST /analyze': 'Run AEMDAS analysis on provided suspects/edges',
                    'POST /analyze/single': 'Quick-analyze a single suspect',
                },
                'eigenvalues': {'Phi': 0.973, 'eta_star': 0.03, 'r': 0.45, 'lambda_dom': -0.333}
            })
        elif parsed.path == '/health':
            self._send_json(200, {'status': 'ok', 'version': VERSION, 'port': PORT})
        elif parsed.path == '/stats':
            engine = SuspectInferenceEngine(db_path=DB_PATH)
            stats = engine.get_db_stats()
            engine.close()
            self._send_json(200, stats)
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/analyze':
            body = self._read_body()
            engine = SuspectInferenceEngine(db_path=DB_PATH)
            for s in body.get('suspects', []):
                engine.add_suspect(SuspectNode(**s))
            for e in body.get('edges', []):
                engine.add_edge(NetworkEdge(**e))
            engine.run_full_analysis()
            assessment = engine.assess_interventions()
            engine.log_to_db()
            engine.close()
            self._send_json(200, assessment)
        elif parsed.path == '/analyze/single':
            body = self._read_body()
            engine = SuspectInferenceEngine(db_path=DB_PATH)
            engine.add_suspect(SuspectNode(
                id=body.get('id', 'suspect'),
                name=body.get('name', 'Unknown'),
                role=body.get('role', 'officer'),
                organization=body.get('organization', 'Unknown'),
                location=body.get('location', ''),
                evidence_refs=body.get('evidence_refs', [])
            ))
            engine.run_full_analysis()
            assessment = engine.assess_interventions()
            engine.log_to_db()
            engine.close()
            self._send_json(200, assessment)
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f'[{self.log_date_time_string()}] {format % args}')

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    server = HTTPServer(('0.0.0.0', PORT), OSINTHandler)
    print(f'EVEZ OSINT API Server v{VERSION}')
    print(f'Listening on port {PORT}')
    print(f'Database: {DB_PATH}')
    print(f'Endpoints: GET / | GET /health | GET /stats | POST /analyze | POST /analyze/single')
    print(f'⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.server_close()

if __name__ == '__main__':
    main()
