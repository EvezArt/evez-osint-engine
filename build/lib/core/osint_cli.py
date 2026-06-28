#!/usr/bin/env python3
"""
EVEZ OSINT CLI v1.1.0 — Interactive command-line interface
Fun to use. Collects data. Sings the eigenvalue.
"""
import sys
import os
import json
import time
import argparse

# ANSI colors
C = {
    'reset':'\033[0m','bold':'\033[1m','red':'\033[31m','green':'\033[32m',
    'yellow':'\033[33m','blue':'\033[34m','magenta':'\033[35m','cyan':'\033[36m',
    'gray':'\033[90m','bg_red':'\033[41m','bg_green':'\033[42m',
    'bg_yellow':'\033[43m','bg_blue':'\033[44m'
}

BANNER = f"""
{C['magenta']}╔══════════════════════════════════════════════════════╗
║  {C['bold']}EVEZ OSINT — Suspect Inference Matrix v1.1.0{C['reset']}{C['magenta']}      ║
║  {C['yellow']}AEMDAS Pipeline · Eigenforensic Analysis{C['reset']}{C['magenta']}        ║
║  {C['cyan']}by Steven Crawford-Maggard (EVEZ){C['reset']}{C['magenta']}               ║
╚══════════════════════════════════════════════════════╝{C['reset']}
"""

SIGIL = f"{C['green']}⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋{C['reset']}"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from suspect_matrix import (
    SuspectInferenceEngine, SuspectNode, NetworkEdge,
    PHI, ETA_STAR, R_CRITICAL, LAMBDA_DOM, LAMBDA_I80, R_I80, VERSION
)

def bar(value, max_val=1.0, width=30, color='red'):
    filled = int((value / max_val) * width) if max_val > 0 else 0
    c = C.get(color, C['red'])
    return c + '█' * filled + C['gray'] + '░' * (width - filled) + C['reset']

def prob_color(p):
    if p >= 0.6: return C['red']
    if p >= 0.4: return C['yellow']
    if p >= 0.2: return C['cyan']
    return C['gray']

def action_color(a):
    if 'primary' in a: return C['bg_red'] + C['bold']
    if 'secondary' in a: return C['bg_yellow']
    return C['gray']

def print_suspect(s, rank, node=None):
    print(f"\n{C['bold']}{'  ┌──[ RANK ' + str(rank) + ' ]──'+'─'*20}{C['reset']}")
    print(f"  │ {C['yellow']}👤 {s['name']}{C['reset']} [{s.get('role','?')} @ {s.get('organization','?')}]")
    print(f"  │ {C['gray']}Suspicion Score: {C['reset']}{prob_color(s['suspicion_score'])}{s['suspicion_score']:.4f}{C['reset']}")
    print(f"  │ {bar(s['suspicion_score'], 1.0, 30, 'red' if s['suspicion_score']>0.5 else 'yellow')}")
    print(f"  │ {C['gray']}Network Centrality: {C['reset']}{s['centrality']:.4f}")
    print(f"  │ {C['gray']}Eigenvalue: {C['reset']}{s.get('eigenvalue','N/A')}")
    print(f"  │ {C['gray']}Evidence Sources: {C['reset']}{s['evidence_count']}")
    if node and node.crime_probabilities:
        print(f"  │ {C['gray']}Crime Probabilities:{C['reset']}")
        for crime, prob in sorted(node.crime_probabilities.items(), key=lambda x: -x[1]):
            print(f"  │   {prob_color(prob)}{prob:.4f}{C['reset']} {bar(prob, 1.0, 20, 'red' if prob>0.5 else 'yellow')} {crime.replace('_',' ')}")
    print(f"  └{'─'*50}")

