# 04 Minimal Evals Exercise

This folder is the smallest useful eval harness in the repo:

- `dataset.py`: hand-written JSONL examples
- `documents.py`: fixed source corpus
- `retriever.py`: retrieval component eval seam
- `answerer.py`: prompt + model seam
- `scorers.py`: deterministic evals first, judge evals later
- `reporting.py`: local structured run logs and summaries
- `main.py`: one-shot batch script, not a chat loop

## Flow

The current `04` exercise runs in this order:

1. Load local settings and the hand-written dataset.
2. Load the fixed document corpus.
3. Retrieve top-k documents for each question.
4. Build a prompt from `question + retrieved docs`.
5. Generate an answer with the OpenAI answerer.
6. Save a structured `RunRecord`.
7. Score the run with deterministic evals first.
8. Print a summary report across all examples.

This is intentionally simple. It gives you one clean pipeline:

`dataset -> retrieval -> prompt assembly -> answer -> run record -> scoring -> report`

## Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Main as main.py
    participant Dataset as dataset.py
    participant Docs as documents.py
    participant Async as asyncio
    participant Retriever as retriever.py
    participant Answerer as answerer.py
    participant Scorers as scorers.py
    participant Report as reporting.py

    Main->>Dataset: load_examples()
    Main->>Docs: build_documents()
    Main->>Async: asyncio.run(run_all_examples(...))
    loop one task per EvalExample
        Async->>Async: acquire semaphore slot
        Async->>Retriever: retrieve(question, documents, top_k)
        Retriever-->>Async: retrieved docs
        Async->>Answerer: answer(question, retrieved docs)
        Answerer-->>Async: answer + prompt + usage
        Async->>Scorers: score(example, run_record)
        Scorers-->>Async: scorer results
        Async->>Report: write_run_record(run_record)
        Report-->>Async: run record persisted
        Async->>Async: release semaphore slot
    end
    Async-->>Main: run_records
    Main->>Report: summarize_runs(run_records)
    Report-->>Main: aggregate summary
```



Suggested exercise order:

1. Inspect `GoldDocHitAtKScorer`.
2. Add one more deterministic retrieval or answer scorer.
3. Run prompt experiments against the OpenAI answerer.
4. Add one judge-based groundedness scorer.
5. Export the run records into your preferred eval backend.

# Eval Datasets and Scopes:

To operationalize the frameworks from **Jason Liu** (Tier 2 Relationships) and **Eugene Yan** (Practical RAG Patterns), you need datasets that go beyond simple "Question-Answer" pairs. You need "Question-Context-Answer" triplets.

Here is a breakdown of canonical datasets on Hugging Face mapped to Liu's **Tier 2 RAG Relationships** and the prioritization of **Patents** for these evals.

---

## 1 Mapping Hugging Face Datasets to Tier 2 Evals

Jason Liu’s Tier 2 focuses on the relationship between Question ($Q$), Context ($C$), and Answer ($A$).


| Tier 2 Relationship             | Definition                                              | Recommended HF Datasets                                                                                                                                                                                                                                                                                                    |
| ------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Context Relevance ($C | Q$)** | Does the retrieved chunk actually answer the query?     | **[MS MARCO](https://huggingface.co/datasets/microsoft/ms_marco)** (v2.1): The gold standard for passage ranking and relevance. **[Natural Questions (NQ)](https://www.google.com/search?q=https://huggingface.co/datasets/google-ads-nq)**: Real Google searches mapped to Wikipedia passages.                            |
| **Faithfulness ($A | C$)**      | Is the answer grounded *only* in the retrieved context? | **[HaluEval](https://www.google.com/search?q=https://huggingface.co/datasets/pwenhu/HaluEval)**: Specifically designed to detect hallucinations in RAG outputs. **[FEVER](https://www.google.com/search?q=https://huggingface.co/datasets/fever)**: Fact extraction and verification dataset.                              |
| **Answer Relevance ($A | Q$)**  | Does the answer address the user's intent?              | **[HotpotQA](https://www.google.com/search?q=https://huggingface.co/datasets/hotpot_qa)**: Requires multi-hop reasoning; if the answer is relevant to the question but misses a "hop," it fails. **[SQuAD v2.0](https://huggingface.co/datasets/rajpurkar/squad_v2)**: Crucial because it includes unanswerable questions. |


---

## 2 Patent RAG Evaluation (The "High-Stakes" Tier)

Patents are the "Final Boss" of RAG because of their legal density and structural complexity. If you are prioritizing patents, you should focus on **Faithfulness ($A  C$)**—a hallucination in a patent search can lead to a multi-million dollar infringement oversight.

### Canonical Patent Datasets

- **[Hupd (Harvard USPTO Patent Dataset)](https://huggingface.co/datasets/HUPD/hupd):** The most comprehensive collection on HF. It contains over 7 million patent documents.
- **[PatentMatch](https://www.google.com/search?q=https://huggingface.co/datasets/TUWien/PatentMatch):** Ideal for **Context Relevance ($C  Q$)**. It specifically evaluates whether a patent claim matches a given technical description (prior art).

### Why Prioritize Patents?

If you use Eugene Yan’s "Evals first" pattern, patents provide a unique stress test for:

1. **Long-context Retrieval:** Patent claims are often buried in 50+ pages of legalese.
2. **Precision requirements:** Unlike a chatbot recommending a movie, patent RAG requires **100% Groundedness**.
3. **Evaluated Status:** Most of these are "pre-evaluated" in the sense that they have leaderboards on **PapersWithCode**, but for your custom RAG, you should run them through a **LLM-as-a-Judge** (using RAGAS or Arize Phoenix) to get your baseline.

---

## 3 Implementation Strategy (The Eugene Yan Approach)

Eugene Yan emphasizes building an **Eval Flywheel**. Instead of just downloading a dataset, you should:

1. **Start with Synthetic Evals:** Use the **[Hugging Face RAG Cookbook](https://huggingface.co/learn/cookbook/rag_evaluation)** method. Use a "Generator LLM" to create $(Q, C, A)$ triplets from your specific patent PDFs.
2. **Unit Tests for RAG:** Don't just measure "accuracy." Measure **"Recall at K"** for your retriever and **"Faithfulness"** for your generator separately.
3. **Human-in-the-loop:** For patents, use the **[Argilla](https://huggingface.co/argilla)** tool on Hugging Face to have a domain expert (patent attorney/agent) verify a small "Golden Set" of 50 samples.

> **Expert Tip:** If you are working with patents, prioritize **[RAGAS](https://www.google.com/search?q=https://github.com/explodinggradients/ragas)** metrics. It is the industry standard for calculating Liu's Tier 2 relationships ($C  Q, A  C, A  Q$) programmatically using Hugging Face models as the underlying judges.

Would you like a Python snippet showing how to load one of these patent datasets and format it for a RAGAS evaluation?

By the way, to unlock the full functionality of all Apps, enable [Gemini Apps Activity](https://myactivity.google.com/product/gemini).





# Sample Eval Hugging face light eval harness:

Inspiration from Huggingface LightEval:

``` https://github.com/huggingface/lighteval.git ```


