# Claude Sycophancy Research

## Project Overview
Research project investigating and reducing sycophancy in Claude's responses — specifically, unwanted "quality commenting" ("Good question!") and emotional management ("Don't be embarrassed") when users express uncertainty. Systematic A/B testing of system prompt interventions with measurable results.

## Owner
Danny (daniel.gross85@gmail.com) — research project.

## Tech Stack
- Python 3, Anthropic SDK (>=0.40.0)
- Claude Sonnet 4.5 (primary test model), Haiku (detection/analysis)
- Plotly (CDN, for interactive HTML reports)

## Key Commands
```bash
pip install -r requirements.txt

# Run experiment
python src/question_quality_test.py [experiment_name] \
  --system-prompt [prompt_name] --runs 3

# Generate comparison report
python src/generate_report.py results/[results_file].json
```

## Architecture
```
src/
  question_quality_test.py  — A/B test runner (575 lines)
  generate_report.py        — Interactive HTML dashboard (921 lines)
prompts/
  claude_ai_system_prompt_xml.txt   — Baseline (104KB)
  intervention_v2.2.txt             — Best intervention (-43 ppt)
results/
  ab_test_*.json            — Experiment results
docs/
  index.html                — GitHub Pages dashboard
```

## Key Results
- Baseline quality commenting rate: 90%
- Best intervention (v2.2): 47% (-43 percentage points)
- Key insight: specific examples beat general instructions

## Detection Methods
- **Pattern matching:** 17 regex patterns across 8 marker categories (300-char scan)
- **LLM detection:** Claude Haiku at temperature 0 for variation catching
- **Combined:** Both methods for thoroughness

## Key Files
- `src/question_quality_test.py` — Test harness with dual detection
- `prompts/intervention_v2.2.txt:856` — The winning intervention text
- `results/ab_test_v2.2_results.json` — Best results data
- `docs/index.html` — Interactive dashboard (GitHub Pages)

## Claude Code Knowledge Base

When you need to leverage Claude Code's advanced capabilities — hooks, custom agents, skills, permission patterns, multi-agent orchestration, or SDK usage — reference the central learnings at:

- **Architecture & capabilities (99 flags, 41 tools, 27 hooks, 100+ env vars):** `/Users/dannygross/CodingProjects/Claude Code codebase/learnings/CLAUDE_CODE_DEEP_DIVE.md`
- **Hook recipes & reference (all 27 events with I/O schemas):** `/Users/dannygross/CodingProjects/Claude Code codebase/learnings/HOOKS_REFERENCE.md`
- **Custom skill templates (8 production skills):** `/Users/dannygross/CodingProjects/Claude Code codebase/learnings/skills/`
- **Full Claude Code source:** `/Users/dannygross/CodingProjects/Claude Code codebase/src/`

Read these when the task involves configuring hooks, building skills, defining custom agents, optimizing permissions, setting up multi-agent workflows, or leveraging any Claude Code feature beyond basic usage. The source code is the definitive reference for how any feature actually works.

**Sycophancy-research-specific patterns in the CC source:**
- **Prompt caching:** `src/services/api/claude.ts:333-435` — static/dynamic boundary split; share cached prefix across 100+ intervention runs
- **Persistent retry:** `src/services/api/withRetry.ts` — unattended mode with 5min max backoff, 6hr cap, 30s heartbeat for overnight runs
- **Extended thinking:** `src/utils/thinking.ts` — ThinkingConfig with budget; analyze reasoning patterns in thinking blocks
- **Modular prompt assembly:** `src/constants/prompts.ts:444-577` — section-based composition for intervention injection without full recompile
- **Cost tracking:** `src/utils/modelCost.ts` — per-experiment cost with cache savings tracking
- **Full pattern map:** `learnings/PROJECT_PATTERNS_MAP.md`
