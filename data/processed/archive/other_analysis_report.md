# OTHER CATEGORY DEEP ANALYSIS REPORT

## Executive Summary

Analysis of 2,700 AmazonHelp conversations reveals:
- **1,163 OTHER conversations** (43.1%) — significantly higher than the 38.4% previously estimated
- **636 multi-intent conversations** (41.4% of classified)
- **CRITICAL FINDING**: A large portion of OTHER (73.4%) represents conversations that genuinely don't match any existing intent

---

## PART 1: OTHER CATEGORY BREAKDOWN

### Theme Distribution in OTHER (1,163 conversations)

| Theme | Count | % of OTHER | Classification |
|-------|-------|------------|---------------|
| NO_THEME_MATCH | 854 | 73.4% | NOISE/MISCELLANEOUS |
| PRIME_ISSUES | 176 | 15.1% | MODIFIER (but treated as primary issue by customers) |
| CASUAL_ORDER_STATUS | 80 | 6.9% | EXISTING_INTENT (ORDER_STATUS - missed) |
| DELIVERY_CASUAL | 40 | 3.4% | EXISTING_INTENT (DELIVERY_LATE/MISSING - missed) |
| HOW_TO_QUESTIONS | 26 | 2.2% | NEW_INTENT_CANDIDATE |
| APP_NAVIGATION | 18 | 1.5% | EXISTING_INTENT (APP_USAGE - missed) |
| ADDRESS_ISSUE | 6 | 0.5% | EXISTING_INTENT (DELIVERY - missed) |
| REFUND_TIMELINE | 5 | 0.4% | EXISTING_INTENT (REFUND_REQUEST - missed) |
| SUBSCRIPTION | 5 | 0.4% | MODIFIER |

### Top Words in OTHER (revealing non-English content)

The word frequency analysis reveals significant multilingual content:

```
que: 317 (French)
est: 112 (French)
pas: 94 (French)
vous: 87 (French)
pour: 66 (French)
por: 82 (Spanish)
pedido: 49 (Spanish)
ich: 63 (German)
nicht: 46 (German)
```

**Key insight**: ~30% of OTHER conversations are in non-English languages (French, Spanish, German, Hindi, Portuguese). These cannot be classified by English keyword matching.

### Top Bigrams in OTHER

```
customer service: 59
amazon prime: 33
from amazon: 32
what the: 31
thank you: 30
amazon logistics: 28
for prime: 27
was supposed: 24
day delivery: 23
worst service: 13
prime membership: 12
```

---

## PART 2: MAJOR THEMES ANALYSIS

### THEME 1: NO_THEME_MATCH (854 conversations, 73.4%)

**Classification**: NOISE_OR_MISCELLANEOUS

**Analysis**: This large group contains conversations that don't match any of the 15 taxonomy intents via keyword matching. Investigation shows:

1. **Non-English conversations** (~30%): French, Spanish, German, Hindi, Portuguese, etc.
2. **Very short/vague messages** (~20%): "help", "please", "thanks"
3. **AmazonHelp responses captured** (~15%): Customer quoting AmazonHelp tweets
4. **Truly unclassifiable** (~35%): Conversations too short or vague to determine intent

**Recommendation**: Accept ~5-7% of total as irreducible noise. Non-English needs separate handling.

---

### THEME 2: PRIME_ISSUES (176 conversations, 15.1%)

**Classification**: MODIFIER (but customers treat as PRIMARY)

**Representative Examples**:

1. `amazonhelp_113358`: "can someone tell me why falling skies was available for free with amazon prime as of yesterday... but now it's charging me to watch?"
2. `amazonhelp_143894`: "so this is how my pop turned up from @Amazon... im a long term prime member and this is how my stuff arrives. this is disgusting"
3. `amazonhelp_022747`: "@AmazonPay why am i paying for 2 day shipping if it's guaranteed to take 4 days to get here?! wtf, prime is turning into a waste of money"
4. `amazonhelp_063279`: "it's unbelievable that the amazon prime student program last 4 years and you can't cancel it"

