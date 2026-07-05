# Morning Briefing — Draft Incident

**Response time degradation on checkout-service**  
Severity: `high` · Service: `checkout-service`

## Summary
Users are experiencing significantly slow checkout processes due to a major increase in response times on the checkout service.

## Suspected cause
The deploy containing commit abc1234 introduced an N+1 query loop in checkout/views.py by replacing `select_related('items')` with individual `OrderItem` queries inside a loop. This change plausibly caused the ~13x increase in p95 latency (180ms -> 2400ms), 8x increase in query volume from checkout-service to orders-postgres, and subsequent connection pool saturation (from 12 to 98 active connections) around 07:40 UTC.

## Suspect commit
abc1234

## Seen before?
**76% match** to a prior incident: _Response time degradation on checkout-service_ — Roll back MR !42 / commit abc1234 on checkout-service.

## Next action
Roll back MR !42 / commit abc1234 on checkout-service.
