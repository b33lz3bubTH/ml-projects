# 📘 Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose

The purpose of this system is to **detect market manipulation, unfair advantage, and anomalous behavior** in digital marketplaces by modeling **user–product–action flows as a Markov system** and identifying **deviations from natural equilibrium (stationary distribution)**.

The system is **unsupervised**, explainable, and designed to work without labeled fraud data.

---

### 1.2 Scope

The system will:

* Ingest **interaction logs** (views, clicks, carts, purchases, etc.)
* Build a **Markov transition graph**
* Compute **stationary distributions**
* Detect **flow imbalances and perturbation sensitivity**
* Output **risk scores** and **explainable alerts**

The system **does NOT**:

* Predict prices
* Recommend products
* Use NLP or user text
* Require supervised ML labels

---

### 1.3 Target Users

* Marketplace trust & safety teams
* E-commerce platform engineers
* Fraud analytics teams
* Research / platform integrity teams

---

## 2. System Overview (High-Level)

### Core Idea (One Diagram in Words)

```
User Actions → Transition Matrix → Stationary Distribution
                          ↓
                  Flow & Stability Analysis
                          ↓
                 Manipulation / Fairness Alerts
```

You are not predicting behavior —
you are detecting **structural imbalance**.

---

## 3. Functional Requirements

### 3.1 Data Ingestion

The system must ingest event-level logs with the following minimum schema:

| Field       | Description                           |
| ----------- | ------------------------------------- |
| event_id    | Unique identifier                     |
| timestamp   | Event time                            |
| user_id     | Anonymized user ID                    |
| entity_id   | Product / seller / listing ID         |
| action_type | view / click / cart / purchase / exit |
| session_id  | Session identifier                    |

Optional (but powerful later):

* device_id
* geo_bucket
* seller_id
* referral_source

---

### 3.2 State Construction

The system must construct **Markov states** using one of the following configurable strategies:

1. `(entity_id, action_type)`
2. `(seller_id, action_type)`
3. `(action_type only)` (baseline)
4. `(entity_id, action_type, session_stage)`

> ⚠️ State definition is a **design lever** — changing it changes what manipulation you can see.

---

### 3.3 Transition Matrix Generation

* Build a **sparse transition matrix P**
* Each entry `P[i][j]` represents probability of transitioning from state `i` → `j`
* Normalize outgoing probabilities

---

### 3.4 Stationary Distribution Computation

The system must:

* Compute stationary distribution `π` such that:

  ```
  πP = π
  ```
* Use **power iteration**
* Support:

  * convergence threshold
  * max iterations
  * damping (optional, PageRank-style)

---

### 3.5 Equilibrium & Flow Analysis

For each state `s`, compute:

* Incoming flow
* Outgoing flow
* Net imbalance
* Flow entropy

This identifies:

* Probability traps
* Artificial loops
* Sink states

---

### 3.6 Perturbation Analysis (Critical)

The system must support **counterfactual removal** of:

* A seller
* A product
* A group of users

Recompute `π'` and calculate:

* KL divergence: `KL(π || π')`
* Total variation distance
* Local impact radius

> Small removals causing large shifts = **manipulation signal**

---

### 3.7 Alerting & Scoring

The system must generate:

* Entity risk scores
* Seller/system health scores
* Time-based instability alerts

Each alert must include:

* Affected states
* Flow explanation
* Before/after distributions

---

## 4. Non-Functional Requirements

### Performance

* Handle millions of events/day
* Sparse matrix operations
* Incremental recomputation support (future)

### Explainability

* Every alert must be explainable via:

  * flow imbalance
  * stationary mass
  * perturbation sensitivity

### Extensibility

* Plug-in new state definitions
* Time-windowed Markov chains
* Streaming updates

---

## 5. Architecture (High-Level)

### Components

1. **Event Processor**
2. **State Builder**
3. **Transition Matrix Engine**
4. **Equilibrium Solver**
5. **Stability Analyzer**
6. **Alert Engine**
7. **Visualization / Reporting Layer**

---

## 6. Data Sources (You Can Use TODAY)

These are **perfect fits** for your project.

---

### 🔹 1. Kaggle – E-commerce Behavior Data

Search for:

* *“E-commerce user behavior dataset”*
* *“Online retail events dataset”*

Examples include:

* View → cart → purchase flows
* Session-based logs
* Anonymized user/product IDs

Why good:

* Clean
* Realistic funnels
* Easy state modeling

---

### 🔹 2. Alibaba / Tianchi User Behavior Dataset

Contains:

* user_id
* item_id
* action_type
* timestamp

Actions include:

* view
* favorite
* cart
* purchase

This dataset is **gold** for Markov modeling.

---

### 🔹 3. Retail Rocket Dataset

Publicly used in academic research.

Includes:

* View
* Add-to-cart
* Purchase
* Session info

Perfect for:

* Flow equilibrium
* Funnel distortion detection

---

### 🔹 4. Synthetic Injection (Important)

You *should* inject:

* Fake users
* Circular buying behavior
* Bot-like flows

This validates your detector **without labels**.

---

## 7. How You Transition to Your Own Data Later

Design your ingestion around this **canonical event schema**:

```json
{
  "timestamp": "...",
  "actor_id": "...",
  "entity_id": "...",
  "action": "...",
  "context": {...}
}
```

As long as your real data maps to this → system works unchanged.

That’s professional-grade design.

---


1. Design the **exact state definitions** for your first dataset
2. Walk through a **numerical toy example** (actual numbers)
4. Design the **attack simulations** (bots, wash trading, loops)


