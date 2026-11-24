# Why did a $20 settlement gap disappear overnight?

Order p104 had a $50 capture and a $30 settlement. The first reconciliation reported a $20 shortfall. Two partial refunds arrived in the next event batch, for $15 and $5. The order then balanced. Resending either entire batch leaves the reconciliation result unchanged.

| Final exception | Evidence | Follow-up |
| --- | --- | --- |
| p103 · USD | 820 cents captured, settlement missing | Check the settlement window. |
| p105 · EUR | 2,899 cents expected, 2,800 settled | Trace the 99-cent difference. |
| p106 · USD | One event ID carries two different amounts | Quarantine the order until the conflicting event is resolved. |
| p107 · USD | 2,400 cents settled without a ledger event | Check for an unmatched capture. |

The fixture is small enough to audit by hand. Exact event copies collapse before aggregation. Conflicting copies block the affected order and currency. All money stays in integer minor units. The settlement input represents one net line per order and currency. Processing fees, exchange rates, and split settlements would require additional rules.

Run `python projects/payment-reconciliation/replay.py` from the repository root with standard Python. The script replays each batch twice and writes both snapshots. The two CSV inputs contain fictional payments.

[Reconciliation query](reconcile.sql) · [Event batches](events.csv) · [Settlement lines](settlements.csv) · [Replay results](exceptions.csv)
