# WeMakeDevs "Where's My Context?" Submission

## 60-Second Demo Script

**[0:00 - 0:10] Introduction**
"Hi, we built SentinelAI Code Guardian with Cognee Memory. Normally, a CI pipeline or a static LLM review catches syntax errors, but misses *context*. If a developer introduces an N+1 query that the team already learned the hard way not to do, a standard LLM won't know."

**[0:10 - 0:30] Seed the Memory**
"First, let's look at our Cognee Cloud backend. We've seeded it with our team's history—including a critical incident where an N+1 query caused a database outage. Our agent has committed this to its long-term memory."

**[0:30 - 0:50] Run the Scenario**
"Now, a developer opens a new Merge Request. The code looks fine on the surface, but it has a loop with a database query inside it. Let's trigger the Sentinel Code Guardian. 
*(Run `scripts/run_code_review.py def5678`)* 
The webhook fires. Our agent fetches the MR diff, queries Cognee for any relevant past lessons, and injects that context into Gemini."

**[0:50 - 1:00] The Verdict**
"Look at the generated review. Instead of just saying 'this is a bad practice', it explicitly says: *'In PR #42 (commit abc1234), we introduced a severe N+1 query... this caused a DB outage.'* It caught the repeating pattern using its Cognee memory. That's real, contextual AI code review."

---

## Google Form Submission Answers

**Project Name**: SentinelAI - Code Guardian with Memory
**Track**: iPhone / Cognee-Cloud Track
**Description**: SentinelAI is an autonomous engineer that reviews your code not just based on static rules, but on your team's actual history. We integrated Cognee Cloud to give the AI long-term memory. When a PR is merged or an incident occurs, the context is saved. When a new PR is opened, the Code Guardian recalls past incidents (like a previous N+1 query outage) to prevent the same mistake from being merged again.
**Cognee Coupon Used**: `COGNEE-35`
