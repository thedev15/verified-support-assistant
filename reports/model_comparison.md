## Hosted-model comparison — 2026-10-02

### Decision

Keep the deterministic extractive backend as the safest default. Use
`meta-llama/Llama-3.1-8B-Instruct` when generated answers are required under the
current 220-token response budget. Do not use `ibm-granite/granite-4.2-8b` with
that cap unless reasoning is disabled or the completion budget is raised and
re-evaluated.

The live W&B report, panels, run tables, and Weave traces are available in the
[Verified Support Assistant Model Evaluation report](https://wandb.ai/p-akinloye-cse2023016-obafemi-awolowo-university/verified-support-assistant/reports/Verified-Support-Assistant-Model-Evaluation--VmlldzoxODA0MzI5OQ).

### Method

- 40 fixed synthetic benchmark cases
- identical TF-IDF retriever, top-3 context, and relevance threshold
- temperature 0
- 25 hosted-model requests per condition; 15 cases refused before inference
- 220 maximum completion tokens per request
- automatic retries disabled
- one W&B run and case-level table per condition
- Weave traces for app-level and model-level calls

### Results

| Condition | Retrieval | Refusal | Citation validity | Keyword coverage | Mean latency | P95 latency | Prompt tokens | Completion tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Extractive baseline | 100% | 100% | n/a | **92%** | n/a | n/a | 0 | 0 |
| Llama 3.1 8B | 100% | 97.5% | **91.7%** | 75% | **0.172 s** | **0.409 s** | 7,427 | **598** |
| Granite 4.2 8B | 100% | **100%** | 28% | 26% | 1.671 s | 3.429 s | 7,513 | 4,917 |

Traced model cost was approximately $0.00150 for Llama and $0.00126 for
Granite, or **$0.00276 total**.

### Interpretation

Llama is the better hosted choice for this serving envelope. Compared with
Granite, it produced 3.3× higher keyword coverage, 3.27× higher citation
validity, 9.7× lower mean latency, and used 8.2× fewer completion tokens.

Granite's score is primarily a serving-configuration failure, not a universal
model-quality result: 16 of 25 generations ended with `finish_reason="length"`,
and 15 returned blank user-visible content because internal reasoning consumed
the 220-token budget. The result is still operationally meaningful—the model is
not suitable under the project's current latency and completion-token cap.

The extractive baseline remains strongest on this small benchmark. Its 92%
keyword coverage exceeded Llama's 75%, and it preserved perfect refusal
accuracy without inference cost. Generation should therefore be an opt-in UX
mode until a larger semantic evaluation demonstrates a meaningful benefit.

### Changes made from the findings

- expose `finish_reason` in API responses;
- convert empty model output into a safe refusal;
- attach a valid retrieved citation when generated text omits valid citation
  syntax;
- disable implicit SDK retries so request budgets are real;
- abort evaluation on billing/auth failures or two consecutive service errors;
- add tests for blank completions and missing citations.

### Limitations

The dataset is synthetic and small. Keyword coverage is lexical rather than a
semantic groundedness score. Each model has one temperature-0 run. Granite was
constrained by a token cap that was appropriate for concise support answers but
too small for its observed reasoning behavior. These results support this
project's engineering decision; they are not a general ranking of the models.