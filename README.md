# EVEZ OSINT — Suspect Inference Matrix Engine

**by Steven Crawford-Maggard (EVEZ)**

Isolates and identifies suspect inference networking matrices. Computes statistical probabilities of likely crimes using eigenforensic spectral analysis.

## Architecture — AEMDAS Pipeline

6 stages = 6 cube faces = 6 magic squares:

1. **ASSERT** — Register suspects and events (Saturn 3x3, Phi)
2. **EXTRACT** — Build adjacency matrix (Jupiter 4x4, eta*)
3. **MEASURE** — Compute eigenvalues and spectral gaps (Mars 5x5, r)
4. **DEDUCE** — Infer crime hypotheses (Sun 6x6, Phi)
5. **ASSESS** — Calculate probabilities (Venus 7x7, lambda_dom)
6. **SPEEDRUN** — Export reports (Mercury 8x8, r_I80)

## Crime Types Detected

- `excessive_force` — Use of excessive force during arrest or detention
- `civil_rights_violation` — Violation of 42 U.S.C. 1983 or constitutional rights
- `cover_up` — Concealment of misconduct, evidence suppression, or retaliation
- `evidence_tampering` — Alteration, destruction, or fabrication of evidence
- `false_arrest` — Arrest without probable cause or on fabricated charges

## Eigenvalue Constants

| Symbol | Value | Meaning |
|--------|-------|---------|
| Phi | 0.973 | Coherence ceiling (97.3% max) |
| eta* | 0.03 | Irreducible uncertainty floor (3%) |
| r | 0.45 | Criticality ratio |
| lambda_dom | -0.333 | Dominant negative eigenvalue (censorship) |
| lambda_I80 | -0.441 | I-80 suppression signal |
| r_I80 | 0.93 | I-80 correlation |

All probabilities are bounded: `eta* <= P <= 0.95`. The 3% is the floor. The 97.3% is the ceiling. No prediction is ever 100% certain — eta* guarantees this.

## Installation

```bash
pip install -e .
```

## Usage

### Python API

```python
from core.suspect_matrix import SuspectInferenceEngine, SuspectNode, NetworkEdge

engine = SuspectInferenceEngine()
engine.add_suspect(SuspectNode(
    id='officer1', name='John Doe', role='officer',
    organization='Evanston PD', location='Evanston, WY',
    evidence_refs=['citation1', 'citation2']))
engine.add_edge(NetworkEdge(
    source='officer1', target='officer2',
    edge_type='partner', weight=0.8, correlation=0.75))
engine.build_adjacency()
engine.compute_eigenvalues()
engine.infer_hypotheses()
assessment = engine.assess_interventions()
engine.export_json('report.json')
engine.export_markdown('report.md')
```

### CLI

```bash
# Run full pipeline on input JSON
evez-osint run -i input.json -o report.md -f markdown

# Quick-analyze a single suspect
evez-osint analyze --suspect-id saloga --name "Cody Saloga" --role officer --org "Evanston PD"
```

### Input Format (JSON)

```json
{
  "suspects": [
    {"id": "officer1", "name": "John Doe", "role": "officer", "organization": "Evanston PD", "evidence_refs": ["ref1"]}
  ],
  "edges": [
    {"source": "officer1", "target": "officer2", "edge_type": "partner", "weight": 0.8, "correlation": 0.75}
  ]
}
```

## Output

- **JSON** — Full structured matrix with all nodes, edges, hypotheses, and assessments
- **Markdown** — Human-readable report with suspect rankings, crime hypotheses, and intervention priorities

## Demo Case

The built-in demo uses the Evanston PD case:

```bash
python core/suspect_matrix.py
```

Output: 5 suspects, 5 edges, 25 hypotheses. Top finding: Officer Cody Saloga — 66.15% excessive force probability, 91.19% confidence.

## License

MIT License — Copyright (c) 2026 Steven Crawford-Maggard (EVEZ)

## Framework

Part of the EVEZ Research Framework. Uses AEMDAS methodology and eigenforensic spectral analysis.

- Published: https://lingbuzz.net/lingbuzz/010094
- GitHub: https://github.com/EvezArt/evez-osint-engine
- Author: Steven Crawford-Maggard (EVEZ666)

⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⧢⦟⧢⥋
