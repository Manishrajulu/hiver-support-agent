#!/usr/bin/env python3
"""Create taxonomy audit and candidate taxonomy v2"""

import json

# ==========================================
# TAXONOMY AUDIT
# ==========================================

taxonomy_audit = {
    "previous_candidate_themes": {
        "DELIVERY_PROBLEM": {
            "current_count": 920,
            "what_it_represents": "Issues with package delivery, tracking, late deliveries, lost packages",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["ORDER_ISSUE", "PRIME_MEMBERSHIP"],
            "recommended_treatment": "KEEP",
            "notes": "Well-defined intent. May need sub-intents: LATE_DELIVERY, MISSING_DELIVERY, TRACKING_ISSUE, CARRIER_ISSUE"
        },
        "ORDER_ISSUE": {
            "current_count": 835,
            "what_it_represents": "Order status, modifying/canceling orders, order numbers",
            "classification": "PRIMARY_INTENT",
            "too_broad": True,
            "too_narrow": False,
            "overlaps_with": ["DELIVERY_PROBLEM", "REFUND"],
            "recommended_treatment": "SPLIT",
            "notes": "Mixed with delivery. ORDER_STATUS is distinct from ORDER_MODIFICATION/CANCELLATION"
        },
        "TECHNICAL_ISSUE": {
            "current_count": 740,
            "what_it_represents": "App/website problems, streaming issues, device problems",
            "classification": "PRIMARY_INTENT",
            "too_broad": True,
            "too_narrow": False,
            "overlaps_with": ["ACCOUNT_ISSUE"],
            "recommended_treatment": "SPLIT",
            "notes": "APP_ISSUE dominates (70%). DEVICE_ISSUE and VIDEO_STREAMING are distinct sub-intents"
        },
        "PRODUCT_ISSUE": {
            "current_count": 575,
            "what_it_represents": "Product quality, wrong item, damaged, defective",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["RETURN_EXCHANGE"],
            "recommended_treatment": "KEEP",
            "notes": "Clear customer problem: received defective/wrong product"
        },
        "ACCOUNT_ISSUE": {
            "current_count": 479,
            "what_it_represents": "Login problems, account locked/closed/suspended",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["TECHNICAL_ISSUE", "CONTACT_REQUEST"],
            "recommended_treatment": "KEEP",
            "notes": "Clear intent. May overlap with login-related TECHNICAL"
        },
        "PRIME_MEMBERSHIP": {
            "current_count": 436,
            "what_it_represents": "Prime subscription, renewal, cancellation, Prime benefits",
            "classification": "CONTEXT_MODIFIER",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["DELIVERY_PROBLEM", "REFUND"],
            "recommended_treatment": "RECLASSIFY",
            "notes": "Often a context modifier, not primary intent. Customer problem is usually delivery/refund, not Prime itself."
        },
        "CUSTOMER_SERVICE_QUALITY": {
            "current_count": 353,
            "what_it_represents": "Complaints about service quality, no response, rudeness",
            "classification": "SENTIMENT_SIGNAL",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["CONTACT_REQUEST", "ESCALATION"],
            "recommended_treatment": "SIGNAL",
            "notes": "Not a customer intent - this is sentiment/escalation signal for routing decisions"
        },
        "CONTACT_REQUEST": {
            "current_count": 945,
            "what_it_represents": "Customer asking to be called/emailed/DMed, requesting to speak to someone",
            "classification": "ESCALATION_SIGNAL",
            "too_broad": True,
            "too_narrow": False,
            "overlaps_with": ["CUSTOMER_SERVICE_QUALITY", "ACCOUNT_ISSUE"],
            "recommended_treatment": "SIGNAL",
            "notes": "Not a customer intent - describes how customer wants to be supported. Should be used for escalation, not intent classification."
        },
        "PAYMENT_ISSUE": {
            "current_count": 335,
            "what_it_represents": "Billing problems, credit card issues, gift cards",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["REFUND", "ACCOUNT_ISSUE"],
            "recommended_treatment": "KEEP",
            "notes": "Clear customer problem with payment"
        },
        "REFUND": {
            "current_count": 262,
            "what_it_represents": "Money refund requests, refund status, reimbursement",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["PAYMENT_ISSUE", "RETURN_EXCHANGE"],
            "recommended_treatment": "KEEP",
            "notes": "Clear customer problem. Often overlaps with RETURN but distinct ask."
        },
        "RETURN_EXCHANGE": {
            "current_count": 256,
            "what_it_represents": "Returning items, exchanges, replacements",
            "classification": "PRIMARY_INTENT",
            "too_broad": False,
            "too_narrow": False,
            "overlaps_with": ["REFUND", "PRODUCT_ISSUE"],
            "recommended_treatment": "KEEP",
            "notes": "Clear customer problem. Customer wants to return/exchange item."
        }
    },
    "problem_summary": {
        "too_broad_categories": ["ORDER_ISSUE", "TECHNICAL_ISSUE"],
        "reclassified_as_signals": ["CUSTOMER_SERVICE_QUALITY", "CONTACT_REQUEST"],
        "reclassified_as_modifiers": ["PRIME_MEMBERSHIP"],
        "needs_splitting": ["DELIVERY_PROBLEM"],
        "needs_merging": [],
        "overlapping_pairs": [
            ("DELIVERY_PROBLEM", "ORDER_ISSUE"),
            ("REFUND", "PAYMENT_ISSUE"),
            ("PRODUCT_ISSUE", "RETURN_EXCHANGE")
        ]
    }
}

