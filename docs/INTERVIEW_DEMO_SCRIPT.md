# Interview and Demo Script

## 10-Line Version
1. LLM EaaS is a platform for evaluating LLM outputs at scale.
2. It removes subjective manual checks and replaces them with rubric-based scoring.
3. Users upload datasets and define quality criteria.
4. The system performs automated LLM-as-judge evaluations.
5. Results are stored at item-level and aggregate-level.
6. Candidate runs are compared against baseline runs.
7. Regression detection prevents degraded models from shipping.
8. CI gate signals support go/no-go deployment decisions.
9. The stack is FastAPI, Next.js, PostgreSQL, and provider-flexible LLM integration.
10. Outcome: faster iteration, safer releases, and measurable quality.

## 60-Second Version
LLM EaaS helps teams evaluate AI model outputs in a reliable and repeatable way. Instead of manual response reviews, users upload datasets, define rubric criteria, and run automated LLM-as-judge evaluations. The platform calculates metrics, compares candidate behavior against a baseline, and detects regressions before deployment. It also exposes CI gate signals so poor-quality changes can be blocked automatically. We chose FastAPI, Next.js, and PostgreSQL for speed, reliability, and clean scaling, plus a provider abstraction layer so teams can optimize for cost, speed, or privacy without code rewrites. Overall, this turns model evaluation from an ad-hoc manual process into a measurable, auditable engineering workflow.
