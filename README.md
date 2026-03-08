## Installation

```bash
python -m venv .venv
source .venv/bin/activate
```


```bash
pip install -r requirements.txt
```

> Note: CarveMe should be installed...

> Activate gem-pipeline -> conda activate gem-pipeline 
---

## Usage

1. Put genome file at `data/input/genome.fna`.
2. Run the pipeline:

```bash
python src/gem_pipeline.py --genome data/input/genome.fna --output-dir data/output
```

## Expected Output Files

- `data/output/proteins.faa`
- `data/output/model.xml`
- `data/output/memote_report.json`
- `data/output/fba_result.txt`


```bash
python src/gem_pipeline.py --protein data/input/protein.fna --output-dir data/output
```
