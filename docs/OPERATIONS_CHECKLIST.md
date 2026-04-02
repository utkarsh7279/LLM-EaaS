# Operations Checklist

## Deployment-Day Checklist
- Confirm backend service is live.
- Confirm frontend service is live.
- Confirm database schema is initialized.
- Confirm health endpoint is green.
- Confirm one end-to-end evaluation succeeds.

## Runtime Verification
- Backend logs show no repeated exceptions.
- API response times are within acceptable range.
- Database connection pool is stable.
- LLM provider requests are succeeding.

## Post-Deployment Monitoring
- Check Render service logs daily during first week.
- Check Render database usage against free-tier limit.
- Check Vercel deployment and runtime logs.
- Check Groq usage quota and error rate.

## Incident Response (Quick Path)
1. Reproduce issue via health endpoint and one API call.
2. Inspect backend logs first.
3. Validate database URL and schema status.
4. Validate LLM key, base URL, model name.
5. Redeploy backend after config fixes.
6. Re-test from frontend.

## Common Issues
### Build/start field missing on Render
- Cause: Docker runtime selected.
- Fix: recreate as Python web service.

### Backend starts but evaluation fails
- Cause: LLM provider env mismatch.
- Fix: verify provider, base URL, API key, model values.

### CORS errors in browser
- Cause: origin mismatch.
- Fix: set allowed origins to exact frontend domain.

### Database errors after deploy
- Cause: schema not initialized.
- Fix: run schema.sql against external DB URL once.

## Release Management
- Commit documentation and deployment changes together.
- Keep local-only helper files out of git.
- Tag stable deployment commits for rollback points.
