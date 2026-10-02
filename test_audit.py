# test_audit.py
import uuid
from langgraph.types import Command
from app.audit_graph import audit_engine

def run_test(pdf_path: str, test_name: str):
    print("=" * 60)
    print(f"TEST RUN: {test_name}")
    print("=" * 60)
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Start Audit Workflow
    result = audit_engine.invoke({"pdf_path": pdf_path}, config=config)

    # 2. Check State to see if workflow paused at Human Review
    state = audit_engine.get_state(config)
    if state.next and "human_review" in state.next:
        interrupt_info = state.tasks[0].interrupts[0].value
        print("\n📢 INTERRUPT TRIGGERED!")
        print(f"Vendor: {interrupt_info['vendor']} | Amount: ${interrupt_info['grand_total']:,.2f}")
        print(f"Violations: {len(interrupt_info['violations'])}")
        for v in interrupt_info['violations']:
            print(f"  ❌ [{v['severity']}] {v['clause_violated']}: {v['finding']}")

        # 3. Simulate Human Manager Approval / Rejection
        print("\nSimulating Human Manager Sign-off: Approving with VP justification...")
        resumed_result = audit_engine.invoke(
            Command(resume={"action": "APPROVED_BY_VP", "comments": "Exception granted for urgent cloud advisory."}),
            config=config
        )
        print(f"Final Decision: {resumed_result['human_decision']}")
        print(f"Manager Notes: {resumed_result['human_comments']}")
    else:
        print(f"\nAudit completed without interruptions!")
        print(f"Decision: {result['human_decision']}")

if __name__ == "__main__":
    # Test 1: Clean Compliant Invoice
    run_test("data/test_invoices/INV_COMPLIANT.pdf", "Scenario 1: Standard Compliant Invoice")

    # Test 2: Policy Breach Invoice (Missing PO & Exceeds $50,000 threshold)
    run_test("data/test_invoices/INV_PO_BREACH.pdf", "Scenario 2: Policy Breach ($65,000 without PO)")