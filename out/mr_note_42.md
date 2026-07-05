# SentinelAI Code Guardian — MR !42
**Commit:** `abc1234` · **Findings:** 1 · **Worst:** 🟠 HIGH

## 🟠 HIGH
- **🟠 HIGH** · _performance_ · `checkout/views.py:6`
  This change introduces an N+1 query problem by loading order line items individually within a loop.
  _Fix:_ Replace the loop with a single query using `.prefetch_related('orderitem_set')` to fetch all line items efficiently, for example: `Order.objects.filter(user=cart.user).prefetch_related('orderitem_set')`.

## CI failure

The `test:checkout` job failed because the `test_confirm_checkout_renders_full_history` test exceeded its database query budget. The test expected at most 5 SQL queries when confirming a checkout but instead performed 27, likely due to an N+1 query problem where each of the user's 12 orders caused a separate query for its items. This performance issue is triggered by the query count assertion at `checkout/tests/test_views.py:88`.
