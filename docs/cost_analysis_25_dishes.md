# Cost Analysis: 25 Dishes per Menu Scan

## 1. Per-Scan Cost Breakdown (25 dishes)

### OCR / Vision (1 call per menu image)

| Step | Provider | Model | Input | Cost |
|------|----------|-------|-------|------|
| Primary OCR | Tesseract (local) | — | 1 image | **$0.000** |
| Fallback OCR | Gemini 2.5-flash | gemini-2.5-flash | ~1 image (~500 KB) | **$0.0001** |
| Emergency fallback | OpenRouter Qwen 2.5 VL | qwen-2.5-vl-72b | ~1 image | **$0.008** |

> **Typical OCR cost per scan: $0.00 – $0.0001**
> (Tesseract succeeds ~80% of the time; Gemini free tier covers the rest.)

---

### LLM Enrichment (per dish × 25 dishes)

Each dish gets enriched with: ingredients, taste profile, dietary classification, allergen flags, similar dishes.

| Step | Provider | Model | Tokens/dish | Cost/dish | Cost × 25 |
|------|----------|-------|-------------|-----------|-----------|
| **Primary** | Ollama (local) | qwen3:8b | ~800 in + 400 out | **$0.000** | **$0.000** |
| **Alt 1** | Groq (free tier) | qwen3-32b | ~800 in + 400 out | **$0.000** | **$0.000** |
| **Alt 2** | Groq (paid) | llama-3.3-70b | ~800 in + 400 out | **$0.0003** | **$0.0075** |
| **Alt 3** | Kilocode | qwen3-235b | ~800 in + 400 out | **$0.0008** | **$0.020** |
| **Fallback** | OpenAI | gpt-4o-mini | ~800 in + 400 out | **$0.0004** | **$0.010** |
| **Emergency** | OpenAI | gpt-4o | ~800 in + 400 out | **$0.005** | **$0.125** |

> **Typical enrichment cost for 25 dishes: $0.00** (Ollama local or Groq free tier)
> **Worst-case enrichment (GPT-4o): $0.125**

---

### Translation (if needed, per dish)

| Provider | Model | Tokens/dish | Cost/dish | Cost × 25 |
|----------|-------|-------------|-----------|-----------|
| **Cached** (DB hit) | — | 0 | $0.000 | **$0.000** |
| Groq (free) | qwen3-32b | ~200 | $0.000 | **$0.000** |
| Gemini | gemini-2.5-flash | ~200 | $0.00003 | **$0.0008** |

> **Typical translation cost: $0.00** (cache hit or free tier)

---

### Storage & Infrastructure (per scan)

| Service | Operation | Cost |
|---------|-----------|------|
| Cloudflare R2 | Store 1 image (~500 KB) | **$0.000015** |
| Supabase PostgreSQL | Write 25 dishes + metadata | **Included in plan** |
| Cloudflare Workers | 1 invocation (~50 ms) | **$0.0000005** |

---

### Total Cost per Scan (25 dishes)

| Scenario | OCR | Enrichment | Translation | Storage | **Total** |
|----------|-----|-----------|-------------|---------|-----------|
| **Best case** (Ollama + Tesseract) | $0.000 | $0.000 | $0.000 | $0.00002 | **$0.00002** |
| **Typical** (Gemini OCR + Groq free) | $0.0001 | $0.000 | $0.000 | $0.00002 | **$0.00012** |
| **Paid LLM** (Groq paid) | $0.0001 | $0.008 | $0.001 | $0.00002 | **$0.009** |
| **Worst case** (GPT-4o fallback) | $0.008 | $0.125 | $0.001 | $0.00002 | **$0.134** |

---

## 2. Monthly Infrastructure Costs (Fixed)

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Supabase | Free → Pro | $0 – $25 |
| Cloudflare Workers | Free (100K req/day) | $0 – $5 |
| Cloudflare R2 | 10 GB free | $0 – $5 |
| Ollama hosting (self-hosted Mac/GPU) | Local | $0 (electricity only) |
| Ollama hosting (cloud GPU) | A10G/T4 | $50 – $200 |
| Stripe | Per-transaction only | $0 fixed |
| Domain / DNS | Cloudflare | $10 – $15/year |

| **Infrastructure tier** | **Monthly fixed** |
|--------------------------|-------------------|
| **Bootstrapping** (all free tiers, local Ollama) | **~$0 – $5** |
| **Growth** (Supabase Pro, local Ollama) | **~$30 – $50** |
| **Scale** (Supabase Pro, cloud GPU) | **~$100 – $275** |

---

## 3. Revenue Model

### Subscription Plans (from schema)

| Plan | Monthly | Yearly | Scan Limit | Net Revenue (after Stripe 2.9%+$0.30) |
|------|---------|--------|------------|----------------------------------------|
| **Free** | $0.00 | — | 3 scans/mo | $0.00 |
| **Pro** | $4.99 | $39.99/yr ($3.33/mo) | Unlimited | $4.55/mo (monthly) · $38.53/yr |
| **Max** | $9.99 | $79.99/yr ($6.67/mo) | Unlimited | $9.40/mo (monthly) · $77.67/yr |