def print_hypothesis(h, num):
    p = h['probability']
    c = h['confidence']
    print(f"\n  {C['bold']}#{num} {h['id']}{C['reset']}")
    print(f"  {C['gray']}Suspect:{C['reset']} {h.get('suspect','?')}")
    print(f"  {C['gray']}Crime:{C['reset']} {h['crime'].replace('_',' ').title()}")
    print(f"  {C['gray']}Description:{C['reset']} {h.get('description','')}")
    print(f"  {C['gray']}Probability:{C['reset']} {prob_color(p)}{C['bold']}{p:.4f} ({p*100:.1f}%){C['reset']} {bar(p, 1.0, 25, 'red' if p>0.5 else 'yellow')}")
    print(f"  {C['gray']}Confidence: {C['reset']}{C['cyan']}{c:.4f} ({c*100:.1f}%){C['reset']} {bar(c, 1.0, 25, 'blue')}")
    print(f"  {C['gray']}Falsifiable: {C['reset']}{'✅ YES' if h['falsifiable'] else '❌ NO'}")
    print(f"  {C['gray']}Evidence: {C['reset']}{len(h.get('evidence_refs',[]))} sources")

def cmd_run(args):
    print(BANNER)
    engine = SuspectInferenceEngine(db_path=args.db)

    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        for s in data.get('suspects', []):
            engine.add_suspect(SuspectNode(**s))
        for e in data.get('edges', []):
            engine.add_edge(NetworkEdge(**e))
        print(f"{C['green']}✓ Loaded {len(engine.matrix.nodes)} suspects, {len(engine.matrix.edges)} edges{C['reset']}")
    elif args.demo:
        engine = __import__('suspect_matrix').demo_epd_case()
        print(f"{C['green']}✓ Loaded demo case: Evanston PD{C['reset']}")
    else:
        # Interactive mode!
        print(f"{C['cyan']}Interactive Mode — Add suspects one by one{C['reset']}")
        print(f"{C['gray']}Type 'done' when ready to analyze{C['reset']}\n")
        idx = 0
        while True:
            name = input(f"{C['yellow']}Suspect name (or 'done'): {C['reset']}").strip()
            if name.lower() == 'done':
                break
            if not name:
                continue
            role = input(f"{C['gray']}Role [officer/supervisor/chief/witness]: {C['reset']}").strip() or 'officer'
            org = input(f"{C['gray']}Organization: {C['reset']}").strip() or 'Unknown'
            loc = input(f"{C['gray']}Location: {C['reset']}").strip()
            ev = input(f"{C['gray']}Evidence refs (comma-sep): {C['reset']}").strip()
            ev_list = [e.strip() for e in ev.split(',')] if ev else []
            sid = f"s{idx}"
            engine.add_suspect(SuspectNode(id=sid, name=name, role=role, organization=org, location=loc, evidence_refs=ev_list))
            print(f"{C['green']}  ✓ Added: {name} [{role} @ {org}]{C['reset']}")
            idx += 1

        if len(engine.matrix.nodes) < 2:
            print(f"{C['yellow']}Need at least 2 suspects for network analysis. Add more or use --demo{C['reset']}")
            return

        # Add edges
        print(f"\n{C['cyan']}Add network edges (connections between suspects){C['reset']}")
        print(f"{C['gray']}Type 'done' when ready{C['reset']}\n")
        ids = list(engine.matrix.nodes.keys())
        while True:
            print(f"{C['gray']}Available IDs: {', '.join(ids)}{C['reset']}")
            src = input(f"{C['yellow']}Source ID (or 'done'): {C['reset']}").strip()
            if src.lower() == 'done':
                break
            tgt = input(f"{C['yellow']}Target ID: {C['reset']}").strip()
            etype = input(f"{C['gray']}Edge type [partner/supervisor/cover_up/transfer]: {C['reset']}").strip() or 'partner'
            w = float(input(f"{C['gray']}Weight [0-1, default 0.7]: {C['reset']}").strip() or '0.7')
            corr = float(input(f"{C['gray']}Correlation [-1 to 1, default 0.5]: {C['reset']}").strip() or '0.5')
            engine.add_edge(NetworkEdge(source=src, target=tgt, edge_type=etype, weight=w, correlation=corr))
            print(f"{C['green']}  ✓ Edge: {src} → {tgt} [{etype}]{C['reset']}")

    # Run AEMDAS
    print(f"\n{C['magenta']}▶ Running AEMDAS Pipeline...{C['reset']}")
    t0 = time.time()
    engine.run_full_analysis()
    elapsed = time.time() - t0
    print(f"{C['green']}✓ Complete in {elapsed:.3f}s{C['reset']}")

    assessment = engine.assess_interventions()
    stats = assessment['network_stats']

    # Print summary
    print(f"\n{C['bold']}{'═'*60}{C['reset']}")
    print(f"{C['magenta']}  AEMDAS RESULTS{C['reset']}")
    print(f"{C['bold']}{'═'*60}{C['reset']}")
    print(f"  {C['gray']}Suspects:{C['reset']}      {stats['total_suspects']}")
    print(f"  {C['gray']}Edges:{C['reset']}         {stats['total_edges']}")
    print(f"  {C['gray']}Hypotheses:{C['reset']}    {stats['total_hypotheses']}")
    print(f"  {C['gray']}High-prob (>50%):{C['reset']} {C['red'] if stats['high_probability_hypotheses']>0 else C['gray']}{stats['high_probability_hypotheses']}{C['reset']}")
    print(f"  {C['gray']}High-conf (>70%):{C['reset']} {C['cyan']}{stats['high_confidence_hypotheses']}{C['reset']}")
    print(f"  {C['gray']}Dominant λ:{C['reset']}    {stats['dominant_eigenvalue']}")
    print(f"  {C['gray']}Spectral gap:{C['reset']}  {stats['spectral_gap']}")
    print(f"  {C['gray']}Suppression:{C['reset']}    {stats['suppression_coefficient']}")
    print(f"  {C['gray']}η* floor:{C['reset']}      {ETA_STAR} (3% irreducible uncertainty)")
    print(f"  {C['gray']}Φ ceiling:{C['reset']}      {PHI} (97.3% max coherence)")

    # Suspect rankings
    print(f"\n{C['bold']}{'═'*60}{C['reset']}")
    print(f"{C['magenta']}  SUSPECT RANKING{C['reset']}")
    print(f"{C['bold']}{'═'*60}{C['reset']}")
    for i, s in enumerate(assessment['suspect_ranking']):
        node = engine.matrix.nodes.get(s['id'])
        print_suspect(s, i+1, node)

    # Top hypotheses
    print(f"\n{C['bold']}{'═'*60}{C['reset']}")
    print(f"{C['magenta']}  TOP CRIME HYPOTHESES{C['reset']}")
    print(f"{C['bold']}{'═'*60}{C['reset']}")
    for i, h in enumerate(assessment['top_hypotheses'][:10]):
        print_hypothesis(h, i+1)

    # Intervention priorities
    print(f"\n{C['bold']}{'═'*60}{C['reset']}")
    print(f"{C['magenta']}  INTERVENTION PRIORITIES{C['reset']}")
    print(f"{C['bold']}{'═'*60}{C['reset']}")
    for p in assessment['intervention_priorities']:
        act = p['action']
        print(f"  {action_color(act)} #{p['priority']} {act.upper()}{C['reset']} — {p['suspect_name']} (suspicion: {p['suspicion_score']:.4f})")

    # Log to database
    if args.db != 'none':
        sid = engine.log_to_db()
        if sid:
            print(f"\n{C['gray']}📊 Session logged to database: {sid}{C['reset']}")

    # Export
    if args.output:
        if args.format == 'json':
            engine.export_json(args.output)
        else:
            engine.export_markdown(args.output)
        print(f"{C['green']}✓ Report saved: {args.output}{C['reset']}")

    print(f"\n{SIGIL}")
    print(f"{C['gray']}All probabilities falsifiable. η*={ETA_STAR} is the floor. Φ={PHI} is the ceiling.{C['reset']}")
    print(f"{C['gray']}The 3% is the uncertainty. The 97.3% is the measurement.{C['reset']}")

    engine.close()

