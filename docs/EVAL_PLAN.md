# Offline Evaluation Plan & Benchmarking Protocol

> **FROZEN BEFORE CODING**
> 
> Locked on November 4, 2026. Do not change these numbers after this point.

---

## 1. Primary Recommendation Metrics
- **Metrics**: **Hit@10** and **NDCG@10** evaluated across simulated listeners.
- **Hit@10**: Proportion of test instances where at least one held-out relevant track appears in the top-10 recommended candidates.
- **NDCG@10**: Normalized Discounted Cumulative Gain at rank 10, measuring position-discounted ranking quality of held-out test tracks.

---

## 2. Simulated Listeners Evaluation Framework
- **Cohort Size**: **200 simulated listeners**.
- **Listener Profile Construction**:
  - Each simulated listener profile is constructed from **10 tracks** that share one specific genre tag in the training split.
  - **Held-Out Test Set**: **3 held-out test tracks** originating from that same genre are reserved as the ground-truth relevance target for each simulated listener.

---

## 3. Baseline Models (Must Beat Both)
The Moodwave recommender engine must quantitatively outperform both established baseline approaches on Hit@10 and NDCG@10:
1. **Baseline A: Global Popularity**: Recommends the top-10 overall most frequent/tagged tracks across the entire training catalog, irrespective of prompt or listener history.
2. **Baseline B: Genre Match Only**: Randomly or popularity-samples 10 tracks matching the primary genre tag without semantic ID prefix structure, mood conditioning, or energy alignment.

---

## 4. Intent Parsing Evaluation
- **Benchmark Dataset**: **60 hand-labelled natural language queries** reflecting realistic student scenarios (e.g., late-night studying, pre-exam anxiety, morning transit, deep sleep).
- **Evaluation Criteria**: Ground-truth accuracy across 3 structured dimensions:
  1. **Mood Accuracy**: Exact or semantic equivalence of extracted mood label.
  2. **Energy Band Accuracy**: Correct classification into low, medium, or high energy.
  3. **Context Accuracy**: Correct identification of user activity context (study, sleep, commute, etc.).

---

## 5. Latency Targets
All measurements taken at 95th percentile (p95) under simulated local network conditions:
- **/v1/recommend (Rules Fallback Path)**: **p95 < 300 ms**.
- **/v1/recommend (LLM Path)**: **p95 < 2.0 s**.

---

## 6. Evaluation Limitations & Proxy Disclosure
The simulated-listener evaluation protocol is an offline **proxy** for genuine user satisfaction and real-world acoustic coherence. Because human music appreciation involves subjective and multisensory factors that synthetic listener profiles cannot fully capture, this limitation will be explicitly acknowledged and highlighted in the hackathon presentation pitch deck.

---
Locked on November 4, 2026. Do not change these numbers after this point.

---

## Amendment 1
*Date: November 4, 2026*

The intent accuracy check uses the fields moods, genres and context from `/docs/INTENT_LABELS.csv`, because the MTG-Jamendo dataset has no energy, valence or tempo values. The energy_band field is removed from the evaluation. No other frozen value changed.

Additionally, the popularity baseline uses the proxy defined in `DATASET.md` (tag counts), since the dataset has no play counts.
