#!/usr/bin/env python3
"""
Generate an HTML report comparing question quality commenting across conditions.
Redesigned with modern visual design and side-by-side comparison UX.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import html as html_module


def load_results(file_path: str) -> dict:
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_html(data: dict) -> str:
    """Generate HTML report from results data."""

    # Extract summary data
    summary = data['summary']
    prompts = data['prompts']
    detailed = data['detailed_results']
    runs_per_prompt = data.get('runs_per_prompt', 3)

    # Define condition order: baseline first, then interventions sorted by rate
    condition_order = ['baseline'] if 'baseline' in summary else []
    interventions = [(k, v) for k, v in summary.items() if k != 'baseline']
    interventions.sort(key=lambda x: x[1]['quality_comment_rate'])
    condition_order.extend([k for k, v in interventions])

    # Calculate baseline rate for deltas
    baseline_rate = summary.get('baseline', {}).get('quality_comment_rate', 0)

    # Color scheme
    colors = {
        'baseline': '#6366f1',      # Indigo
        'intervention': '#10b981',  # Emerald
        'regression': '#ef4444',    # Red
        'clean': '#10b981',         # Emerald
        'flagged': '#ef4444',       # Red
        'mixed': '#f59e0b',         # Amber
    }

    # Build summary cards data
    summary_cards_data = []
    for condition in condition_order:
        stats = summary[condition]
        rate = stats['quality_comment_rate']
        count = stats['quality_comment_count']
        total = stats['total_runs']
        delta = rate - baseline_rate

        if condition == 'baseline':
            delta_text = 'baseline'
            card_color = colors['baseline']
        elif delta < 0:
            delta_text = f'{delta*100:+.0f} ppt'
            card_color = colors['intervention']
        else:
            delta_text = f'{delta*100:+.0f} ppt'
            card_color = colors['regression']

        summary_cards_data.append({
            'condition': condition,
            'rate': rate,
            'count': count,
            'total': total,
            'delta_text': delta_text,
            'color': card_color,
            'is_baseline': condition == 'baseline'
        })

    # Build prompt comparison data structure
    prompt_data = []
    for i, prompt in enumerate(prompts):
        prompt_info = {
            'index': i,
            'text': prompt,
            'conditions': {}
        }

        for condition in condition_order:
            condition_results = detailed.get(condition, [])
            prompt_results = [r for r in condition_results if r['prompt'] == prompt]

            runs = []
            for j, result in enumerate(prompt_results):
                runs.append({
                    'run_num': j + 1,
                    'flagged': result['has_quality_comment'],
                    'response_text': result['response_text'],
                    'pattern_match': result.get('pattern_match', False),
                    'pattern_matched_text': result.get('pattern_matched_text'),
                    'llm_match': result.get('llm_match', False),
                    'llm_matched_text': result.get('llm_matched_text'),
                    'llm_category': result.get('llm_category', ''),
                    'llm_explanation': result.get('llm_explanation', '')
                })

            flagged_count = sum(1 for r in runs if r['flagged'])
            prompt_info['conditions'][condition] = {
                'runs': runs,
                'flagged_count': flagged_count,
                'total': len(runs),
                'all_clean': flagged_count == 0,
                'all_flagged': flagged_count == len(runs)
            }

        prompt_data.append(prompt_info)

    # Generate verdict
    best_intervention = None
    best_rate = baseline_rate
    for condition in condition_order:
        if condition != 'baseline' and summary[condition]['quality_comment_rate'] < best_rate:
            best_rate = summary[condition]['quality_comment_rate']
            best_intervention = condition

    if best_intervention is None:
        verdict = "No improvement detected"
        verdict_desc = "The interventions did not reduce quality commenting compared to baseline."
        verdict_class = "bad"
    else:
        improvement = (baseline_rate - best_rate) * 100
        if improvement >= 30:
            verdict = "Strong improvement"
            verdict_class = "good"
        elif improvement >= 15:
            verdict = "Moderate improvement"
            verdict_class = "moderate"
        else:
            verdict = "Modest improvement"
            verdict_class = "modest"
        verdict_desc = f"{best_intervention} reduced quality commenting by {improvement:.0f} percentage points."

    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Commenting A/B Test Results</title>
    <style>
        :root {{
            --bg-primary: #fafafa;
            --bg-card: #ffffff;
            --bg-hover: #f5f5f5;
            --text-primary: #18181b;
            --text-secondary: #71717a;
            --text-muted: #a1a1aa;
            --border-color: #e4e4e7;
            --border-light: #f4f4f5;
            --indigo: #6366f1;
            --indigo-light: #eef2ff;
            --emerald: #10b981;
            --emerald-light: #d1fae5;
            --red: #ef4444;
            --red-light: #fee2e2;
            --amber: #f59e0b;
            --amber-light: #fef3c7;
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 16px;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -4px rgba(0,0,0,0.05);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            font-size: 15px;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-primary);
            -webkit-font-smoothing: antialiased;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        /* Header */
        .header {{
            margin-bottom: 32px;
        }}

        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}

        .header-meta {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .header-meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Verdict Banner */
        .verdict {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 20px 24px;
            border-radius: var(--radius-lg);
            margin-bottom: 32px;
        }}

        .verdict.good {{
            background: var(--emerald-light);
            border: 1px solid var(--emerald);
        }}

        .verdict.moderate {{
            background: #fef3c7;
            border: 1px solid var(--amber);
        }}

        .verdict.modest {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
        }}

        .verdict.bad {{
            background: var(--red-light);
            border: 1px solid var(--red);
        }}

        .verdict-icon {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            flex-shrink: 0;
        }}

        .verdict.good .verdict-icon {{ background: var(--emerald); color: white; }}
        .verdict.moderate .verdict-icon {{ background: var(--amber); color: white; }}
        .verdict.modest .verdict-icon {{ background: var(--text-muted); color: white; }}
        .verdict.bad .verdict-icon {{ background: var(--red); color: white; }}

        .verdict-content h2 {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .verdict-content p {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        /* Summary Cards */
        .summary-section {{
            margin-bottom: 48px;
        }}

        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }}

        .summary-card {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            padding: 24px;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
        }}

        .summary-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }}

        .summary-card.baseline::before {{ background: var(--indigo); }}
        .summary-card.improved::before {{ background: var(--emerald); }}
        .summary-card.regressed::before {{ background: var(--red); }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 16px;
        }}

        .card-label {{
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .card-badge {{
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
        }}

        .card-badge.baseline {{
            background: var(--indigo-light);
            color: var(--indigo);
        }}

        .card-badge.improved {{
            background: var(--emerald-light);
            color: var(--emerald);
        }}

        .card-badge.regressed {{
            background: var(--red-light);
            color: var(--red);
        }}

        .card-rate {{
            font-size: 42px;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }}

        .card-rate.baseline {{ color: var(--indigo); }}
        .card-rate.improved {{ color: var(--emerald); }}
        .card-rate.regressed {{ color: var(--red); }}

        .card-detail {{
            font-size: 14px;
            color: var(--text-secondary);
        }}

        /* Visual Comparison Bar */
        .comparison-bar {{
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid var(--border-light);
        }}

        .bar-container {{
            height: 8px;
            background: var(--border-light);
            border-radius: 4px;
            overflow: hidden;
        }}

        .bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        .bar-fill.baseline {{ background: var(--indigo); }}
        .bar-fill.improved {{ background: var(--emerald); }}
        .bar-fill.regressed {{ background: var(--red); }}

        /* Prompt Comparison Section */
        .prompts-section {{
            margin-bottom: 48px;
        }}

        .prompt-card {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            margin-bottom: 16px;
            overflow: hidden;
        }}

        .prompt-header {{
            padding: 20px 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 16px;
            transition: background 0.15s ease;
            user-select: none;
        }}

        .prompt-header:hover {{
            background: var(--bg-hover);
        }}

        .prompt-number {{
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: var(--bg-hover);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            flex-shrink: 0;
        }}

        .prompt-text {{
            flex: 1;
            font-size: 14px;
            color: var(--text-primary);
            line-height: 1.5;
        }}

        .prompt-badges {{
            display: flex;
            gap: 8px;
            flex-shrink: 0;
        }}

        .prompt-badge {{
            font-size: 11px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            white-space: nowrap;
        }}

        .prompt-badge.clean {{
            background: var(--emerald-light);
            color: var(--emerald);
        }}

        .prompt-badge.flagged {{
            background: var(--red-light);
            color: var(--red);
        }}

        .prompt-badge.mixed {{
            background: var(--amber-light);
            color: var(--amber);
        }}

        .expand-icon {{
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-muted);
            transition: transform 0.2s ease;
            flex-shrink: 0;
        }}

        .prompt-card.expanded .expand-icon {{
            transform: rotate(180deg);
        }}

        /* Response Comparison Area */
        .response-area {{
            display: none;
            border-top: 1px solid var(--border-color);
        }}

        .prompt-card.expanded .response-area {{
            display: block;
        }}

        /* Run Tabs */
        .run-tabs {{
            display: flex;
            gap: 0;
            padding: 0 24px;
            background: var(--bg-hover);
            border-bottom: 1px solid var(--border-color);
        }}

        .run-tab {{
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
            transition: all 0.15s ease;
        }}

        .run-tab:hover {{
            color: var(--text-primary);
        }}

        .run-tab.active {{
            color: var(--indigo);
            border-bottom-color: var(--indigo);
            background: var(--bg-card);
        }}

        /* Side-by-Side Comparison */
        .comparison-grid {{
            display: grid;
            grid-template-columns: repeat({len(condition_order)}, 1fr);
            gap: 1px;
            background: var(--border-color);
        }}

        .condition-column {{
            background: var(--bg-card);
            padding: 20px;
        }}

        .column-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-light);
        }}

        .column-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .column-title.baseline {{ color: var(--indigo); }}
        .column-title.improved {{ color: var(--emerald); }}

        .status-indicator {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 500;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}

        .status-dot.clean {{ background: var(--emerald); }}
        .status-dot.flagged {{ background: var(--red); }}

        .status-indicator.clean {{ color: var(--emerald); }}
        .status-indicator.flagged {{ color: var(--red); }}

        /* Response Content */
        .response-content {{
            font-size: 14px;
            line-height: 1.75;
            color: var(--text-primary);
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .response-content::-webkit-scrollbar {{
            width: 6px;
        }}

        .response-content::-webkit-scrollbar-track {{
            background: var(--border-light);
            border-radius: 3px;
        }}

        .response-content::-webkit-scrollbar-thumb {{
            background: var(--text-muted);
            border-radius: 3px;
        }}

        /* Highlighted Markers */
        .marker-highlight {{
            background: linear-gradient(to bottom, var(--red-light) 0%, var(--red-light) 100%);
            border-bottom: 2px solid var(--red);
            padding: 1px 2px;
            border-radius: 2px;
        }}

        /* Detection Info */
        .detection-info {{
            margin-top: 16px;
            padding: 12px;
            background: var(--bg-hover);
            border-radius: var(--radius-sm);
            font-size: 13px;
        }}

        .detection-label {{
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }}

        .detection-text {{
            color: var(--text-primary);
        }}

        /* Footer */
        .footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .comparison-grid {{
                grid-template-columns: 1fr;
            }}

            .prompt-badges {{
                display: none;
            }}
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .prompt-card {{
            animation: fadeIn 0.3s ease forwards;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Quality Commenting A/B Test</h1>
            <div class="header-meta">
                <span><strong>Model:</strong> {html_module.escape(data.get('model', 'Unknown'))}</span>
                <span><strong>Temperature:</strong> {data.get('temperature', 0.7)}</span>
                <span><strong>Runs:</strong> {runs_per_prompt} per prompt</span>
                <span><strong>Generated:</strong> {datetime.now().strftime('%b %d, %Y at %H:%M')}</span>
            </div>
        </header>

        <!-- Verdict -->
        <div class="verdict {verdict_class}">
            <div class="verdict-icon">
                {'↓' if verdict_class in ['good', 'moderate'] else '→' if verdict_class == 'modest' else '↑'}
            </div>
            <div class="verdict-content">
                <h2>{verdict}</h2>
                <p>{verdict_desc}</p>
            </div>
        </div>

        <!-- Summary Cards -->
        <section class="summary-section">
            <h3 class="section-title">Results by Condition</h3>
            <div class="summary-grid">
'''

    for card in summary_cards_data:
        card_class = 'baseline' if card['is_baseline'] else ('improved' if card['rate'] < baseline_rate else 'regressed')
        html_content += f'''
                <div class="summary-card {card_class}">
                    <div class="card-header">
                        <span class="card-label">{html_module.escape(card['condition'])}</span>
                        <span class="card-badge {card_class}">{card['delta_text']}</span>
                    </div>
                    <div class="card-rate {card_class}">{card['rate']*100:.0f}%</div>
                    <div class="card-detail">{card['count']} of {card['total']} responses flagged</div>
                    <div class="comparison-bar">
                        <div class="bar-container">
                            <div class="bar-fill {card_class}" style="width: {card['rate']*100}%"></div>
                        </div>
                    </div>
                </div>
'''

    html_content += '''
            </div>
        </section>

        <!-- Prompt Comparison -->
        <section class="prompts-section">
            <h3 class="section-title">Response Comparison</h3>
'''

    for prompt_info in prompt_data:
        i = prompt_info['index']
        prompt_text = html_module.escape(prompt_info['text'])

        # Build badges for each condition
        badges_html = ''
        for condition in condition_order:
            cond_data = prompt_info['conditions'][condition]
            if cond_data['all_clean']:
                badge_class = 'clean'
                badge_text = '✓'
            elif cond_data['all_flagged']:
                badge_class = 'flagged'
                badge_text = f'{cond_data["flagged_count"]}/{cond_data["total"]}'
            else:
                badge_class = 'mixed'
                badge_text = f'{cond_data["flagged_count"]}/{cond_data["total"]}'
            badges_html += f'<span class="prompt-badge {badge_class}" title="{condition}">{badge_text}</span>'

        html_content += f'''
            <div class="prompt-card" id="prompt-{i}">
                <div class="prompt-header" onclick="togglePrompt({i})">
                    <span class="prompt-number">{i + 1}</span>
                    <span class="prompt-text">{prompt_text}</span>
                    <div class="prompt-badges">{badges_html}</div>
                    <div class="expand-icon">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M4.94 5.72a.75.75 0 0 1 1.06 0L8 7.69l1.97-1.97a.75.75 0 1 1 1.06 1.06l-2.5 2.5a.75.75 0 0 1-1.06 0l-2.5-2.5a.75.75 0 0 1 0-1.06z"/>
                        </svg>
                    </div>
                </div>
                <div class="response-area">
                    <div class="run-tabs" id="tabs-{i}">
'''
        for run_num in range(1, runs_per_prompt + 1):
            active = 'active' if run_num == 1 else ''
            html_content += f'<div class="run-tab {active}" onclick="selectRun({i}, {run_num})">Run {run_num}</div>'

        html_content += f'''
                    </div>
'''

        # Create content for each run
        for run_num in range(1, runs_per_prompt + 1):
            display = 'block' if run_num == 1 else 'none'
            html_content += f'''
                    <div class="comparison-grid" id="run-{i}-{run_num}" style="display: {display};">
'''
            for condition in condition_order:
                cond_data = prompt_info['conditions'][condition]
                run_data = cond_data['runs'][run_num - 1] if run_num <= len(cond_data['runs']) else None

                if run_data:
                    flagged = run_data['flagged']
                    status_class = 'flagged' if flagged else 'clean'
                    status_text = 'Flagged' if flagged else 'Clean'

                    # Prepare response text with highlighting
                    response_text = html_module.escape(run_data['response_text'])

                    # Highlight markers
                    if run_data.get('llm_matched_text'):
                        matched = html_module.escape(run_data['llm_matched_text'])
                        response_text = response_text.replace(
                            matched,
                            f'<span class="marker-highlight">{matched}</span>',
                            1
                        )
                    elif run_data.get('pattern_matched_text'):
                        matched = html_module.escape(run_data['pattern_matched_text'])
                        response_text = response_text.replace(
                            matched,
                            f'<span class="marker-highlight">{matched}</span>',
                            1
                        )

                    column_class = 'baseline' if condition == 'baseline' else 'improved'

                    detection_html = ''
                    if run_data.get('llm_explanation') and flagged:
                        detection_html = f'''
                        <div class="detection-info">
                            <div class="detection-label">Detection reason</div>
                            <div class="detection-text">{html_module.escape(run_data['llm_explanation'])}</div>
                        </div>
'''

                    html_content += f'''
                        <div class="condition-column">
                            <div class="column-header">
                                <span class="column-title {column_class}">{html_module.escape(condition)}</span>
                                <span class="status-indicator {status_class}">
                                    <span class="status-dot {status_class}"></span>
                                    {status_text}
                                </span>
                            </div>
                            <div class="response-content">{response_text}</div>
                            {detection_html}
                        </div>
'''
                else:
                    html_content += f'''
                        <div class="condition-column">
                            <div class="column-header">
                                <span class="column-title">{html_module.escape(condition)}</span>
                            </div>
                            <div class="response-content" style="color: var(--text-muted);">No data</div>
                        </div>
'''

            html_content += '''
                    </div>
'''

        html_content += '''
                </div>
            </div>
'''

    html_content += f'''
        </section>

        <footer class="footer">
            Quality Commenting Detection Test &middot; {len(prompts)} prompts &middot; {len(condition_order)} conditions
        </footer>
    </div>

    <script>
        function togglePrompt(idx) {{
            const card = document.getElementById('prompt-' + idx);
            card.classList.toggle('expanded');
        }}

        function selectRun(promptIdx, runNum) {{
            // Update tabs
            const tabs = document.querySelectorAll('#tabs-' + promptIdx + ' .run-tab');
            tabs.forEach((tab, i) => {{
                tab.classList.toggle('active', i === runNum - 1);
            }});

            // Update content
            for (let i = 1; i <= {runs_per_prompt}; i++) {{
                const content = document.getElementById('run-' + promptIdx + '-' + i);
                if (content) {{
                    content.style.display = i === runNum ? 'grid' : 'none';
                }}
            }}
        }}

        // Expand first prompt by default for demo
        document.addEventListener('DOMContentLoaded', function() {{
            // Optional: auto-expand first prompt
            // togglePrompt(0);
        }});
    </script>
</body>
</html>
'''

    return html_content


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_question_quality_report.py <results_file.json> [-o output.html]")
        sys.exit(1)

    input_file = sys.argv[1]

    # Parse output file argument
    output_file = None
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    # Generate default output filename if not specified
    if not output_file:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_report.html"

    # Load and generate
    print(f"Loading results from: {input_file}")
    data = load_results(input_file)

    print("Generating HTML report...")
    html_content = generate_html(data)

    # Write output
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"Report saved to: {output_file}")
    print(f"\nOpen in browser: file://{Path(output_file).resolve()}")


if __name__ == "__main__":
    main()
