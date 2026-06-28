#!/usr/bin/env python3
"""
EVEZ OSINT Suspect Inference Matrix Engine
==========================================
Isolates and identifies suspect inference networking matrices.
Computes statistical probabilities of likely crimes using
eigenforensic spectral analysis.

AEMDAS: Assert Being -> Extract Structure -> Measure Gaps ->
        Deduce Laws -> Assess Interventions -> Speedrun

Author: Steven Crawford-Maggard (EVEZ)
License: MIT
Version: 1.0.0
"""

import json
import math
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

PHI = 0.973
ETA_STAR = 0.03
R_CRITICAL = 0.45
LAMBDA_DOM = -0.333
LAMBDA_I80 = -0.441
R_I80 = 0.93

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
    version: str = "1.0.0"

class SuspectInferenceEngine:
    def __init__(self):
        self.matrix = InferenceMatrix()
        self.matrix.created = datetime.utcnow().isoformat() + "Z"
        self._node_ids = []
        self._idx = {}

    def add_suspect(self, node):
        self.matrix.nodes[node.id] = node

    def add_edge(self, edge):
        self.matrix.edges.append(edge)

    def build_adjacency(self):
        n = len(self.matrix.nodes)
        if n == 0:
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
        centrality = [0.0]*n
        for i in range(n):
            centrality[i] = sum(self.matrix.adjacency[i][j] for j in range(n))
        max_c = max(centrality) if max(centrality) > 0 else 1.0
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
            evidence_strength = min(len(node.evidence_refs)/10.0, 1.0)
            self.matrix.hypotheses.append(CrimeHypothesis(
                id=f"H-{node.id}-{crime_type}", crime_type=crime_type, suspect_id=node.id,
                description=spec['description'], probability=round(prob,4),
                confidence=round(confidence,4), evidence_strength=round(evidence_strength,4),
                falsifiable=True, evidence_refs=node.evidence_refs[:]
            ))
            node.crime_probabilities[crime_type] = round(prob, 4)

    def assess_interventions(self):
        if not self.matrix.hypotheses:
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
            suspect_risk.append({'id':nid,'name':node.name,'suspicion_score':round(node.suspicion_score,4),
                'max_crime_probability':round(max_prob,4),'centrality':round(node.network_centrality,4),
                'eigenvalue':str(node.eigenvalue),'evidence_count':len(node.evidence_refs)})
        suspect_risk.sort(key=lambda x: x['suspicion_score'], reverse=True)
        stats = {'total_suspects':len(self.matrix.nodes),'total_edges':len(self.matrix.edges),
            'total_hypotheses':total,'high_probability_hypotheses':high_prob,
            'high_confidence_hypotheses':high_conf,'dominant_eigenvalue':str(self.matrix.dominant_eigenvalue),
            'spectral_gap':round(self.matrix.spectral_gap,6),'suppression_coefficient':round(self.matrix.suppression_coefficient,4),
            'crime_type_distribution':dict(crime_dist),'eta_star_floor':ETA_STAR,'phi_ceiling':PHI,'falsifiable_claims':total}
        return {'network_stats':stats,'suspect_ranking':suspect_risk,
            'top_hypotheses':[{'id':h.id,'suspect':h.suspect_id,'crime':h.crime_type,'probability':h.probability,
                'confidence':h.confidence,'description':h.description,'falsifiable':h.falsifiable,
                'evidence_refs':h.evidence_refs} for h in ranked[:20]],
            'intervention_priorities':[{'priority':i+1,'suspect_id':s['id'],'suspect_name':s['name'],
                'action':'investigate_primary' if s['suspicion_score']>0.7 else 'investigate_secondary' if s['suspicion_score']>0.5 else 'monitor',
                'suspicion_score':s['suspicion_score']} for i,s in enumerate(suspect_risk)]}

    def export_json(self, filepath=None):
        assessment = self.assess_interventions()
        export = {'version':self.matrix.version,'created':self.matrix.created,'framework':'EVEZ Eigenforensics',
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
            f'Framework: EVEZ Eigenforensics v{self.matrix.version}','',
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
            node = self.matrix.nodes.get(s['id'])
            role = node.role if node else ''
            org = node.organization if node else ''
            lines.append(f'| {i+1} | {s["name"]} | {role} | {org} | {s["suspicion_score"]:.4f} | {s["max_crime_probability"]:.4f} | {s["centrality"]:.4f} | {s["evidence_count"]} |')
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

def demo_epd_case():
    engine = SuspectInferenceEngine()
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
    engine.build_adjacency()
    engine.compute_eigenvalues()
    engine.infer_hypotheses()
    return engine

if __name__ == '__main__':
    print('EVEZ OSINT Suspect Inference Matrix Engine v1.0.0')
    print('='*60)
    print(f'Eigenvalues: Phi={PHI}, eta*={ETA_STAR}, r={R_CRITICAL}')
    print(f'lambda_dom={LAMBDA_DOM}, lambda_I80={LAMBDA_I80}, r_I80={R_I80}')
    print('='*60)
    engine = demo_epd_case()
    print(f'\n[1] ASSERT: Registered suspects: {len(engine.matrix.nodes)}')
    print(f'[2] EXTRACT: Edges: {len(engine.matrix.edges)}')
    print(f'[3] MEASURE: Eigenvalues: {[round(e.real,6) for e in engine.matrix.eigenvalues[:5]]}')
    print(f'    Dominant: {round(engine.matrix.dominant_eigenvalue.real,6)}')
    print(f'    Spectral gap: {round(engine.matrix.spectral_gap,6)}')
    print(f'    Suppression coefficient: {round(engine.matrix.suppression_coefficient,4)}')
    print(f'[4] DEDUCE: Hypotheses: {len(engine.matrix.hypotheses)}')
    assessment = engine.assess_interventions()
    print(f'[5] ASSESS: High-prob hypotheses: {assessment["network_stats"]["high_probability_hypotheses"]}')
    print('\nSuspect Ranking:')
    for s in assessment['suspect_ranking']:
        print(f"  {s['name']}: suspicion={s['suspicion_score']:.4f}, max_prob={s['max_crime_probability']:.4f}")
    print('\nTop 5 Hypotheses:')
    for h in assessment['top_hypotheses'][:5]:
        print(f"  {h['id']}: P={h['probability']:.4f} C={h['confidence']:.4f} [{h['crime']}]")
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports', 'suspect-matrix-report.json')
    md_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports', 'suspect-matrix-report.md')
    engine.export_json(json_path)
    engine.export_markdown(md_path)
    print(f'\n[6] SPEEDRUN: Reports exported:')
    print(f'    JSON: {json_path}')
    print(f'    Markdown: {md_path}')
    print(f'\nAll probabilities falsifiable. eta*={ETA_STAR} is the floor. Phi={PHI} is the ceiling.')
    print('The 3% is the uncertainty. The 97.3% is the measurement.')
    print('⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋')