**What customers actually want**:
- Prime benefits not working as expected
- Dissatisfaction with Prime delivery promises
- Prime membership billing/cancellation issues
- Feeling cheated by Prime commitments

**Existing Intent Coverage**:
- Most map to DELIVERY_LATE (Prime promised 2-day, didn't deliver)
- Some map to REFUND_REQUEST (want Prime refund)
- Some map to ACCOUNT_OTHER (Prime membership management)

**Problem**: PRIME_CUSTOMER is currently a MODIFIER, not an intent. But for these 176 conversations, Prime IS the primary complaint.

**Recommendation**: Keep as MODIFIER but ensure it doesn't override the underlying issue. Don't create PRIME_ISSUE as separate intent — most map to existing intents.

---

### THEME 3: CASUAL_ORDER_STATUS (80 conversations, 6.9%)

**Classification**: EXISTING_INTENT (ORDER_STATUS — missed by strict keywords)

**Representative Examples**:

1. `amazonhelp_026129`: "my order was suppose to be delivered today. but till now there is no update where my order is!"
2. `amazonhelp_070390`: "@AmazonHelp had ordered honor 8 pro... but received a marble piece in the box"
3. `amazonhelp_133594`: "@AmazonPay i have purchased... and received 3 soap in packet... what is the update???"

**Why Missed**: ORDER_STATUS keywords are: "order status", "where is my order", "when will my order", "order number"

These conversations use:
- "where is my order" → matches ORDER_STATUS ✓
- "no update where my order is" → doesn't match (missing "update")
- "what is the update" → doesn't match (missing order context)
- "status of delivery" → doesn't match (delivery, not order)

**Recommendation**: Expand ORDER_STATUS keywords to include:
- "update", "any update", "no update"
- "what's the status"
- "status"

---

### THEME 4: DELIVERY_CASUAL (40 conversations, 3.4%)

**Classification**: EXISTING_INTENT (DELIVERY_LATE or DELIVERY_MISSING — missed)

**Representative Examples**:

1. `amazonhelp_145117`: "just got screwed by @Amazon again... cancelled two orders on me, now both unavailable"
2. `amazonhelp_007191`: "i have buy oneplus3t... it more then 2 month but till now cash back"
3. `amazonhelp_117726`: "@AmazonHelp when will you deliver my product. i am waiting for it from past 2 weeks"

**Why Missed**: DELIVERY keywords miss informal delivery language:
- "waiting for" → not in keywords
- "haven't received" → not in keywords
- "still waiting" → not in keywords
- "nothing arrived" → not in keywords

**Recommendation**: Expand DELIVERY_LATE keywords to include:
- "waiting", "still waiting", "waiting for"
- "haven't received", "havent received"
- "never got", "never received"
- "nothing arrived", "nothing came"

---

### THEME 5: HOW_TO_QUESTIONS (26 conversations, 2.2%)

**Classification**: NEW_INTENT_CANDIDATE (GENERAL_INQUIRY)

**Representative Examples**:

1. `amazonhelp_072125`: "do y'all deliver on sundays or nah?"
2. `amazonhelp_019134`: "@AmazonHelp if you buy an echo plus do you no longer need the Phillips home hub to control lights?"

**Analysis**: These are information requests, not problem reports. The customer is asking HOW TO do something, not reporting a problem.

**Current Taxonomy Gap**: All 15 intents assume the customer has a PROBLEM. None handle general inquiries.

**Recommendation**: Consider adding GENERAL_INQUIRY as 16th intent for "how to" questions that don't map to problems. However, volume is low (26 = 2.2% of OTHER, 1% of total).

---

### THEME 6: APP_NAVIGATION (18 conversations, 1.5%)

**Classification**: EXISTING_INTENT (APP_USAGE — missed)

**Representative Examples**:

1. `amazonhelp_144745`: "done with all my formalities and provided all information. looking for my product soon!!"
2. `amazonhelp_094660`: "i don't know why my mobile number was blocked. please help!"

**Why Missed**: APP_USAGE keywords are "app", "website", "not working", "error", "page". These don't capture:
- "looking for"
- "can't find"
- "where is"

**Recommendation**: Expand APP_USAGE keywords to include:
- "can't find", "cant find"
- "where is"
- "looking for"
- "search"

---

## PART 3: MULTI-INTENT ANALYSIS

### Top 15 Intent Pairs

| Rank | Intent Pair | Count |
|------|-------------|-------|
| 1 | APP_USAGE + DELIVERY_LATE | 142 |
| 2 | REFUND_REQUEST + RETURN_REQUEST | 76 |
| 3 | APP_USAGE + RETURN_REQUEST | 73 |
| 4 | APP_USAGE + REFUND_REQUEST | 71 |
| 5 | APP_USAGE + DEVICE_ISSUE | 61 |
| 6 | DELIVERY_LATE + REFUND_REQUEST | 61 |
| 7 | DELIVERY_LATE + DELIVERY_TRACKING | 54 |
| 8 | DELIVERY_LATE + RETURN_REQUEST | 51 |
| 9 | DELIVERY_CARRIER + DELIVERY_LATE | 43 |
| 10 | ACCOUNT_ACCESS + APP_USAGE | 36 |
| 11 | APP_USAGE + DELIVERY_TRACKING | 36 |
| 12 | APP_USAGE + DELIVERY_CARRIER | 34 |
| 13 | PRODUCT_ISSUE + RETURN_REQUEST | 27 |
| 14 | DELIVERY_CARRIER + DELIVERY_TRACKING | 25 |
| 15 | APP_USAGE + PAYMENT_ISSUE | 24 |

### Primary Intent Selection Rule (DETERMINISTIC)

Based on analysis of 50 multi-intent examples:

**RULE**: "Customer's UNRESOLVED GOAL is primary"

1. **Explicit request > Implicit complaint**: If customer explicitly asks for something ("I want a refund"), that's primary
2. **Problem > Context**: A problem report beats context mention
3. **Specific > General**: "DELIVERY_MISSING" beats "APP_USAGE" when both present
4. **Unresolved > Resolved**: If Amazon already resolved one issue, the unresolved one is primary

**Practical Priority Order**:
```
PRIORITY 1: RETURN_REQUEST (customer wants action: return/replace)
PRIORITY 2: REFUND_REQUEST (customer wants money back)
PRIORITY 3: DELIVERY_MISSING > DELIVERY_LATE > DELIVERY_TRACKING
PRIORITY 4: PRODUCT_ISSUE (if product defect mentioned)
PRIORITY 5: APP_USAGE / DEVICE_ISSUE / VIDEO_STREAMING
PRIORITY 6: ORDER_STATUS / ORDER_MODIFY
PRIORITY 7: ACCOUNT_ACCESS
PRIORITY 8 (ALWAYS SECONDARY): Escalation signals
```

**Example Decisions**:

| Conversation | Intents | Primary | Reason |
|-------------|---------|---------|--------|
| APP_USAGE + DELIVERY_LATE | "can't track order on app" | DELIVERY_LATE | Delivery is the problem; app is how they're trying to check |
| APP_USAGE + REFUND_REQUEST | "app won't let me request refund" | REFUND_REQUEST | Customer's goal is refund; app is obstacle |
| REFUND_REQUEST + RETURN_REQUEST | "want to return and get money back" | RETURN_REQUEST | Return is the action; refund follows |

---

## PART 4: ESCALATION SIGNALS ANALYSIS

### Signal Distribution

From the stress test data:
- FRUSTRATION_HIGH: 217
- PREVIOUS_CONTACT: 111
- SERVICE_COMPLAINT: 101
- ESCALATION_REQUEST: 52

**Total**: 481 conversations (17.8% of all conversations)

### Key Finding: Signals Are Often SECONDARY

Example from multi-intent sample:
```
amazonhelp_044450:
- Intents: DELIVERY_LATE, APP_USAGE, DEVICE_ISSUE, ACCOUNT_ACCESS
- Signals: SERVICE_COMPLAINT
- PRIMARY: DELIVERY_LATE (unresolved late delivery)
- SECONDARY: SERVICE_COMPLAINT (frustration about poor service)
```

**Recommendation**: Signals should ALWAYS be extracted as secondary intents, never as primary. The primary intent is the actual problem; the signal indicates priority/urgency.

---

## PART 5: MODIFIER ANALYSIS

### Current Modifiers

| Modifier | Recommendation | Evidence |
|----------|----------------|----------|
| PRIME_CUSTOMER | KEEP as modifier | 176 OTHER conversations are Prime-related, but most map to existing intents (delivery, refund) |
| MARKETPLACE | KEEP as modifier | Low volume (5-10%), useful for routing |
| CARRIER | DEMOTE to context | 82 primary vs 145 context — carrier is almost always context |

### CARRIER Specific Analysis

The stress test showed:
- DELIVERY_CARRIER as PRIMARY: 82 conversations
- DELIVERY_CARRIER as CONTEXT: 145 conversations

**Recommendation**: CARRIER should be a MODIFIER, not a leaf intent. Change:
- DELIVERY_CARRIER → add "carrier" as context keyword to DELIVERY_* intents
- Remove DELIVERY_CARRIER from primary intents

---

## PART 6: EXISTING INTENT RULE CHANGES NEEDED

### 1. ORDER_STATUS — Expand Keywords

**Current**: "order status", "where is my order", "when will my order", "order number"

**Missing patterns**:
- "any update", "no update", "update"
- "what's the status"
- "status"

**Fix**: Add "update", "status" to ORDER_STATUS keywords

---

### 2. DELIVERY_LATE — Expand Keywords

**Current**: "late", "delayed", "eta", "expected delivery", "not arrived yet", "still waiting"

**Missing patterns**:
- "waiting for", "still waiting"
- "haven't received", "never received"
- "nothing arrived"

**Fix**: Add "waiting", "haven't received", "never received", "nothing arrived" to DELIVERY_LATE

---

### 3. APP_USAGE — Expand Keywords

**Current**: "app", "website", "not working", "error", "page"

**Missing patterns**:
- "can't find", "where is"
- "looking for"

**Fix**: Add "can't find", "where is", "looking for" to APP_USAGE

---

### 4. DELIVERY_CARRIER — Remove or Demote

**Current**: 14-leaf taxonomy with DELIVERY_CARRIER as separate intent

**Evidence**: 145 context vs 82 primary

**Fix**: Remove from primary intents; add "carrier" as context keyword to DELIVERY_* intents

---

## PART 7: FINAL OTHER ANALYSIS SUMMARY

### 1. Original OTHER Count
**1,163 conversations (43.1% of 2,700)**

### 2. Number of Major Themes Discovered
**9 distinct themes** (plus 1 UNCATEGORIZED)

### 3. Top 10 OTHER Themes

| Rank | Theme | Count | % OTHER |
|------|-------|-------|---------|
| 1 | NO_THEME_MATCH (noise/non-English) | 854 | 73.4% |
| 2 | PRIME_ISSUES | 176 | 15.1% |
| 3 | CASUAL_ORDER_STATUS | 80 | 6.9% |
| 4 | DELIVERY_CASUAL | 40 | 3.4% |
| 5 | HOW_TO_QUESTIONS | 26 | 2.2% |
| 6 | APP_NAVIGATION | 18 | 1.5% |
| 7 | ADDRESS_ISSUE | 6 | 0.5% |
| 8 | REFUND_TIMELINE | 5 | 0.4% |
| 9 | SUBSCRIPTION | 5 | 0.4% |

### 4. Themes Mapping to Existing Intents

| Theme | Maps to Existing | Count | Fix Needed |
|-------|-----------------|-------|------------|
| CASUAL_ORDER_STATUS | ORDER_STATUS | 80 | Expand keywords |
| DELIVERY_CASUAL | DELIVERY_LATE/MISSING | 40 | Expand keywords |
| APP_NAVIGATION | APP_USAGE | 18 | Expand keywords |
| ADDRESS_ISSUE | DELIVERY | 6 | Add "wrong address" |
| REFUND_TIMELINE | REFUND_REQUEST | 5 | Expand keywords |

**Total recoverable**: 149 conversations (12.8% of OTHER)

### 5. Genuinely Missing Intents

| Candidate | Count | Justification |
|-----------|-------|---------------|
| GENERAL_INQUIRY | 26 | "How to" questions that aren't problems |
| DELIVERY_ADDRESS | 6 | Wrong/change address issues |

**Recommendation**: Do NOT create new intents for <10 conversations. Add keywords to existing intents instead.

### 6. Themes Classified as MODIFIERS

| Theme | Treatment | Count |
|-------|-----------|-------|
| PRIME_ISSUES | Keep as PRIME_CUSTOMER modifier | 176 |
| SUBSCRIPTION | Keep as context | 5 |

### 7. Themes Classified as ESCALATION SIGNALS

| Signal | Count | Treatment |
|--------|-------|-----------|
| FRUSTRATION_HIGH | 217 | Always secondary |
| PREVIOUS_CONTACT | 111 | Always secondary |
| SERVICE_COMPLAINT | 101 | Always secondary |
| ESCALATION_REQUEST | 52 | Always secondary |

**Total**: 481 conversations where signals are present

### 8. Themes Classified as NOISE/MISCELLANEOUS

| Category | Count | % OTHER |
|----------|-------|---------|
| NO_THEME_MATCH | 854 | 73.4% |
| - Non-English (est.) | ~350 | 30.1% |
| - Too short/vague (est.) | ~170 | 14.6% |
| - AmazonHelp responses (est.) | ~130 | 11.2% |
| - Truly unclassifiable (est.) | ~200 | 17.2% |

### 9. Estimated Remaining OTHER Percentage

| Source | Current | After Fixes |
|--------|---------|-------------|
| Keyword gaps (recoverable) | ~149 | ~20 |
| Non-English | ~350 | ~350 |
| Noise/unclassifiable | ~200 | ~150 |
| **TOTAL OTHER** | **1,163 (43%)** | **~520 (19%)** |

**Realistic floor with English-only**: 7-10%
**Realistic floor including all languages**: 19-22%

### 10. Most Common Multi-Intent Combinations

| Rank | Combination | Count |
|------|-------------|-------|
| 1 | APP_USAGE + DELIVERY_LATE | 142 |
| 2 | REFUND_REQUEST + RETURN_REQUEST | 76 |
| 3 | APP_USAGE + RETURN_REQUEST | 73 |
| 4 | APP_USAGE + REFUND_REQUEST | 71 |
| 5 | APP_USAGE + DEVICE_ISSUE | 61 |
| 6 | DELIVERY_LATE + REFUND_REQUEST | 61 |
| 7 | DELIVERY_LATE + DELIVERY_TRACKING | 54 |
| 8 | DELIVERY_LATE + RETURN_REQUEST | 51 |
| 9 | DELIVERY_CARRIER + DELIVERY_LATE | 43 |
| 10 | ACCOUNT_ACCESS + APP_USAGE | 36 |

### 11. Recommended Primary-Intent Selection Rule

**"Customer's Unresolved Goal is Primary"**

```
PRIORITY ORDER (highest to lowest):
1. RETURN_REQUEST (customer wants to return/exchange)
2. REFUND_REQUEST (customer wants money back)
3. DELIVERY_MISSING (package never arrived)
4. DELIVERY_LATE (package is late)
5. DELIVERY_TRACKING (tracking issue)
6. PRODUCT_ISSUE (product defect)
7. PAYMENT_ISSUE (payment problem)
8. APP_USAGE / DEVICE_ISSUE / VIDEO_STREAMING
9. ORDER_STATUS / ORDER_MODIFY
10. ACCOUNT_ACCESS

ALWAYS SECONDARY (extract but don't use as primary):
- FRUSTRATION_HIGH
- PREVIOUS_CONTACT
- SERVICE_COMPLAINT
- ESCALATION_REQUEST
```

### 12. Biggest Taxonomy Risks

**RISK 1: Non-English Content (30% of OTHER)**
- ~350 conversations in French, Spanish, German, Hindi, Portuguese
- Cannot be classified by English keyword matching
- **Mitigation**: Need language detection as preprocessing step

**RISK 2: Multi-Intent Conversations (41% of classified)**
- 636 conversations have 2+ intents
- Single-label classification will always misclassify these
- **Mitigation**: Primary + secondary intent structure

**RISK 3: DELIVERY_CARRIER as Primary**
- 82 conversations have carrier as primary issue
- But 145 have carrier as context
- **Mitigation**: Demote to context modifier

**RISK 4: Escalation Signals as Primary**
- 481 conversations have escalation signals
- Treating signal as primary misclassifies the actual issue
- **Mitigation**: Always extract as secondary

**RISK 5: Prime as Modifier vs Intent**
- 176 conversations are Prime-related complaints
- But Prime is currently a modifier, not intent
- **Mitigation**: Keep as modifier, ensure rules don't override underlying issue

---

## RECOMMENDATIONS FOR FINAL TAXONOMY

### 1. Keyword Expansions (High Impact, Low Risk)

| Intent | Add Keywords | Recoverable |
|--------|-------------|-------------|
| ORDER_STATUS | "update", "status" | ~60 |
| DELIVERY_LATE | "waiting", "haven't received", "never received" | ~35 |
| APP_USAGE | "can't find", "where is", "looking for" | ~15 |
| REFUND_REQUEST | "when will i get", "how long", "pending" | ~5 |

### 2. Intent Mergers (Based on Stress Test)

| From | To | Evidence |
|------|-----|----------|
| DELIVERY_CARRIER | DELIVERY (modifier) | 145 context vs 82 primary |
| ACCOUNT_ACCESS | APP_USAGE | 36 overlap |
| PRODUCT_ISSUE | RETURN_REQUEST | 27 overlap |
| VIDEO_STREAMING | DEVICE_ISSUE | Low volume |
| PAYMENT_ISSUE | REFUND_REQUEST | 22 overlap |

### 3. Structure Changes

| Change | Rationale |
|--------|-----------|
| Add "GENERAL_INQUIRY" intent? | NO — volume too low (26), most map to existing |
| Add "PRIME_ISSUE" intent? | NO — keep as modifier, most map to existing |
| Make signals secondary intents | YES — always extract, never primary |

### 4. Expected Coverage After Fixes

| Metric | Before | After |
|--------|--------|-------|
| OTHER rate | 43.1% | ~19-22% |
| Classified rate | 56.9% | ~78-81% |
| Multi-intent handling | None | Primary + secondary |

---

## FILES GENERATED

1. `data/processed/other_theme_counts.json` — Theme counts and word frequencies
2. `data/processed/multi_intent_combinations.json` — Intent pair analysis
3. `data/samples/other_representative_examples.json` — Example conversations per theme
4. `data/samples/multi_intent_sample.json` — 50 multi-intent examples
5. `data/processed/other_analysis_report.md` — This report