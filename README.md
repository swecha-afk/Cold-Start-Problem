# Xpert Cold Start – AI Memory Extraction System

## Overview
An AI-powered conversation understanding pipeline that extracts structured personal and organisational memory from chat histories.

The system identifies:
- People and their relationship circles
- Organisations and their associated conversations
- Personal goals
- Open commitments, follow-ups, deadlines and actionable questions

## Architecture
Briefly explain the pipeline:

Input conversations → Data preprocessing → Entity and relationship extraction → Goal and open-loop detection → Status inference → Structured JSON output.

## Tech Stack
- Python
- Rule-based NLP and contextual heuristics
- JSON-based structured output
- OpenAI-compatible LLM client (if applicable to the implementation)

## Project Structure
- `solution.py` – Main execution entry point
- `pipeline.py` – Core extraction and inference logic
- `run.sh` – Execution script
- `schema.json` – Output structure
- `WRITEUP.md` – Technical methodology and evaluation

## Setup

Python 3 is required.

## Execution

```bash
./run.sh <input_directory> <output_file>
```

Example:

```bash
./run.sh data/dev output.json
```

## Evaluation
The current implementation achieved 21.1/56 on the labelled development evaluation.

| Category | Score |
|---|---:|
| Circles | 4.4/12 |
| Organisations | 1.8/8 |
| Chats | 6.3/8 |
| Open loops found | 5.1/14 |
| Open loops closed right | 3.4/14 |
| **Total** | **21.1/56** |

The dev dataset does not provide labels for Goals and Help, so these categories are excluded from the reported total.

Loop detection:
- Precision: 32.6%
- Recall: 41.9%
- F1: 36.7%

## Limitations
The system uses heuristic and contextual inference. Ambiguous relationships, implicit commitments and context-dependent task completion remain challenging.

See `WRITEUP.md` for the detailed methodology and evaluation.