## Inputs:

### Multiple tasks with reasoning tag removal  

```
lighteval vllm \  

    "model_name=mistralai/Magistral-Small-2507,dtype=float16,data_parallel_size=4" \  

    aime24 \  

    --remove-reasoning-tags \  

    --reasoning-tags="[('[THINK]','[/THINK]')]"  
```



## Eval Pipeline consrunction Design:

1. [Lighteval Pipeline Class](https://github.com/huggingface/lighteval/blob/6496d623/src/lighteval/pipeline.py#L70-L78)

```
class Pipeline:
    def __init__(
        self,
        tasks: str,
        pipeline_parameters: PipelineParameters,
        evaluation_tracker: EvaluationTracker,
        model_config: ModelConfig | None = None,
        model=None,
        metric_options=None,
```


# AI engineering design patterns

Here's a comprehensive overview of eval harnesses by AI engineering design pattern:

---

## The 5 AI Engineering Patterns & Their Eval Harnesses

---

### 1. Single-Turn LLM Call
*One prompt in, one response out. No memory, no tools, no state.*

**What you're testing:** Does the model produce the right output for a given input?

**Eval harness to build:**
- **Dataset-driven regression suite** — a golden set of (input, expected output) pairs stored in a file or DB. Run on every model/prompt change.
- **Exact match evaluator** — for classification, extraction, factual QA where there's one right answer.
- **LLM-as-judge evaluator** — for tone, helpfulness, coherence, style. A second LLM scores the output 1–5 against a rubric.
- **Schema validator** — for structured outputs (JSON, XML). Assert field presence, types, value ranges.

**Key metrics:** accuracy, format compliance, latency p50/p99, cost per call, refusal rate.

**Tooling:** `promptfoo`, `Braintrust`, `pytest` + custom scorers, `openai/evals`.

---

### 2. RAG Pipeline
*Retrieve relevant chunks → inject into prompt → generate grounded answer.*

**What you're testing:** Two distinct systems — the retriever AND the generator. Never conflate them.

**Eval harness to build:**
- **Retrieval eval (offline)** — given a query, did the right chunks come back? Metrics: recall@k, precision@k, NDCG, MRR. Requires a labeled (query → relevant doc IDs) dataset.
- **Faithfulness eval** — is the generated answer actually supported by the retrieved context? LLM-as-judge checks for hallucination relative to the source, not ground truth.
- **Answer correctness eval** — end-to-end: is the final answer right? Exact match or LLM judge against a golden answer.
- **Context utilization eval** — is the model actually using what was retrieved, or ignoring it?

**Key metrics:** recall@k, faithfulness score, hallucination rate, answer correctness, context precision.

**Tooling:** `RAGAS`, `TruLens`, `DeepEval`, `LangSmith`.

---

### 3. Multi-Turn Conversation
*Session with accumulating history. User and assistant exchange multiple messages toward a goal.*

**What you're testing:** Does the model maintain coherence, remember context, and help the user reach their goal across the whole session — not just turn by turn?

**Eval harness to build:**
- **Trajectory replay harness** — pre-scripted conversation scripts that run deterministically. Assert on specific turns (e.g., "by turn 3, the model should have asked for X").
- **Simulated user harness** — a second LLM plays the user, including edge cases like changing their mind, being vague, or being adversarial. Runs full sessions automatically.
- **Goal completion evaluator** — end-of-session: did the user accomplish what they came to do? Binary or rubric-scored by LLM judge.
- **Coherence & memory checker** — does the model contradict itself across turns? Does it forget information the user gave earlier?

**Key metrics:** task completion rate, turns to completion, recovery rate from confusion, contradiction rate.

**Tooling:** `Botpress evals`, `LangSmith`, custom simulation loops, human annotation pipelines.

---

### 4. Agent / Tool-Use
*The LLM plans and executes multi-step actions — calling APIs, writing files, querying DBs — to complete a task.*

**What you're testing:** Did the agent take the right actions, in the right order, using tools correctly, without doing anything dangerous?

**Eval harness to build:**
- **Sandboxed execution harness** — a real or mock environment where tools actually run (mock API server, in-memory DB, temp filesystem). The harness checks the end state, not just what the model said it would do.
- **Trajectory evaluator** — given a task, was the sequence of tool calls correct? Score at the step level (was each call valid?) and the plan level (was the overall strategy right?).
- **Outcome evaluator** — ignore the steps; did the world end up in the right state? (e.g., was the correct row inserted? was the right file created?)
- **Safety / refusal harness** — explicitly test that the agent refuses destructive or unauthorized actions. Inject prompts designed to elicit harmful tool calls.

**Key metrics:** task success rate, step efficiency (steps taken vs. optimal), invalid tool call rate, refusal rate on unsafe tasks, cost per task.

**Tooling:** `Inspect AI` (UK AISI), `AgentBench`, `SWE-bench`, `ToolBench`, `LangSmith traces`.

---

### 5. Multi-Agent Orchestration
*A network of specialized agents coordinate — passing tasks, sharing state, checking each other's work — to solve a complex goal.*

**What you're testing:** Do agents hand off correctly, stay consistent with each other, recover from individual failures, and produce a correct end result?

**Eval harness to build:**
- **Contract / schema testing** — validate that every agent's output matches the schema expected by the next agent in the pipeline. Catches integration failures before runtime.
- **End-to-end correctness harness** — run the full multi-agent pipeline on a golden task set. Score only the final output (ignores internal routing as long as the answer is right).
- **Fault injection harness** — deliberately fail individual agents mid-run. Test whether the orchestrator retries, reroutes, or fails gracefully rather than silently producing wrong output.
- **Consistency checker** — do different agents make contradictory claims or decisions about the same entity within one run?
- **Observability harness** — full span-level tracing of every agent call, with cost and latency per agent. Required for debugging; also used to detect runaway loops.

**Key metrics:** end-to-end task success rate, handoff error rate, recovery rate from agent failure, total run cost, deadlock/loop rate.

**Tooling:** `OpenTelemetry` + `LangSmith`/`Langfuse`, `CrewAI evals`, custom orchestration test runners.

---

## Universal Principles Across All 5

**Separate retrieval from generation** (RAG), **steps from outcomes** (agents), and **turn quality from session quality** (conversation). Conflating these makes failures undiagnosable.

**Always have a held-out golden dataset.** Never eval only on data the system was prompted or fine-tuned with.

**Automate regression, humanize edge cases.** Run automated evals on every change; bring in human raters when automated scores diverge from intuition or for high-stakes rubrics.

**Eval the failure modes, not just the happy path.** Every harness should include adversarial inputs, malformed tool responses, empty retrievals, and mid-session user pivots.

**Track cost alongside quality.** A 95% accurate agent that costs $2/task may be worse than an 90% accurate one at $0.10/task depending on your use case.
