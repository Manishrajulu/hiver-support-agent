#!/usr/bin/env python3
"""Create candidate taxonomy v3 based on stress test"""

import json

# ============================================
# TAXONOMY V3 RECOMMENDATIONS
# ============================================

# Based on stress test findings:

# FINDING 1: DELIVERY_CARRIER is usually context, not primary intent
#   - 82 primary vs 145 context
#   - RECOMMENDATION: Make DELIVERY_CARRIER a MODIFIER, not leaf intent

# FINDING 2: APP_USAGE and ACCOUNT_ACCESS overlap significantly (32)
#   - Login via app is still an app issue
#   - RECOMMENDATION: Merge ACCOUNT_ACCESS into APP_USAGE

# FINDING 3: PRODUCT_ISSUE and RETURN_REQUEST overlap (32)
#   - Product issue almost always leads to return
#   - RECOMMENDATION: Merge PRODUCT_ISSUE into RETURN_REQUEST

# FINDING 4: ORDER_MODIFY has only 9 examples (too rare)
#   - RECOMMENDATION: Merge ORDER_MODIFY into ORDER_STATUS (status inquiry includes modification intent)

# FINDING 5: OTHER is 38% - too high
#   - Need to improve coverage
#   - May need broader intent definitions

# FINDING 6: REFUND_REQUEST and PAYMENT_ISSUE overlap manageable (19)
#   - Keep separate but group under PAYMENT

