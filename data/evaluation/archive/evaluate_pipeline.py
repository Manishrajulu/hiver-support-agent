import sys
sys.path.insert(0, "data")

from pipeline import run_pipeline


TEST_CASES = [
    # ACCOUNT_ACCESS
    ("ACCOUNT_ACCESS", "I forgot my password"),
    ("ACCOUNT_ACCESS", "I can't log into my account"),
    ("ACCOUNT_ACCESS", "I am unable to access my account"),
    ("ACCOUNT_ACCESS", "How do I reset my password?"),
    ("ACCOUNT_ACCESS", "My login isn't working"),

    # APP_USAGE
    ("APP_USAGE", "How do I use this app?"),
    ("APP_USAGE", "How can I change my app settings?"),
    ("APP_USAGE", "Where can I find this feature?"),
    ("APP_USAGE", "How do I use the application?"),
    ("APP_USAGE", "I don't know how to use this feature"),

    # DELIVERY_LATE
    ("DELIVERY_LATE", "My package is late"),
    ("DELIVERY_LATE", "My delivery hasn't arrived on time"),
    ("DELIVERY_LATE", "My order is delayed"),
    ("DELIVERY_LATE", "The delivery was supposed to arrive yesterday"),
    ("DELIVERY_LATE", "Why is my package taking so long?"),

    # DELIVERY_MISSING
    ("DELIVERY_MISSING", "My package never arrived"),
    ("DELIVERY_MISSING", "My order is missing"),
    ("DELIVERY_MISSING", "I haven't received my package"),
    ("DELIVERY_MISSING", "My delivery disappeared"),
    ("DELIVERY_MISSING", "The package says delivered but I don't have it"),

    # DELIVERY_TRACKING
    ("DELIVERY_TRACKING", "Where can I track my package?"),
    ("DELIVERY_TRACKING", "I want to track my order"),
    ("DELIVERY_TRACKING", "Can you give me my tracking information?"),
    ("DELIVERY_TRACKING", "How do I check my delivery status?"),
    ("DELIVERY_TRACKING", "Where is the tracking number?"),

    # DEVICE_ISSUE
    ("DEVICE_ISSUE", "My device isn't working"),
    ("DEVICE_ISSUE", "The device keeps crashing"),
    ("DEVICE_ISSUE", "My hardware is not working properly"),
    ("DEVICE_ISSUE", "My device won't turn on"),
    ("DEVICE_ISSUE", "I'm having a problem with my device"),

    # ORDER_MODIFY
    ("ORDER_MODIFY", "I want to cancel my order"),
    ("ORDER_MODIFY", "Can I change my order?"),
    ("ORDER_MODIFY", "I need to modify my order"),
    ("ORDER_MODIFY", "Can I change the items in my order?"),
    ("ORDER_MODIFY", "I want to update my order"),

    # ORDER_STATUS
    ("ORDER_STATUS", "Where is my order?"),
    ("ORDER_STATUS", "What is the status of my order?"),
    ("ORDER_STATUS", "Can you tell me about my order status?"),
    ("ORDER_STATUS", "I want to know where my order is"),
    ("ORDER_STATUS", "What is happening with my order?"),

    # OTHER
    ("OTHER", "I have a question that doesn't fit the usual categories"),
    ("OTHER", "I need help with something else"),
    ("OTHER", "Can someone help me with a general issue?"),
    ("OTHER", "I have another problem"),
    ("OTHER", "I need assistance with something unrelated"),

    # PAYMENT_ISSUE
    ("PAYMENT_ISSUE", "I was charged twice for the same order"),
    ("PAYMENT_ISSUE", "My payment failed"),
    ("PAYMENT_ISSUE", "I was charged but my order was not placed"),
    ("PAYMENT_ISSUE", "There is a problem with my payment"),
    ("PAYMENT_ISSUE", "Why was I charged twice?"),

    # PRODUCT_ISSUE
    ("PRODUCT_ISSUE", "My package arrived damaged"),
    ("PRODUCT_ISSUE", "The product I received is broken"),
    ("PRODUCT_ISSUE", "There is something wrong with the product"),
    ("PRODUCT_ISSUE", "The item I received is defective"),
    ("PRODUCT_ISSUE", "My product was damaged when it arrived"),

    # REFUND_REQUEST
    ("REFUND_REQUEST", "I want a refund"),
    ("REFUND_REQUEST", "Can I get my money back?"),
    ("REFUND_REQUEST", "I would like to request a refund"),
    ("REFUND_REQUEST", "How can I get a refund?"),
    ("REFUND_REQUEST", "Please refund my payment"),

    # RETURN_REQUEST
    ("RETURN_REQUEST", "I want to return my order"),
    ("RETURN_REQUEST", "How can I return an item?"),
    ("RETURN_REQUEST", "Can I send this product back?"),
    ("RETURN_REQUEST", "I need to return something I bought"),
    ("RETURN_REQUEST", "What is the process for returning an item?"),

    # VIDEO_STREAMING
    ("VIDEO_STREAMING", "My video won't play"),
    ("VIDEO_STREAMING", "The video keeps buffering"),
    ("VIDEO_STREAMING", "I can't stream videos"),
    ("VIDEO_STREAMING", "My video playback is not working"),
    ("VIDEO_STREAMING", "The video keeps stopping"),
]


def main():
    results = []
    correct = 0

    print("=" * 80)
    print("PIPELINE EVALUATION")
    print("=" * 80)

    for i, (expected, message) in enumerate(TEST_CASES, 1):
        try:
            result = run_pipeline(message, skip_generation=True)

            predicted = result["intent"]
            confidence = result["confidence"]
            decision = result["decision"]
            reason = result["reason"]

            is_correct = predicted == expected

            if is_correct:
                correct += 1

            results.append({
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "decision": decision,
                "correct": is_correct,
            })

            status = "OK" if is_correct else "WRONG"

            print(
                f"\n[{i:02d}/70] {status}"
                f"\nMessage:   {message}"
                f"\nExpected:  {expected}"
                f"\nPredicted: {predicted}"
                f"\nConfidence: {confidence:.3f}"
                f"\nDecision:  {decision}"
                f"\nReason:    {reason}"
            )

        except Exception as e:
            print(f"\n[{i:02d}/70] ERROR")
            print(f"Message: {message}")
            print(f"Error: {e}")

    print("\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    accuracy = correct / total * 100 if total else 0

    print(f"Total tests: {total}")
    print(f"Correct:     {correct}")
    print(f"Incorrect:   {total - correct}")
    print(f"Accuracy:    {accuracy:.2f}%")

    auto_handle = sum(
        r["decision"] == "AUTO_HANDLE"
        for r in results
    )

    escalate = sum(
        r["decision"] == "ESCALATE"
        for r in results
    )

    print(f"AUTO_HANDLE: {auto_handle}")
    print(f"ESCALATE:    {escalate}")

    print("\n")
    print("=" * 80)
    print("WRONG PREDICTIONS")
    print("=" * 80)

    wrong = [r for r in results if not r["correct"]]

    if not wrong:
        print("No incorrect predictions!")
    else:
        for r in wrong:
            print(
                f"\nExpected:   {r['expected']}"
                f"\nPredicted:  {r['predicted']}"
                f"\nConfidence: {r['confidence']:.3f}"
                f"\nDecision:   {r['decision']}"
            )


if __name__ == "__main__":
    main()