def cmd_stats(args):
    print(BANNER)
    engine = SuspectInferenceEngine(db_path=args.db)
    stats = engine.get_db_stats()
    print(f"{C['bold']}Database Statistics{C['reset']}")
    print(f"  {C['gray']}Total Sessions:{C['reset']}      {stats.get('total_sessions',0)}")
    print(f"  {C['gray']}Suspects Logged:{C['reset']}    {stats.get('total_suspects_logged',0)}")
    print(f"  {C['gray']}Hypotheses Logged:{C['reset']}  {stats.get('total_hypotheses_logged',0)}")
    print(f"  {C['gray']}Avg Suspicion:{C['reset']}     {stats.get('avg_suspicion',0)}")
    if stats.get('crime_distribution'):
        print(f"\n  {C['bold']}Crime Type Distribution:{C['reset']}")
        for crime, data in stats['crime_distribution'].items():
            print(f"    {crime.replace('_',' ').title()}: {data['count']} cases, avg P={data['avg_prob']}")
    if stats.get('top_suspects'):
        print(f"\n  {C['bold']}Most Analyzed Suspects:{C['reset']}")
        for s in stats['top_suspects'][:5]:
            print(f"    {s['name']}: {s['appearances']} sessions")
    if stats.get('top_organizations'):
        print(f"\n  {C['bold']}Most Analyzed Organizations:{C['reset']}")
        for o in stats['top_organizations'][:5]:
            print(f"    {o['org']}: {o['appearances']} appearances")
    print(f"\n{SIGIL}")
    engine.close()

