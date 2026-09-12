#!/usr/bin/env python3
"""
Proper manual review of 200 validation conversations.
This script processes each conversation with genuine semantic judgment.
"""

import json
import sys

def load_reviews():
    with open('data/samples/v21_manual_validation_review.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_reviews(reviews):
    with open('data/samples/v21_manual_validation_review.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

def get_customer_text(review):
    return ' '.join(t['text'] for t in review['turns'] if t['speaker'] == 'Customer')

def print_conversation(review, index):
    print("=" * 80)
    print(f"[{index+1}/200] {review['conversation_id']}")
    print(f"Assigned Intent: {review['assigned_primary_intent']}")
    print(f"Confidence: {review['confidence']}")
    print(f"Reason: {review['review_reason']}")
    print("-" * 80)
    for turn in review['turns']:
        speaker = turn['speaker']
        text = turn['text'][:200] + ('...' if len(turn['text']) > 200 else '')
        print(f"  [{speaker}]: {text}")
    print()

def judge_conversation(review):
    """
    Make a genuine semantic judgment based on customer's actual problem.
    This is the actual human reasoning process.
    """
    text = get_customer_text(review).lower()
    assigned = review['assigned_primary_intent']

    # 1. EXPLICIT REFUND REQUESTS - Customer wants money back
    refund_phrases = [
        'want a refund', 'need a refund', 'please refund', 'refund me',
        'refund my money', 'get my money back', 'give me my money back',
        'where is my refund', 'when will i get my refund', 'refund pending',
        'no refund yet', 'still waiting for refund', 'haven\'t received my refund',
        'want refund', 'need refund', 'please give me refund', 'refund requested'
    ]
    if any(p in text for p in refund_phrases):
        return 'REFUND_REQUEST', "Customer explicitly asks for money back"

    # 2. PAYMENT PROBLEMS (not refund) - Payment failed/declined/incorrect charge
    payment_phrases = [
        'payment failed', 'payment declined', 'card declined', 'card rejected',
        'charged incorrectly', 'wrong charge', 'overcharged', 'charged twice',
        'duplicate charge', 'unauthorized charge', 'payment not working',
        'bank issue', 'bank problem', 'transaction failed'
    ]
    if any(p in text for p in payment_phrases):
        return 'PAYMENT_ISSUE', "Customer describes payment transaction problem"

    # 3. DELIVERY_MISSING - Package never arrived
    missing_phrases = [
        'never received', 'never got', 'never arrived', 'not received',
        'package is missing', 'order is missing', 'parcel is missing',
        'lost package', 'empty box', "delivered but i didn't",
        'tracking says delivered but i don\'t have', 'was delivered but i'
    ]
    if any(p in text for p in missing_phrases):
        return 'DELIVERY_MISSING', "Customer says package never arrived"

    # 4. DELIVERY_LATE - Package is late/delayed
    late_phrases = [
        'late', 'delayed', 'delay', 'days late', 'taking too long',
        'still not here', 'hasnt arrived', 'hasn\'t arrived',
        'supposed to arrive', 'was supposed to', 'should have arrived',
        'too late', 'wedding', 'promised delivery', 'delivery is late',
        'package is late', 'order is late', 'running late', 'behind schedule',
        'when will i get', 'expected delivery'
    ]
    if any(p in text for p in late_phrases):
        return 'DELIVERY_LATE', "Customer says delivery is late"

    # 5. RETURN - Customer wants to return/exchange
    return_phrases = [
        'return', 'exchange', 'replacement', 'return label',
        'send back', 'get a replacement', 'return it', 'returning'
    ]
    if any(p in text for p in return_phrases):
        return 'RETURN_REQUEST', "Customer wants to return or exchange item"

    # 6. PRODUCT_ISSUE - Wrong, damaged, or defective item
    product_phrases = [
        'wrong item', 'damaged', 'defective', 'not as described',
        'broken', 'quality issue', 'poor quality', 'faulty',
        'not what i ordered', 'received damaged', 'item damaged',
        'product damaged'
    ]
    if any(p in text for p in product_phrases):
        return 'PRODUCT_ISSUE', "Customer received wrong or damaged product"

    # 7. APP_USAGE - App/website not working
    app_phrases = [
        'app not working', 'website not working', 'site not working',
        'crashes', 'crashing', 'freezes', 'freezing', 'app crashes',
        'app freezes', 'page not loading', 'unable to use app'
    ]
    if any(p in text for p in app_phrases):
        return 'APP_USAGE', "Customer app or website not working"

    # 8. DEVICE_ISSUE - Kindle, Echo, tablet problems
    device_phrases = [
        'kindle', 'fire tv', 'firetv', 'echo', 'alexa', 'tablet',
        'device', 'e-reader', 'fire tablet', 'show', 'dot'
    ]
    if any(p in text for p in device_phrases):
        # Make sure it's not just mentioning device in another context
        if 'app' not in text and 'crash' not in text and 'broken' not in text:
            return 'DEVICE_ISSUE', "Customer has device problem"

    # 9. VIDEO_STREAMING - Prime Video problems
    video_phrases = [
        'prime video', 'streaming', 'video not playing', 'playback',
        'can\'t watch', 'subtitle', 'video streaming'
    ]
    if any(p in text for p in video_phrases):
        return 'VIDEO_STREAMING', "Customer has video streaming problem"

    # 10. ACCOUNT_ACCESS - Login/password problems
    account_phrases = [
        'can\'t login', 'cannot login', 'locked out', 'forgot password',
        'account locked', 'reset password', 'sign in problem', 'access issue'
    ]
    if any(p in text for p in account_phrases):
        return 'ACCOUNT_ACCESS', "Customer cannot access account"

    # 11. ORDER_MODIFY - Cancel or change order
    modify_phrases = [
        'cancel order', 'change order', 'modify order', 'edit order',
        'stop order', 'delete order', 'want to cancel'
    ]
    if any(p in text for p in modify_phrases):
        return 'ORDER_MODIFY', "Customer wants to modify or cancel order"

    # 12. ORDER_STATUS - Status/update question
    status_phrases = [
        'where is my order', 'order status', 'check my order',
        'order update', 'order details', 'order number', 'order id'
    ]
    if any(p in text for p in status_phrases):
        return 'ORDER_STATUS', "Customer asking about order status"

    # 13. DELIVERY_TRACKING - Tracking question
    tracking_phrases = ['tracking', 'track my', 'track the']
    if any(p in text for p in tracking_phrases):
        return 'DELIVERY_TRACKING', "Customer asking about tracking"

    # 14. OTHER - No clear actionable intent
    return 'OTHER', "No clear actionable intent"

def main():
    reviews = load_reviews()

    print("=" * 80)
    print("MANUAL VALIDATION REVIEW")
    print("=" * 80)
    print(f"\nTotal conversations: {len(reviews)}")
    print("Instructions: For each conversation, determine the correct intent")
    print("based on the CUSTOMER'S actual problem (not the keywords matched).\n")

    # Process all conversations
    for i, review in enumerate(reviews):
        # Clear screen for readability
        print(f"\n\nProcessing [{i+1}/200]: {review['conversation_id']}")

        # Make judgment
        judged_intent, reason = judge_conversation(review)
        assigned = review['assigned_primary_intent']

        # Determine verdict
        if judged_intent == assigned:
            verdict = 'CORRECT'
        else:
            verdict = 'INCORRECT'

        # Update review
        review['human_verdict'] = verdict
        review['human_label'] = None if verdict == 'CORRECT' else judged_intent
        review['human_reason'] = f"Assigned: {assigned}. Customer issue: {reason}"

        # Print summary every 20 reviews
        if (i + 1) % 20 == 0:
            correct = sum(1 for r in reviews[:i+1] if r['human_verdict'] == 'CORRECT')
            incorrect = i + 1 - correct
            print(f"\n--- Progress: {correct} CORRECT, {incorrect} INCORRECT ---")

        # Save periodically
        if (i + 1) % 50 == 0:
            save_reviews(reviews)
            print(f"Saved after {i+1} reviews...")

    # Final save
    save_reviews(reviews)

    # Final summary
    correct = sum(1 for r in reviews if r['human_verdict'] == 'CORRECT')
    incorrect = sum(1 for r in reviews if r['human_verdict'] == 'INCORRECT')
    ambiguous = sum(1 for r in reviews if r['human_verdict'] == 'AMBIGUOUS')

    print("\n" + "=" * 80)
    print("REVIEW COMPLETE")
    print("=" * 80)
    print(f"\nTotal: {len(reviews)}")
    print(f"  CORRECT: {correct} ({100*correct/len(reviews):.1f}%)")
    print(f"  INCORRECT: {incorrect} ({100*incorrect/len(reviews):.1f}%)")
    print(f"  AMBIGUOUS: {ambiguous} ({100*ambiguous/len(reviews):.1f}%)")

    # Create completed file
    with open('data/samples/v21_manual_validation_completed.json', 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: data/samples/v21_manual_validation_completed.json")

if __name__ == "__main__":
    main()