---

## 4. Unit Economics: Cost vs Revenue

### Assumptions
- Average Pro user: **15 scans/month** (25 dishes each = 375 dishes)
- Average Max user: **30 scans/month** (25 dishes each = 750 dishes)
- Free user: 3 scans/month

### Per-User Margin (Typical scenario — Ollama/Groq free)

| Plan | Monthly Revenue (net) | Variable Cost (scans) | **Gross Margin** | **Margin %** |
|------|----------------------|-----------------------|-------------------|-------------|
| **Free** | $0.00 | 3 × $0.00012 = $0.0004 | **−$0.0004** | — |
| **Pro** (monthly) | $4.55 | 15 × $0.00012 = $0.002 | **+$4.55** | **99.96%** |
| **Pro** (yearly) | $3.21/mo | 15 × $0.00012 = $0.002 | **+$3.21** | **99.94%** |
| **Max** (monthly) | $9.40 | 30 × $0.00012 = $0.004 | **+$9.40** | **99.96%** |
| **Max** (yearly) | $6.47/mo | 30 × $0.00012 = $0.004 | **+$6.47** | **99.94%** |

### Per-User Margin (Worst case — GPT-4o fallbacks)

| Plan | Monthly Revenue (net) | Variable Cost (scans) | **Gross Margin** | **Margin %** |
|------|----------------------|-----------------------|-------------------|-------------|
| **Free** | $0.00 | 3 × $0.134 = $0.40 | **−$0.40** | — |
| **Pro** (monthly) | $4.55 | 15 × $0.134 = $2.01 | **+$2.54** | **55.8%** |
| **Max** (monthly) | $9.40 | 30 × $0.134 = $4.02 | **+$5.38** | **57.2%** |

---

## 5. Breakeven Analysis

### How many paying users to cover infrastructure?

| Infrastructure Tier | Fixed Cost/mo | Pro Users Needed | Max Users Needed |
|--------------------|---------------|-----------------|-----------------|
| **Bootstrapping** ($5/mo) | $5 | **2 Pro** | **1 Max** |
| **Growth** ($50/mo) | $50 | **11 Pro** | **6 Max** |
| **Scale** ($275/mo) | $275 | **61 Pro** | **30 Max** |

---

## 6. Scaling Projections (1K, 10K, 100K scans/month)

| Metric | 1K scans | 10K scans | 100K scans |
|--------|----------|-----------|------------|
| Dishes processed | 25,000 | 250,000 | 2,500,000 |
| **Variable cost (typical)** | $0.12 | $1.20 | $12.00 |
| **Variable cost (paid LLM)** | $9.00 | $90.00 | $900.00 |
| **Variable cost (worst)** | $134.00 | $1,340.00 | $13,400.00 |
| Infrastructure | $5 – $50 | $50 – $275 | $275 – $1,000 |
| **Total cost** | **$5 – $184** | **$51 – $1,615** | **$287 – $14,400** |
| Est. paying users (10% conv.) | ~7 Pro | ~67 Pro | ~667 Pro |
| Est. revenue | $32/mo | $305/mo | $3,035/mo |

---

## 7. Cost Optimization Strategies

| Strategy | Impact | Status |
|----------|--------|--------|
| **Ollama local inference** | Eliminates LLM cost entirely | ✅ Implemented |
| **Groq free tier** | Free ~6K requests/day | ✅ Implemented |
| **Gemini free tier** | Free OCR up to 1,500 req/day | ✅ Implemented |
| **Translation caching** | Avoid re-translating known dishes | ✅ Implemented |
| **Batch enrichment** | Process 25–50 dishes per LLM call | ✅ Implemented |
| **Web-only subscriptions** | Avoids 30% App Store tax | ✅ Implemented |
| **Result caching** (menu dedup) | Skip re-processing same menus | ✅ Implemented |
| **Tiered fallbacks** | Free → cheap → expensive providers | ✅ Implemented |

---

## 8. Key Takeaways

1. **Near-zero marginal cost**: With Ollama + free-tier APIs, each 25-dish scan costs ~$0.00012. Even at 100K scans/month, variable costs stay under $12.

2. **Massive gross margins**: Pro plan yields ~99.9% margin in typical scenario, ~56% even in worst case (all GPT-4o fallbacks).

3. **Breakeven is trivially low**: Just 2 Pro subscribers cover bootstrapping costs. 11 Pro users cover growth infrastructure.

4. **The real cost is infrastructure, not LLM**: At scale, Supabase ($25–$100) and cloud GPU hosting ($50–$200) dominate, not per-call API fees.

5. **Avoid App Store commissions**: Web-only Stripe billing saves 30% vs in-app purchases, adding ~$1.50/mo per Pro user to margin.

6. **Risk: fallback cascades**: If Ollama/Groq go down, GPT-4o fallbacks cost 1,000× more. Monitor fallback rates closely.
