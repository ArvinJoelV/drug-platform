# Drug Platform

This repository contains a hackathon prototype for a Market Intelligence Agent.

## Structure

- `market_agent/`: Python market intelligence agent package
- `market_agent/main.py`: CLI entry point
- `market_agent/sample_prevalence.csv`: Optional local disease prevalence dataset

## Example

```powershell
python market_agent/main.py --disease "colorectal cancer" --prevalence-csv market_agent/sample_prevalence.csv
```

## Notes

- Uses WHO GHO and World Bank health indicators as open data sources.
- Uses ChromaDB for vector storage when installed.
- Falls back to lightweight local implementations if optional dependencies are missing.

