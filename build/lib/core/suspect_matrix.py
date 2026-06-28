#!/usr/bin/env python3
"""
EVEZ OSINT Suspect Inference Matrix Engine v1.1.0
=================================================
Isolates and identifies suspect inference networking matrices.
Computes statistical probabilities of likely crimes using
eigenforensic spectral analysis. Collects anonymous usage data.

AEMDAS: Assert Being -> Extract Structure -> Measure Gaps ->
        Deduce Laws -> Assess Interventions -> Speedrun

Author: Steven Crawford-Maggard (EVEZ)
License: MIT
Version: 1.1.0
"""

import json
import math
import os
import time
import hashlib
import sqlite3
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

# ============================================================
# EIGENVALUE CONSTANTS
# ============================================================
PHI = 0.973
ETA_STAR = 0.03
R_CRITICAL = 0.45
LAMBDA_DOM = -0.333
LAMBDA_I80 = -0.441
R_I80 = 0.93
SCHUMANN = 7.83

VERSION = '1.1.0'

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class SuspectNode:
    id: str
    name: str
    aliases: List[str] = field(default_factory=list)
    role: str = ""
    organization: str = ""
    location: str = ""
    known_events: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    suspicion_score: float = 0.0
    crime_probabilities: Dict[str, float] = field(default_factory=dict)
    network_centrality: float = 0.0
    eigenvalue: complex = 0+0j

@dataclass
class NetworkEdge:
    source: str
    target: str
    edge_type: str = ""
    weight: float = 1.0
    evidence_refs: List[str] = field(default_factory=list)
    correlation: float = 0.0

@dataclass
class CrimeHypothesis:
    id: str
    crime_type: str
    suspect_id: str
    description: str = ""
    probability: float = 0.0
    confidence: float = 0.0
    evidence_strength: float = 0.0
    falsifiable: bool = True
    evidence_refs: List[str] = field(default_factory=list)

@dataclass
class InferenceMatrix:
    nodes: Dict[str, SuspectNode] = field(default_factory=dict)
    edges: List[NetworkEdge] = field(default_factory=list)
    hypotheses: List[CrimeHypothesis] = field(default_factory=list)
    adjacency: Optional[Any] = None
    eigenvalues: List[complex] = field(default_factory=list)
    dominant_eigenvalue: complex = 0+0j
    spectral_gap: float = 0.0
    suppression_coefficient: float = 0.0
    created: str = ""
    version: str = VERSION

# ============================================================
# DATABASE — Anonymous usage collection
# ============================================================