# ==========================================
# PROPOSED CANDIDATE TAXONOMY V2
# ==========================================

candidate_taxonomy_v2 = {
    "top_level_categories": 6,
    "leaf_intents": 14,
    "coverage_estimate": "75-80%",
    "other_estimate": "20-25%",

    "primary_intents": [
        {
            "intent_id": "DELIVERY_LATE",
            "name": "Late Delivery",
            "definition": "Customer's package has not arrived by the expected delivery date",
            "parent_category": "DELIVERY",
            "frequency_estimate": "25-30%",
            "example_count": "Common (258+ in sample)",
            "why_exists": "Most common delivery problem - specific action available (check status, expedite, refund)",
            "common_confusion": "Often overlaps with ORDER_STATUS - but here customer knows package exists, just late",
            "how_to_distinguish": "Keywords: 'late', 'delayed', 'eta', 'expected delivery', 'not arrived yet'"
        },
        {
            "intent_id": "DELIVERY_MISSING",
            "name": "Missing/Not Delivered",
            "definition": "Customer never received package, shows delivered but not there",
            "parent_category": "DELIVERY",
            "frequency_estimate": "10-15%",
            "example_count": "Moderate (94+ in sample)",
            "why_exists": "Different action than late - may need refund or replacement faster",
            "common_confusion": "May overlap with LATE if customer unsure",
            "how_to_distinguish": "Keywords: 'not delivered', 'never received', 'missing', 'shows delivered but'"
        },
        {
            "intent_id": "DELIVERY_TRACKING",
            "name": "Tracking Issue",
            "definition": "Customer cannot track package or tracking information is wrong",
            "parent_category": "DELIVERY",
            "frequency_estimate": "10-15%",
            "example_count": "Moderate (135+ in sample)",
            "why_exists": "Specific troubleshooting action available",
            "common_confusion": "Often accompanies LATE or MISSING",
            "how_to_distinguish": "Keywords: 'tracking', 'track', 'where is my package', 'status unclear'"
        },
        {
            "intent_id": "DELIVERY_CARRIER",
            "name": "Carrier/Logistics Problem",
            "definition": "Issue with delivery carrier (Gati, etc.) causing delivery problems",
            "parent_category": "DELIVERY",
            "frequency_estimate": "10-15%",
            "example_count": "Moderate (117+ in sample)",
            "why_exists": "May require different escalation path",
            "common_confusion": "Often a sub-issue of other delivery problems",
            "how_to_distinguish": "Keywords: carrier names, 'delivery partner', specific carrier complaints"
        },
        {
            "intent_id": "ORDER_STATUS",
            "name": "Order Status Inquiry",
            "definition": "Customer wants to know status of order, where it is, when arriving",
            "parent_category": "ORDER",
            "frequency_estimate": "8-10%",
            "example_count": "Common",
            "why_exists": "Very common - different from modification/cancellation",
            "common_confusion": "Overlaps with DELIVERY",
            "how_to_distinguish": "Customer is asking for information, not requesting change"
        },
        {
            "intent_id": "ORDER_MODIFY",
            "name": "Order Modification/Cancellation",
            "definition": "Customer wants to change or cancel their order",
            "parent_category": "ORDER",
            "frequency_estimate": "3-5%",
            "example_count": "Moderate",
            "why_exists": "Different action path than status inquiry",
            "common_confusion": "May overlap with cancellation requests",
            "how_to_distinguish": "Keywords: 'cancel', 'change order', 'modify', 'edit order'"
        },
        {
            "intent_id": "APP_USAGE",
            "name": "App/Website Issue",
            "definition": "Problem using Amazon app or website (not working, error, can't find something)",
            "parent_category": "TECHNICAL",
            "frequency_estimate": "25-30%",
            "example_count": "Very common (506+ in sample)",
            "why_exists": "Most common technical issue",
            "common_confusion": "May overlap with LOGIN issue",
            "how_to_distinguish": "Keywords: 'app', 'website', 'not working', 'error', 'page'"
        },
        {
            "intent_id": "DEVICE_ISSUE",
            "name": "Device Problem",
            "definition": "Issue with Amazon device (Kindle, Fire TV, Echo, Alexa)",
            "parent_category": "TECHNICAL",
            "frequency_estimate": "15-20%",
            "example_count": "Common (146+ in sample)",
            "why_exists": "Device-specific troubleshooting available",
            "common_confusion": "May need to distinguish from general APP issue",
            "how_to_distinguish": "Keywords: 'kindle', 'fire tv', 'echo', 'alexa', 'tablet', 'device'"
        },
        {
            "intent_id": "VIDEO_STREAMING",
            "name": "Video/Streaming Issue",
            "definition": "Problem with Prime Video, streaming content, subtitles, playback",
            "parent_category": "TECHNICAL",
            "frequency_estimate": "5-10%",
            "example_count": "Moderate (90+ in sample)",
            "why_exists": "Specific troubleshooting for video issues",
            "common_confusion": "May overlap with DEVICE issue",
            "how_to_distinguish": "Keywords: 'video', 'streaming', 'prime video', 'subtitle', 'playback'"
        },
        {
            "intent_id": "ACCOUNT_ACCESS",
            "name": "Account Access Problem",
            "definition": "Customer cannot login, access account, password issues, account locked",
            "parent_category": "ACCOUNT",
            "frequency_estimate": "3-5%",
            "example_count": "Moderate",
            "why_exists": "Different action path than other issues",
            "common_confusion": "May overlap with APP_USAGE (login via app)",
            "how_to_distinguish": "Keywords: 'login', 'password', 'locked', 'access', 'account suspended'"
        },
        {
            "intent_id": "REFUND_REQUEST",
            "name": "Refund Request",
            "definition": "Customer wants money back for order, payment, or subscription",
            "parent_category": "REFUND_PAYMENT",
            "frequency_estimate": "5-8%",
            "example_count": "Moderate",
            "why_exists": "Clear customer action - want money back",
            "common_confusion": "Overlaps with RETURN but different request",
            "how_to_distinguish": "Keywords: 'refund', 'money back', 'reimburse', 'charged but'"
        },
        {
            "intent_id": "PAYMENT_ISSUE",
            "name": "Payment Problem",
            "definition": "Issue with payment method, billing, credit card, gift card",
            "parent_category": "REFUND_PAYMENT",
            "frequency_estimate": "3-5%",
            "example_count": "Moderate",
            "why_exists": "Different from refund - problem with payment process itself",
            "common_confusion": "May overlap with REFUND",
            "how_to_distinguish": "Keywords: 'payment', 'billing', 'credit card', 'charged incorrectly'"
        },
        {
            "intent_id": "RETURN_REQUEST",
            "name": "Return/Exchange Request",
            "definition": "Customer wants to return item or get replacement",
            "parent_category": "RETURN_PRODUCT",
            "frequency_estimate": "3-5%",
            "example_count": "Moderate",
            "why_exists": "Clear customer action",
            "common_confusion": "Often overlaps with PRODUCT_ISSUE",
            "how_to_distinguish": "Keywords: 'return', 'exchange', 'replacement', 'pick up'"
        },
        {
            "intent_id": "PRODUCT_ISSUE",
            "name": "Product Quality/Defect",
            "definition": "Customer received wrong, damaged, or defective product",
            "parent_category": "RETURN_PRODUCT",
            "frequency_estimate": "3-5%",
            "example_count": "Moderate",
            "why_exists": "Often leads to RETURN but distinct problem",
            "common_confusion": "Almost always leads to RETURN",
            "how_to_distinguish": "Keywords: 'wrong item', 'damaged', 'defective', 'not as described'"
        }
    ],

    "context_modifiers": [
        {
            "modifier_id": "PRIME_CUSTOMER",
            "name": "Prime Customer",
            "definition": "Customer is a Prime member - affects delivery expectations",
            "usage": "Add as modifier/context, not primary intent",
            "frequency": "15-20%"
        },
        {
            "modifier_id": "MARKETPLACE",
            "name": "Marketplace/Region",
            "definition": "Customer using Amazon.in, Amazon.fr, etc.",
            "usage": "Add as modifier/context",
            "frequency": "10-15%"
        }
    ],

    "escalation_signals": [
        {
            "signal_id": "FRUSTRATION_HIGH",
            "name": "High Frustration",
            "definition": "Customer expresses anger, frustration, or strong negative emotion",
            "action": "Consider escalation to human",
            "frequency": "15-20%"
        },
        {
            "signal_id": "PREVIOUS_CONTACT",
            "name": "Previous Unresolved Contact",
            "definition": "Customer mentions contacting before with no resolution",
            "action": "Consider escalation priority",
            "frequency": "10-15%"
        },
        {
            "signal_id": "ESCALATION_REQUEST",
            "name": "Escalation Request",
            "definition": "Customer explicitly asks for manager, supervisor, or callback",
            "action": "Escalate to human",
            "frequency": "5-10%"
        },
        {
            "signal_id": "SERVICE_COMPLAINT",
            "name": "Service Quality Complaint",
            "definition": "Customer complains about Amazon service quality",
            "action": "Log for quality tracking, consider escalation",
            "frequency": "10-15%"
        }
    ],

    "proposed_hierarchy": """
HIERARCHICAL PROPOSAL (Recommended):

TOP LEVEL (6 categories):
├── DELIVERY (40-45%)
│   ├── DELIVERY_LATE
│   ├── DELIVERY_MISSING
│   ├── DELIVERY_TRACKING
│   └── DELIVERY_CARRIER
├── ORDER (10-15%)
│   ├── ORDER_STATUS
│   └── ORDER_MODIFY
├── TECHNICAL (25-30%)
│   ├── APP_USAGE
│   ├── DEVICE_ISSUE
│   └── VIDEO_STREAMING
├── ACCOUNT (3-5%)
│   └── ACCOUNT_ACCESS
├── REFUND_PAYMENT (8-13%)
│   ├── REFUND_REQUEST
│   └── PAYMENT_ISSUE
└── RETURN_PRODUCT (6-10%)
    ├── RETURN_REQUEST
    └── PRODUCT_ISSUE

FLAT ALTERNATIVE (if simpler taxonomy needed):
10-12 primary intents without hierarchy

RECOMMENDATION: Hierarchical with 14 leaf intents
- Easier to explain and understand
- Allows aggregation to top-level for high-level routing
- Sub-intents are meaningful for retrieval and training
"""
}

# Save files
with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_taxonomy_audit.json', 'w', encoding='utf-8') as f:
    json.dump(taxonomy_audit, f, indent=2, ensure_ascii=False)

with open(r'C:\Users\DELL\Desktop\hiver\data\processed\amazonhelp_candidate_taxonomy_v2.json', 'w', encoding='utf-8') as f:
    json.dump(candidate_taxonomy_v2, f, indent=2, ensure_ascii=False)

print("Taxonomy audit and candidate taxonomy v2 saved.")
print("- amazonhelp_taxonomy_audit.json")
print("- amazonhelp_candidate_taxonomy_v2.json")
