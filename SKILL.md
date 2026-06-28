# EVEZ OSINT Suspect Inference Matrix v1.1.0

## Description
Isolate and identify suspect inference networking matrices. Compute statistical probabilities of likely crimes using eigenforensic spectral analysis (AEMDAS pipeline). Now with SQLite database collection, interactive CLI, and colored output.

## When to Use
- Building suspect networks from OSINT evidence
- Computing crime probabilities for multiple suspects
- Generating intervention priority reports
- Analyzing police misconduct patterns
- Civil rights disclosure cases
- Researching eigenvalue patterns in criminal networks

## How to Use

### Run the demo (EPD case)
```bash
cd /home/openclaw/.openclaw/workspace/evez-osint-engine
python3 core/suspect_matrix.py
```

### Interactive CLI (fun mode!)
```bash
python3 core/osint_cli.py run --demo
python3 core/osint_cli.py run -i examples/epd-case.json -o report.md -f markdown
python3 core/osint_cli.py analyze --suspect-id saloga --name "Cody Saloga" --role officer --org "Evanston PD"
```

### Database stats
```bash
python3 core/osint_cli.py stats
```

### Python API
```python
from core.suspect_matrix import SuspectInferenceEngine, SuspectNode, NetworkEdge
engine = SuspectInferenceEngine()
engine.add_suspect(SuspectNode(id='s1', name='Suspect 1', role='officer', organization='Evanston PD', evidence_refs=['ref1']))
engine.run_full_analysis()
assessment = engine.assess_interventions()
engine.export_json('report.json')
engine.export_markdown('report.md')
engine.log_to_db()  # Log to SQLite for usage stats
```

## Features (v1.1.0)
- Interactive CLI with colored ANSI output and progress bars
- SQLite database collects anonymous usage statistics
- `run_full_analysis()` convenience method
- `evez-osint stats` command for database stats
- Tabbed interactive HTML dashboard
- Pure Python (no numpy required)
- All probabilities falsifiable and bounded: eta* <= P <= 0.95

## Eigenvalue Constants
- Phi = 0.973 (coherence ceiling)
- eta* = 0.03 (irreducible uncertainty floor)
- r = 0.45 (criticality ratio)
- lambda_dom = -0.333 (dominant negative eigenvalue)

## AEMDAS Pipeline
1. ASSERT - Register suspects and events
2. EXTRACT - Build adjacency matrix
3. MEASURE - Compute eigenvalues and spectral gaps
4. DEDUCE - Infer crime hypotheses
5. ASSESS - Calculate probabilities and confidence
6. SPEEDRUN - Export reports