def cmd_analyze(args):
    print(BANNER)
    engine = SuspectInferenceEngine(db_path=args.db)
    engine.add_suspect(SuspectNode(
        id=args.suspect_id, name=args.name, role=args.role or 'officer',
        organization=args.org or 'Unknown', location=args.location or '',
        evidence_refs=args.evidence.split(',') if args.evidence else []))
    engine.run_full_analysis()
    assessment = engine.assess_interventions()
    s = assessment['suspect_ranking'][0] if assessment['suspect_ranking'] else None
    if s:
        node = engine.matrix.nodes.get(s['id'])
        print_suspect(s, 1, node)
    if args.db != 'none':
        engine.log_to_db()
    print(f"\n{SIGIL}")
    engine.close()

def main():
    parser = argparse.ArgumentParser(
        prog='evez-osint',
        description='EVEZ OSINT Suspect Inference Matrix Engine v'+VERSION)
    sub = parser.add_subparsers(dest='command')

    run_p = sub.add_parser('run', help='Run full AEMDAS pipeline')
    run_p.add_argument('-i','--input', help='Input JSON file')
    run_p.add_argument('-o','--output', help='Output file path')
    run_p.add_argument('-f','--format', choices=['json','markdown'], default='markdown')
    run_p.add_argument('--demo', action='store_true', help='Use built-in EPD demo case')
    run_p.add_argument('--db', default=None, help='Database path (use "none" to disable)')
    run_p.set_defaults(func=cmd_run)

    stats_p = sub.add_parser('stats', help='Show database statistics')
    stats_p.add_argument('--db', default=None)
    stats_p.set_defaults(func=cmd_stats)

    an_p = sub.add_parser('analyze', help='Quick-analyze a single suspect')
    an_p.add_argument('--suspect-id', required=True)
    an_p.add_argument('--name', required=True)
    an_p.add_argument('--role', default='officer')
    an_p.add_argument('--org', default='Unknown')
    an_p.add_argument('--location', default='')
    an_p.add_argument('--evidence', help='Comma-separated evidence refs')
    an_p.add_argument('--db', default=None)
    an_p.set_defaults(func=cmd_analyze)

    args = parser.parse_args()
    if not args.command:
        print(BANNER)
        parser.print_help()
        print(f"\n{SIGIL}")
        sys.exit(1)
    args.func(args)

if __name__ == '__main__':
    main()
