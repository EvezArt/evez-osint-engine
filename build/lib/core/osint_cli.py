#!/usr/bin/env python3
"""EVEZ OSINT CLI -- command-line interface for suspect inference matrix engine"""
import sys
import os
import argparse
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suspect_matrix import (
    SuspectInferenceEngine, SuspectNode, NetworkEdge,
    PHI, ETA_STAR, R_CRITICAL, LAMBDA_DOM
)

def cmd_run(args):
    engine = SuspectInferenceEngine()
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        for s in data.get('suspects', []):
            engine.add_suspect(SuspectNode(**s))
        for e in data.get('edges', []):
            engine.add_edge(NetworkEdge(**e))
    else:
        engine = __import__('suspect_matrix').demo_epd_case()
    engine.build_adjacency()
    engine.compute_eigenvalues()
    engine.infer_hypotheses()
    if args.format == 'json':
        print(engine.export_json(args.output))
    else:
        print(engine.export_markdown(args.output))

def cmd_analyze(args):
    engine = SuspectInferenceEngine()
    engine.add_suspect(SuspectNode(
        id=args.suspect_id, name=args.name, role=args.role or 'officer',
        organization=args.org or 'Unknown', location=args.location or '',
        evidence_refs=args.evidence.split(',') if args.evidence else []))
    engine.build_adjacency()
    engine.compute_eigenvalues()
    engine.infer_hypotheses()
    assessment = engine.assess_interventions()
    print(f"Suspect: {args.name}")
    print(f"Suspicion Score: {assessment['suspect_ranking'][0]['suspicion_score']:.4f}")
    print(f"Crimes:")
    for h in assessment['top_hypotheses'][:5]:
        print(f"  {h['crime']}: P={h['probability']:.4f} C={h['confidence']:.4f}")

def main():
    parser = argparse.ArgumentParser(
        prog='evez-osint',
        description='EVEZ OSINT Suspect Inference Matrix Engine v1.0.0')
    sub = parser.add_subparsers(dest='command')
    run_p = sub.add_parser('run', help='Run full AEMDAS pipeline on input data')
    run_p.add_argument('-i','--input', help='Input JSON file with suspects/edges')
    run_p.add_argument('-o','--output', help='Output file path')
    run_p.add_argument('-f','--format', choices=['json','markdown'], default='markdown')
    run_p.set_defaults(func=cmd_run)
    an_p = sub.add_parser('analyze', help='Quick-analyze a single suspect')
    an_p.add_argument('--suspect-id', required=True)
    an_p.add_argument('--name', required=True)
    an_p.add_argument('--role', default='officer')
    an_p.add_argument('--org', default='Unknown')
    an_p.add_argument('--location', default='')
    an_p.add_argument('--evidence', help='Comma-separated evidence refs')
    an_p.set_defaults(func=cmd_analyze)
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)

if __name__ == '__main__':
    main()