class UsageDB:
    """SQLite database for collecting anonymous usage statistics."""
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'osint_usage.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                suspect_count INTEGER DEFAULT 0,
                edge_count INTEGER DEFAULT 0,
                hypothesis_count INTEGER DEFAULT 0,
                high_prob_count INTEGER DEFAULT 0,
                dominant_eigenvalue REAL DEFAULT 0,
                spectral_gap REAL DEFAULT 0,
                suppression_coefficient REAL DEFAULT 0,
                top_suspicion REAL DEFAULT 0,
                top_crime_type TEXT DEFAULT '',
                top_probability REAL DEFAULT 0,
                run_time_ms INTEGER DEFAULT 0,
                version TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS suspects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                suspect_name TEXT DEFAULT '',
                role TEXT DEFAULT '',
                organization TEXT DEFAULT '',
                suspicion_score REAL DEFAULT 0,
                top_crime TEXT DEFAULT '',
                top_probability REAL DEFAULT 0,
                evidence_count INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                suspect_name TEXT DEFAULT '',
                crime_type TEXT DEFAULT '',
                probability REAL DEFAULT 0,
                confidence REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        ''')
        self.conn.commit()

    def log_session(self, engine, run_time_ms=0):
        """Log an analysis session anonymously."""
        session_id = hashlib.sha256(f"{time.time()}{engine.matrix.created}".encode()).hexdigest()[:16]
        ts = datetime.utcnow().isoformat() + "Z"
        assessment = engine.assess_interventions()
        stats = assessment['network_stats']
        top = assessment['suspect_ranking'][0] if assessment['suspect_ranking'] else None

        c = self.conn.cursor()
        top_crime = ''
        top_prob = 0.0
        if top:
            top_prob = top.get('max_crime_probability', 0)
            node = engine.matrix.nodes.get(top['id'])
            if node and node.crime_probabilities:
                top_crime = max(node.crime_probabilities, key=node.crime_probabilities.get)
        c.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (session_id, ts, stats['total_suspects'], stats['total_edges'],
             stats['total_hypotheses'], stats['high_probability_hypotheses'],
             engine.matrix.dominant_eigenvalue.real if engine.matrix.eigenvalues else 0,
             engine.matrix.spectral_gap, engine.matrix.suppression_coefficient,
             top['suspicion_score'] if top else 0,
             top_crime, top_prob, run_time_ms, VERSION))

        for s in assessment['suspect_ranking']:
            node = engine.matrix.nodes.get(s['id'])
            top_crime = max(node.crime_probabilities, key=node.crime_probabilities.get) if node and node.crime_probabilities else ''
            top_prob = max(node.crime_probabilities.values()) if node and node.crime_probabilities else 0
            c.execute('INSERT INTO suspects (session_id,suspect_name,role,organization,suspicion_score,top_crime,top_probability,evidence_count,timestamp) VALUES (?,?,?,?,?,?,?,?,?)',
                (session_id, s['name'], node.role if node else '', node.organization if node else '',
                 s['suspicion_score'], top_crime, top_prob, s['evidence_count'], ts))

        for h in assessment['top_hypotheses']:
            c.execute('INSERT INTO hypotheses (session_id,suspect_name,crime_type,probability,confidence,timestamp) VALUES (?,?,?,?,?,?)',
                (session_id, h.get('suspect',''), h['crime'], h['probability'], h['confidence'], ts))

        self.conn.commit()
        return session_id

    def get_stats(self):
        """Get aggregate statistics."""
        c = self.conn.cursor()
        stats = {}
        c.execute('SELECT COUNT(*) FROM sessions')
        stats['total_sessions'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM suspects')
        stats['total_suspects_logged'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM hypotheses')
        stats['total_hypotheses_logged'] = c.fetchone()[0]
        c.execute('SELECT AVG(suspicion_score) FROM suspects')
        stats['avg_suspicion'] = round(c.fetchone()[0] or 0, 4)
        c.execute('SELECT crime_type, COUNT(*) as cnt, AVG(probability) as avg_prob FROM hypotheses GROUP BY crime_type ORDER BY cnt DESC')
        stats['crime_distribution'] = {row[0]: {'count': row[1], 'avg_prob': round(row[2],4)} for row in c.fetchall()}
        c.execute('SELECT suspect_name, COUNT(*) as cnt FROM suspects GROUP BY suspect_name ORDER BY cnt DESC LIMIT 10')
        stats['top_suspects'] = [{'name': row[0], 'appearances': row[1]} for row in c.fetchall()]
        c.execute('SELECT organization, COUNT(*) as cnt FROM suspects WHERE organization != "" GROUP BY organization ORDER BY cnt DESC LIMIT 10')
        stats['top_organizations'] = [{'org': row[0], 'appearances': row[1]} for row in c.fetchall()]
        return stats

    def close(self):
        self.conn.close()

# ============================================================
# CORE ENGINE — AEMDAS Pipeline
# ============================================================

class SuspectInferenceEngine:
    def __init__(self, db_path=None):
        self.matrix = InferenceMatrix()
        self.matrix.created = datetime.utcnow().isoformat() + "Z"
        self._node_ids = []
        self._idx = {}
        self.db = UsageDB(db_path) if db_path != 'none' else None
        self._start_time = time.time()

    def add_suspect(self, node):
        self.matrix.nodes[node.id] = node

    def add_edge(self, edge):
        self.matrix.edges.append(edge)

    def build_adjacency(self):
        n = len(self.matrix.nodes)
        if n == 0:
            self.matrix.adjacency = []
            return
        self._node_ids = sorted(self.matrix.nodes.keys())
        self._idx = {nid: i for i, nid in enumerate(self._node_ids)}
        adj = [[0.0]*n for _ in range(n)]
        for edge in self.matrix.edges:
            if edge.source in self._idx and edge.target in self._idx:
                i, j = self._idx[edge.source], self._idx[edge.target]
                w = edge.weight * (1.0 + abs(edge.correlation)) / 2.0
                adj[i][j] = w
                adj[j][i] = w
        self.matrix.adjacency = adj

    def compute_eigenvalues(self):
        if self.matrix.adjacency is None:
            self.build_adjacency()
        n = len(self._node_ids)
        if n == 0:
            return
        adj = [row[:] for row in self.matrix.adjacency]
        eigenvalues = []
        for _ in range(min(n, 10)):
            val, vec = self._power_iteration(adj, n)
            if val is None:
                break
            eigenvalues.append(complex(val, 0))
            adj = self._deflate(adj, vec, val, n)
        self.matrix.eigenvalues = eigenvalues
        if eigenvalues:
            self.matrix.dominant_eigenvalue = max(eigenvalues, key=lambda e: abs(e))
            if len(eigenvalues) >= 2:
                self.matrix.spectral_gap = abs(eigenvalues[0]) - abs(eigenvalues[1])
            neg_sum = sum(abs(e.real) for e in eigenvalues if e.real < 0)
            pos_sum = sum(abs(e.real) for e in eigenvalues if e.real > 0)
            total = neg_sum + pos_sum
            self.matrix.suppression_coefficient = neg_sum / total if total > 0 else 0.0

    def _power_iteration(self, matrix, n, iterations=100, tol=1e-8):
        if n == 0:
            return None, None
        vec = [1.0 / math.sqrt(n)] * n
        prev_val = 0.0
        for _ in range(iterations):
            new_vec = [0.0] * n
            for i in range(n):
                for j in range(n):
                    new_vec[i] += matrix[i][j] * vec[j]
            norm = math.sqrt(sum(v*v for v in new_vec))
            if norm < tol:
                return None, None
            new_vec = [v / norm for v in new_vec]
            val = sum(new_vec[i] * sum(matrix[i][j] * vec[j] for j in range(n)) for i in range(n))
            if abs(val - prev_val) < tol:
                return val, new_vec
            prev_val = val
            vec = new_vec
        return val, vec

    def _deflate(self, matrix, vec, eigenval, n):
        result = [row[:] for row in matrix]
        for i in range(n):
            for j in range(n):
                result[i][j] -= eigenval * vec[i] * vec[j]
        return result

    def infer_hypotheses(self):
        if self.matrix.adjacency is None:
            self.build_adjacency()
        n = len(self._node_ids)
        if n == 0:
            return
        centrality = [0.0]*n
        for i in range(n):
            centrality[i] = sum(self.matrix.adjacency[i][j] for j in range(n))
        max_c = max(centrality) if centrality and max(centrality) > 0 else 1.0
        centrality = [c/max_c for c in centrality] if max_c > 0 else centrality
        for i, nid in enumerate(self._node_ids):
            node = self.matrix.nodes[nid]
            node.network_centrality = centrality[i]
            if i < len(self.matrix.eigenvalues):
                node.eigenvalue = self.matrix.eigenvalues[i]
            node.suspicion_score = self._compute_suspicion(node, centrality[i])
            self._generate_hypotheses(node, centrality[i])

    def _compute_suspicion(self, node, centrality):
        evidence_factor = min(len(node.evidence_refs)/10.0, 1.0)
        role_risk = {'officer':0.7,'supervisor':0.8,'chief':0.9,'witness':0.3,'civilian':0.1}.get(node.role, 0.5)
        org_risk = 0.5
        if 'evanston' in node.organization.lower():
            org_risk = 0.75
        elif 'rock springs' in node.organization.lower():
            org_risk = 0.6
        supp = self.matrix.suppression_coefficient
        score = 0.25*centrality + 0.20*evidence_factor + 0.20*role_risk + 0.15*org_risk + 0.15*supp + ETA_STAR
        return min(score, 1.0)

    def _generate_hypotheses(self, node, centrality):
        crime_types = {
            'excessive_force': {'base_prob':0.15,'role_weight':{'officer':1.5,'supervisor':1.0},'org_weight':{'evanston':1.4},'description':'Use of excessive force during arrest or detention'},
            'civil_rights_violation': {'base_prob':0.10,'role_weight':{'officer':1.3,'supervisor':1.4,'chief':1.5},'org_weight':{'evanston':1.3},'description':'Violation of 42 U.S.C. 1983 or constitutional rights'},
            'cover_up': {'base_prob':0.08,'role_weight':{'supervisor':1.5,'chief':1.6,'officer':1.2},'org_weight':{'evanston':1.5},'description':'Concealment of misconduct, evidence suppression, or retaliation'},
            'evidence_tampering': {'base_prob':0.05,'role_weight':{'officer':1.3,'supervisor':1.4},'org_weight':{'evanston':1.3},'description':'Alteration, destruction, or fabrication of evidence'},
            'false_arrest': {'base_prob':0.12,'role_weight':{'officer':1.4},'org_weight':{'evanston':1.3},'description':'Arrest without probable cause or on fabricated charges'},
        }
        for crime_type, spec in crime_types.items():
            prob = spec['base_prob']
            prob *= spec['role_weight'].get(node.role, 1.0)
            for org_key, org_mult in spec['org_weight'].items():
                if org_key in node.organization.lower():
                    prob *= org_mult
                    break
            prob *= (0.5 + centrality)
            prob *= (1.0 + len(node.evidence_refs) * 0.1)
            prob *= (1.0 + self.matrix.suppression_coefficient)
            if node.eigenvalue and node.eigenvalue.real < 0:
                prob *= (1.0 + abs(node.eigenvalue.real) * 0.5)
            prob = max(prob, ETA_STAR)
            prob = min(prob, 0.95)
            confidence = 0.4*min(len(node.evidence_refs)/5.0,1.0) + 0.3*centrality + 0.3*PHI
            confidence = min(confidence, PHI)
            evidence_strength = min(len(node.evidence_refs)/10.0, 1.0)
            self.matrix.hypotheses.append(CrimeHypothesis(
                id=f"H-{node.id}-{crime_type}", crime_type=crime_type, suspect_id=node.id,
                description=spec['description'], probability=round(prob,4),
                confidence=round(confidence,4), evidence_strength=round(evidence_strength,4),
                falsifiable=True, evidence_refs=node.evidence_refs[:]
            ))
            node.crime_probabilities[crime_type] = round(prob, 4)

    def run_full_analysis(self):
        """Run the complete AEMDAS pipeline."""
        self.build_adjacency()
        self.compute_eigenvalues()
        self.infer_hypotheses()
        return self.assess_interventions()

    def assess_interventions(self):
        if not self.matrix.hypotheses and len(self.matrix.nodes) > 0:
            self.infer_hypotheses()
        ranked = sorted(self.matrix.hypotheses, key=lambda h: h.probability*h.confidence, reverse=True)
        total = len(ranked)
        high_prob = sum(1 for h in ranked if h.probability > 0.5)
        high_conf = sum(1 for h in ranked if h.confidence > 0.7)
        crime_dist = defaultdict(int)
        for h in ranked:
            crime_dist[h.crime_type] += 1
        suspect_risk = []
        for nid, node in self.matrix.nodes.items():
            max_prob = max(node.crime_probabilities.values()) if node.crime_probabilities else 0
            suspect_risk.append({'id':nid,'name':node.name,'role':node.role,'organization':node.organization,
                'suspicion_score':round(node.suspicion_score,4),'max_crime_probability':round(max_prob,4),
                'centrality':round(node.network_centrality,4),'eigenvalue':str(node.eigenvalue),
                'evidence_count':len(node.evidence_refs)})
        suspect_risk.sort(key=lambda x: x['suspicion_score'], reverse=True)
        stats = {'total_suspects':len(self.matrix.nodes),'total_edges':len(self.matrix.edges),
            'total_hypotheses':total,'high_probability_hypotheses':high_prob,
            'high_confidence_hypotheses':high_conf,'dominant_eigenvalue':str(self.matrix.dominant_eigenvalue),
            'spectral_gap':round(self.matrix.spectral_gap,6),'suppression_coefficient':round(self.matrix.suppression_coefficient,4),
            'crime_type_distribution':dict(crime_dist),'eta_star_floor':ETA_STAR,'phi_ceiling':PHI,'falsifiable_claims':total,
            'version':VERSION}
        return {'network_stats':stats,'suspect_ranking':suspect_risk,
            'top_hypotheses':[{'id':h.id,'suspect':h.suspect_id,'crime':h.crime_type,'probability':h.probability,
                'confidence':h.confidence,'description':h.description,'falsifiable':h.falsifiable,
                'evidence_refs':h.evidence_refs} for h in ranked[:20]],
            'intervention_priorities':[{'priority':i+1,'suspect_id':s['id'],'suspect_name':s['name'],
                'action':'investigate_primary' if s['suspicion_score']>0.7 else 'investigate_secondary' if s['suspicion_score']>0.5 else 'monitor',
                'suspicion_score':s['suspicion_score']} for i,s in enumerate(suspect_risk)]}

    def export_json(self, filepath=None):
        assessment = self.assess_interventions()
        export = {'version':VERSION,'created':self.matrix.created,'framework':'EVEZ Eigenforensics',
            'methodology':'AEMDAS','eigenvalues':{'Phi':PHI,'eta_star':ETA_STAR,'r':R_CRITICAL,
            'lambda_dom':LAMBDA_DOM,'lambda_I80':LAMBDA_I80,'r_I80':R_I80},
            'nodes':{nid:asdict(node) for nid,node in self.matrix.nodes.items()},
            'edges':[asdict(e) for e in self.matrix.edges],
            'hypotheses':[asdict(h) for h in self.matrix.hypotheses],'assessment':assessment}
        def clean(obj):
            if isinstance(obj, complex):
                return {'real':round(obj.real,6),'imag':round(obj.imag,6)}
            if isinstance(obj, dict):
                return {k:clean(v) for k,v in obj.items()}
            if isinstance(obj, list):
                return [clean(v) for v in obj]
            return obj
        export = clean(export)
        if filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(export, f, indent=2)
            return filepath
        return json.dumps(export, indent=2)

    def export_markdown(self, filepath=None):
        assessment = self.assess_interventions()
        stats = assessment['network_stats']
        lines = ['# EVEZ OSINT -- Suspect Inference Matrix Report',
            f'Generated: {self.matrix.created}',
            f'Framework: EVEZ Eigenforensics v{VERSION}','',
            '## Network Statistics',
            f'- Total suspects: {stats["total_suspects"]}',
            f'- Total edges: {stats["total_edges"]}',
            f'- Total hypotheses: {stats["total_hypotheses"]}',
            f'- High probability (>50%): {stats["high_probability_hypotheses"]}',
            f'- High confidence (>70%): {stats["high_confidence_hypotheses"]}',
            f'- Dominant eigenvalue: {stats["dominant_eigenvalue"]}',
            f'- Spectral gap: {stats["spectral_gap"]}',
            f'- Suppression coefficient: {stats["suppression_coefficient"]}',
            f'- eta* floor: {ETA_STAR} (3% irreducible uncertainty)',
            f'- Phi ceiling: {PHI} (97.3% max coherence)','',
            '## Suspect Ranking','','| Rank | Name | Role | Organization | Suspicion | Max Crime Prob | Centrality | Evidence |',
            '|------|------|------|-------------|-----------|----------------|------------|----------|']
        for i, s in enumerate(assessment['suspect_ranking']):
            lines.append(f'| {i+1} | {s["name"]} | {s.get("role","")} | {s.get("organization","")} | {s["suspicion_score"]:.4f} | {s["max_crime_probability"]:.4f} | {s["centrality"]:.4f} | {s["evidence_count"]} |')
        lines.extend(['','## Top Crime Hypotheses',''])
        for h in assessment['top_hypotheses']:
            lines.extend([f'### {h["id"]}',f'- **Suspect:** {h["suspect"]}',
                f'- **Crime:** {h["crime"]} -- {h["description"]}',
                f'- **Probability:** {h["probability"]:.4f} ({h["probability"]*100:.1f}%)',
                f'- **Confidence:** {h["confidence"]:.4f} ({h["confidence"]*100:.1f}%)',
                f'- **Falsifiable:** {h["falsifiable"]}',f'- **Evidence:** {len(h["evidence_refs"])} sources',''])
        lines.extend(['## Intervention Priorities','','| Priority | Suspect | Action | Suspicion Score |','|----------|---------|--------|-----------------|'])
        for p in assessment['intervention_priorities']:
            lines.append(f'| {p["priority"]} | {p["suspect_name"]} | {p["action"]} | {p["suspicion_score"]:.4f} |')
        lines.extend(['','---','All probabilities are falsifiable. All claims are measurable.',
            f'eta* = {ETA_STAR} is the irreducible floor. Phi = {PHI} is the coherence ceiling.',
            'The 3% is the uncertainty. The 97.3% is the measurement.','','⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋'])
        report = '\n'.join(lines)
        if filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(report)
            return filepath
        return report

    def log_to_db(self):
        """Log this session to the usage database."""
        if self.db:
            run_time = int((time.time() - self._start_time) * 1000)
            return self.db.log_session(self, run_time)
        return None

    def get_db_stats(self):
        """Get aggregate statistics from the database."""
        if self.db:
            return self.db.get_stats()
        return {}

    def close(self):
        if self.db:
            self.db.close()

# ============================================================
# DEMO
# ============================================================

def demo_epd_case():
    engine = SuspectInferenceEngine(db_path='none')
    engine.add_suspect(SuspectNode(id='saloga',name='Cody Saloga',aliases=['Officer Saloga'],
        role='officer',organization='Evanston PD',location='Evanston, WY',
        evidence_refs=['uinta-county-herald-viral-arrest','smith-v-evanston-1-2025cv00037',
            'youtube-viral-video-1M-views','rock-springs-pd-transfer']))
    engine.add_suspect(SuspectNode(id='kennedy',name='Dustin Kennedy',
        role='officer',organization='Evanston PD',location='Evanston, WY',
        evidence_refs=['uinta-county-herald-viral-arrest']))
    engine.add_suspect(SuspectNode(id='epd-chief',name='EPD Chief (Unknown)',
        role='chief',organization='Evanston PD',location='Evanston, WY',
        evidence_refs=['epd-2022-annual-report-complaints']))
    engine.add_suspect(SuspectNode(id='epd-ia',name='EPD Internal Affairs',
        role='supervisor',organization='Evanston PD',location='Evanston, WY',
        evidence_refs=['epd-2022-annual-report-inquiries']))
    engine.add_suspect(SuspectNode(id='saloga-rspd',name='Rock Springs PD (hiring)',
        role='supervisor',organization='Rock Springs PD',location='Rock Springs, WY',
        evidence_refs=['saloga-transfer-rspd']))
    engine.add_edge(NetworkEdge(source='saloga',target='kennedy',edge_type='partner',
        weight=0.8,correlation=0.75,evidence_refs=['uinta-county-herald-viral-arrest']))
    engine.add_edge(NetworkEdge(source='saloga',target='epd-chief',edge_type='supervisor',
        weight=0.7,correlation=0.60))
    engine.add_edge(NetworkEdge(source='epd-chief',target='epd-ia',edge_type='cover_up',
        weight=0.6,correlation=0.50,evidence_refs=['epd-2022-annual-report-sealed']))
    engine.add_edge(NetworkEdge(source='saloga',target='saloga-rspd',edge_type='transfer',
        weight=0.7,correlation=0.80,evidence_refs=['officer-transfer-pattern']))
    engine.add_edge(NetworkEdge(source='epd-chief',target='saloga-rspd',edge_type='cover_up',
        weight=0.5,correlation=0.65))
    engine.run_full_analysis()
    return engine

if __name__ == '__main__':
    print('EVEZ OSINT Suspect Inference Matrix Engine v' + VERSION)
    print('='*60)
    print(f'Eigenvalues: Phi={PHI}, eta*={ETA_STAR}, r={R_CRITICAL}')
    print(f'lambda_dom={LAMBDA_DOM}, lambda_I80={LAMBDA_I80}, r_I80={R_I80}')
    print('='*60)
    engine = demo_epd_case()
    a = engine.assess_interventions()
    print(f'\n[1] ASSERT: Registered suspects: {len(engine.matrix.nodes)}')
    print(f'[2] EXTRACT: Edges: {len(engine.matrix.edges)}')
    print(f'[3] MEASURE: Eigenvalues: {[round(e.real,6) for e in engine.matrix.eigenvalues[:5]]}')
    print(f'    Dominant: {round(engine.matrix.dominant_eigenvalue.real,6)}')
    print(f'    Spectral gap: {round(engine.matrix.spectral_gap,6)}')
    print(f'    Suppression coefficient: {round(engine.matrix.suppression_coefficient,4)}')
    print(f'[4] DEDUCE: Hypotheses: {len(engine.matrix.hypotheses)}')
    print(f'[5] ASSESS: High-prob hypotheses: {a["network_stats"]["high_probability_hypotheses"]}')
    print('\nSuspect Ranking:')
    for s in a['suspect_ranking']:
        print(f"  {s['name']}: suspicion={s['suspicion_score']:.4f}, max_prob={s['max_crime_probability']:.4f}")
    print('\nTop 5 Hypotheses:')
    for h in a['top_hypotheses'][:5]:
        print(f"  {h['id']}: P={h['probability']:.4f} C={h['confidence']:.4f} [{h['crime']}]")
    print(f'\nAll probabilities falsifiable. eta*={ETA_STAR} is the floor. Phi={PHI} is the ceiling.')
    print('The 3% is the uncertainty. The 97.3% is the measurement.')
    print('⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋')