taxonomy_v3 = {
    "version": "v3",
    "changes_from_v2": [
        "MERGED: DELIVERY_CARRIER -> DELIVERY (now modifier)",
        "MERGED: ACCOUNT_ACCESS -> APP_USAGE",
        "MERGED: PRODUCT_ISSUE -> RETURN_REQUEST",
        "MERGED: ORDER_MODIFY -> ORDER_STATUS",
        "RETAINED: DELIVERY_LATE, DELIVERY_MISSING, DELIVERY_TRACKING (4 delivery intents -> 3)",
        "RETAINED: VIDEO_STREAMING as separate (low overlap)"
    ],
    "top_level_categories": 5,
    "leaf_intents": 9,
    "coverage_estimate": "70-75% (improved from 60-65%)",
    "other_estimate": "25-30%",

    "primary_intents": [
        {
            "intent_id": "DELIVERY_LATE",
            "name": "Late Delivery",
            "definition": "Customer's package has not arrived by the expected delivery date or is delayed",
            "parent_category": "DELIVERY",
            "v2_leaf_intents_consolidated": ["DELIVERY_LATE", "DELIVERY_CARRIER"],
            "stress_test_notes": "Most common delivery issue. Carrier issues treated as context.",
            "keep": True
        },
        {
            "intent_id": "DELIVERY_MISSING",
            "name": "Missing/Not Delivered",
            "definition": "Customer never received package, shows delivered but not there, or package lost",
            "parent_category": "DELIVERY",
            "v2_leaf_intents_consolidated": ["DELIVERY_MISSING"],
            "stress_test_notes": "Distinct from late - requires different action path",
            "keep": True
        },
        {
            "intent_id": "DELIVERY_TRACKING",
            "name": "Tracking Issue",
            "definition": "Customer cannot track package, tracking info wrong/unclear, or needs tracking help",
            "parent_category": "DELIVERY",
            "v2_leaf_intents_consolidated": ["DELIVERY_TRACKING"],
            "stress_test_notes": "Distinct from status - troubleshooting focused",
            "keep": True
        },
        {
            "intent_id": "ORDER_STATUS",
            "name": "Order Inquiry/Modification",
            "definition": "Customer wants to know order status OR wants to modify/cancel order",
            "parent_category": "ORDER",
            "v2_leaf_intents_consolidated": ["ORDER_STATUS", "ORDER_MODIFY"],
            "stress_test_notes": "Merged due to low ORDER_MODIFY count (9 examples). Status inquiry and modification are related.",
            "keep": True
        },
        {
            "intent_id": "APP_TECHNICAL",
            "name": "App/Technical Issue",
            "definition": "Problem using Amazon app, website, or technical issue including login/access problems",
            "parent_category": "TECHNICAL",
            "v2_leaf_intents_consolidated": ["APP_USAGE", "ACCOUNT_ACCESS"],
            "stress_test_notes": "Merged due to high overlap (32). Login via app is still app issue.",
            "keep": True
        },
        {
            "intent_id": "DEVICE_ISSUE",
            "name": "Device Problem",
            "definition": "Issue with Amazon device (Kindle, Fire TV, Echo, Alexa) or video streaming on device",
            "parent_category": "TECHNICAL",
            "v2_leaf_intents_consolidated": ["DEVICE_ISSUE", "VIDEO_STREAMING"],
            "stress_test_notes": "Merged - VIDEO_STREAMING often involves specific device. Low overlap (10).",
            "keep": True
        },
        {
            "intent_id": "REFUND_REQUEST",
            "name": "Refund or Payment Issue",
            "definition": "Customer wants money back, has billing problem, or payment issue",
            "parent_category": "PAYMENT",
            "v2_leaf_intents_consolidated": ["REFUND_REQUEST", "PAYMENT_ISSUE"],
            "stress_test_notes": "Merged - high overlap (19) and related. Payment issues lead to refund.",
            "keep": True
        },
        {
            "intent_id": "RETURN_REQUEST",
            "name": "Return/Exchange/Product Issue",
            "definition": "Customer wants to return item, exchange, or has product quality issue (wrong, damaged, defective)",
            "parent_category": "RETURN_PRODUCT",
            "v2_leaf_intents_consolidated": ["RETURN_REQUEST", "PRODUCT_ISSUE"],
            "stress_test_notes": "Merged due to very high overlap (32). Product issue always leads to return.",
            "keep": True
        },
        {
            "intent_id": "ACCOUNT_OTHER",
            "name": "Account/Seller/Other",
            "definition": "Account issues not related to app/technical, seller issues, marketplace questions, or general inquiries",
            "parent_category": "OTHER",
            "v2_leaf_intents_consolidated": ["ACCOUNT_ACCESS"],  # Now catch-all
            "stress_test_notes": "Account issues that aren't APP_USAGE.",
            "keep": True
        }
    ],

    "context_modifiers": [
        {
            "modifier_id": "PRIME_CUSTOMER",
            "name": "Prime Customer",
            "definition": "Customer is a Prime member - affects delivery expectations",
            "usage": "Add as modifier/context",
            "frequency": "15-20%"
        },
        {
            "modifier_id": "MARKETPLACE",
            "name": "Marketplace/Region",
            "definition": "Customer using Amazon.in, Amazon.fr, Amazon.de, Amazon.uk, etc.",
            "usage": "Add as modifier/context for routing",
            "frequency": "10-15%"
        },
        {
            "modifier_id": "DELIVERY_CARRIER",
            "name": "Delivery Carrier Issue",
            "definition": "Issue specifically with delivery carrier (Gati, FedEx, etc.)",
            "usage": "Add as modifier to DELIVERY intents",
            "frequency": "5-10%",
            "notes": "Was separate leaf intent in v2, now demoted to modifier due to stress test"
        }
    ],

    "escalation_signals": [
        {
            "signal_id": "FRUSTRATION_HIGH",
            "name": "High Frustration",
            "definition": "Customer expresses anger, frustration, or strong negative emotion",
            "action": "Consider escalation to human",
            "frequency": "8%",
            "keywords": ["angry", "furious", "frustrated", "awful", "terrible", "worst", "pathetic"]
        },
        {
            "signal_id": "PREVIOUS_CONTACT",
            "name": "Previous Unresolved Contact",
            "definition": "Customer mentions contacting before with no resolution",
            "action": "Consider escalation priority",
            "frequency": "4%",
            "keywords": ["already contacted", "already called", "spoken to", "multiple times", "days ago"]
        },
        {
            "signal_id": "ESCALATION_REQUEST",
            "name": "Escalation Request",
            "definition": "Customer explicitly asks for manager, supervisor, or callback",
            "action": "Escalate to human",
            "frequency": "2%",
            "keywords": ["manager", "supervisor", "escalate", "call me back", "callback"]
        },
        {
            "signal_id": "SERVICE_COMPLAINT",
            "name": "Service Quality Complaint",
            "definition": "Customer complains about Amazon service quality or rude behavior",
            "action": "Log for quality tracking, consider escalation",
            "frequency": "4%",
            "keywords": ["worst service", "bad service", "poor service", "rude", "no response"]
        }
    ],

    "proposed_hierarchy": """
PROPOSED HIERARCHY V3 (9 leaf intents):

TOP LEVEL (5 categories):
├── DELIVERY (35-40%)
│   ├── DELIVERY_LATE
│   ├── DELIVERY_MISSING
│   └── DELIVERY_TRACKING
├── ORDER (10-15%)
│   └── ORDER_STATUS (includes modification)
├── TECHNICAL (25-30%)
│   ├── APP_TECHNICAL (includes login/access)
│   └── DEVICE_ISSUE (includes video streaming)
├── PAYMENT (8-12%)
│   └── REFUND_REQUEST (includes payment issues)
└── RETURN_PRODUCT (6-10%)
    └── RETURN_REQUEST (includes product issues)

MODIFIERS: PRIME_CUSTOMER, MARKETPLACE, DELIVERY_CARRIER

SIGNALS: FRUSTRATION_HIGH, PREVIOUS_CONTACT, ESCALATION_REQUEST, SERVICE_COMPLAINT
""",

    "strict_labeling_rules": {
        "DELIVERY_LATE": {
            "inclusion": "Customer states package is late, delayed, or not arrived by expected date",
            "exclusion": "Package shows delivered but customer says not received -> DELIVERY_MISSING. Cannot track -> DELIVERY_TRACKING",
            "priority": "If 'late' AND 'tracking' both present, prefer DELIVERY_LATE"
        },
        "DELIVERY_MISSING": {
            "inclusion": "Customer says package shows delivered but not received, never received, or is lost",
            "exclusion": "Package is simply late -> DELIVERY_LATE. Need tracking help -> DELIVERY_TRACKING",
            "priority": "If 'not delivered' AND 'late' both present, prefer DELIVERY_MISSING"
        },
        "DELIVERY_TRACKING": {
            "inclusion": "Customer cannot find tracking info, tracking shows wrong status, needs tracking number",
            "exclusion": "Package is late -> DELIVERY_LATE. Package missing -> DELIVERY_MISSING",
            "priority": "Only use if tracking is the PRIMARY problem, not accompaniment"
        },
        "ORDER_STATUS": {
            "inclusion": "Customer asks about order status, wants to modify/cancel order",
            "exclusion": "This is about a delivery issue -> DELIVERY_* instead",
            "priority": "If 'order' AND 'delivery' both prominent, use DELIVERY_*"
        },
        "APP_TECHNICAL": {
            "inclusion": "Problem with app, website, login, access, or general technical issue",
            "exclusion": "Specific device problem -> DEVICE_ISSUE",
            "priority": "Login/access problems are APP_TECHNICAL even if on mobile"
        },
        "DEVICE_ISSUE": {
            "inclusion": "Problem with Kindle, Fire TV, Echo, Alexa, or video streaming on Amazon devices",
            "exclusion": "General app/website issue -> APP_TECHNICAL",
            "priority": "If device name mentioned + technical issue, prefer DEVICE_ISSUE"
        },
        "REFUND_REQUEST": {
            "inclusion": "Customer wants money back, has billing issue, or payment problem",
            "exclusion": "Customer wants to return item -> RETURN_REQUEST",
            "priority": "If 'refund' AND 'return' both present, prefer RETURN_REQUEST"
        },
        "RETURN_REQUEST": {
            "inclusion": "Customer wants to return item, exchange, or has product quality issue",
            "exclusion": "Only wants money back -> REFUND_REQUEST",
            "priority": "Product quality issues are RETURN_REQUEST even if no explicit return mentioned"
        },
        "ACCOUNT_OTHER": {
            "inclusion": "Account issues not fitting APP_TECHNICAL, seller questions, marketplace issues",
            "exclusion": "Login/access -> APP_TECHNICAL",
            "priority": "Catch-all for account issues"
        }
    },

    "boundary_decisions": {
        "ORDER_STATUS_vs_DELIVERY_TRACKING": {
            "rule": "ORDER_STATUS = asking about order existence/status. DELIVERY_TRACKING = cannot find tracking info or tracking wrong.",
            "overlap_count": 3,
            "decision": "Keep separate - low overlap"
        },
        "DELIVERY_CARRIER": {
            "rule": "Demote from leaf intent to MODIFIER. Add as context to DELIVERY_* when carrier is specifically mentioned.",
            "primary_count": 82,
            "context_count": 145,
            "decision": "MERGE into DELIVERY category as modifier"
        },
        "APP_USAGE_vs_ACCOUNT_ACCESS": {
            "rule": "Login/access via app is APP_TECHNICAL. Login issues are not distinct enough to separate.",
            "overlap_count": 32,
            "decision": "MERGE into APP_TECHNICAL"
        },
        "PRODUCT_ISSUE_vs_RETURN_REQUEST": {
            "rule": "Product issue almost always leads to return request. Merge into RETURN_REQUEST.",
            "overlap_count": 32,
            "decision": "MERGE into RETURN_REQUEST"
        },
        "REFUND_REQUEST_vs_PAYMENT_ISSUE": {
            "rule": "Payment issues lead to refund. Keep as single intent REFUND_REQUEST.",
            "overlap_count": 19,
            "decision": "MERGE into REFUND_REQUEST"
        },
        "DEVICE_ISSUE_vs_VIDEO_STREAMING": {
            "rule": "Video streaming often on specific device. Merge into DEVICE_ISSUE.",
            "overlap_count": 10,
            "decision": "MERGE into DEVICE_ISSUE"
        }
    },

    "weakest_intents": [
        {
            "intent": "DELIVERY_TRACKING",
            "issue": "Low volume, often accompanies other delivery intents",
            "recommendation": "Keep - useful for routing specific troubleshooting"
        },
        {
            "intent": "ACCOUNT_OTHER",
            "issue": "Catch-all category may be too vague",
            "recommendation": "Keep but monitor - may need future split"
        }
    ]
}

# Save taxonomy v3
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_candidate_taxonomy_v3.json', 'w', encoding='utf-8') as f:
    json.dump(taxonomy_v3, f, indent=2, ensure_ascii=False)

print("Candidate taxonomy v3 saved.")
print("\nKey changes from v2 -> v3:")
print("  - 14 leaf intents -> 9 leaf intents")
print("  - DELIVERY_CARRIER: leaf -> MODIFIER")
print("  - ACCOUNT_ACCESS: merged into APP_TECHNICAL")
print("  - PRODUCT_ISSUE: merged into RETURN_REQUEST")
print("  - ORDER_MODIFY: merged into ORDER_STATUS")
print("  - VIDEO_STREAMING: merged into DEVICE_ISSUE")
print("  - REFUND_REQUEST: merged with PAYMENT_ISSUE")
