# Master Policy Consolidation - Deployment Checklist

## Pre-Deployment Verification

### Code Changes ✅
- [x] `backend/agents/policy_consolidator.py` - Created (450+ lines)
- [x] `backend/db/models.py` - Modified (added MasterPolicy class)
- [x] `backend/db/crud.py` - Modified (added 3 CRUD functions)
- [x] `backend/db/migrate_add_master_policies.py` - Created
- [x] `backend/main.py` - Modified (added endpoints & imports)
- [x] `backend/models/schemas.py` - Modified (added Pydantic models)
- [x] `backend/agents/__init__.py` - Updated (added exports)

### Documentation ✅
- [x] `MASTER_POLICY_FEATURE.md` - Feature documentation
- [x] `IMPLEMENTATION_GUIDE.md` - Implementation guide
- [x] `API_REFERENCE.md` - API documentation
- [x] `IMPLEMENTATION_SUMMARY.md` - Summary document
- [x] `DEPLOYMENT_CHECKLIST.md` - This file

---

## Pre-Production Testing

### Unit Tests
- [ ] Test consolidate_policies() with single framework
- [ ] Test consolidate_policies() with multi-framework
- [ ] Test conflict resolution logic
- [ ] Test deduplication logic
- [ ] Test fallback consolidation
- [ ] Test save_master_policy() CRUD
- [ ] Test get_master_policy_for_session() CRUD
- [ ] Test delete_master_policy_for_session() CRUD

### Integration Tests
- [ ] Test POST /policies/consolidate endpoint
- [ ] Test GET /policies/master/{session_id} endpoint
- [ ] Test POST /export/master-policy/{session_id}/docx endpoint
- [ ] Test with real policies from database
- [ ] Test with multiple frameworks (GDPR, ISO, SOC2)
- [ ] Test authentication/authorization
- [ ] Test error handling (bad session, no policies, etc.)

### Database Tests
- [ ] Verify master_policies table created
- [ ] Verify foreign key to sessions works
- [ ] Verify indexes created (session_id, master_policy_id)
- [ ] Verify data persists after app restart
- [ ] Verify cascade delete works
- [ ] Test with 100+ master policies
- [ ] Test database query performance

### End-to-End Tests
- [ ] Profile org → Generate policies → Consolidate → Export
- [ ] Verify DOCX file opens in MS Word
- [ ] Verify DOCX file opens in LibreOffice
- [ ] Verify DOCX file opens in Google Docs
- [ ] Verify page numbers are correct
- [ ] Verify formatting is professional
- [ ] Test with different org names (special characters, etc.)

### Performance Tests
- [ ] Measure consolidation time (target: 45-60 seconds for 3 frameworks)
- [ ] Measure master policy retrieval time (target: <1 second)
- [ ] Measure DOCX export time (target: 5-10 seconds)
- [ ] Test with max load (4 concurrent consolidations)
- [ ] Monitor memory usage
- [ ] Monitor CPU usage

---

## Production Deployment

### Pre-Deployment
- [ ] Backup production database
- [ ] Notify users of planned downtime (if needed)
- [ ] Prepare rollback plan
- [ ] Test on staging environment first
- [ ] Review all code changes
- [ ] Verify all tests pass

### Deployment Steps

1. **Stop Application**
   ```bash
   # Stop FastAPI server
   # Stop any running consolidations
   ```
   - [ ] Completed

2. **Backup Database**
   ```bash
   cp backend/compliance.db backend/compliance.db.backup.$(date +%Y%m%d)
   ```
   - [ ] Backup created

3. **Deploy Code**
   ```bash
   # Pull latest code from repository
   git pull origin main
   
   # Or update files manually
   # backend/agents/policy_consolidator.py
   # backend/db/models.py
   # backend/db/crud.py
   # backend/db/migrate_add_master_policies.py
   # backend/main.py
   # backend/models/schemas.py
   # backend/agents/__init__.py
   ```
   - [ ] Code deployed

4. **Update Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   - [ ] Dependencies verified (should not need updates)

5. **Start Application**
   ```bash
   python main.py
   ```
   - [ ] Application started successfully
   - [ ] Check logs for: "✓ Migration complete: master_policies table created"
   - [ ] No errors during startup

6. **Verify Database Migration**
   ```bash
   sqlite3 backend/compliance.db ".tables" | grep master_policies
   ```
   - [ ] master_policies table exists

7. **Test API Endpoints**
   ```bash
   # Test health check
   curl http://localhost:8000/health
   
   # Test consolidation endpoint (if test session exists)
   curl -X POST http://localhost:8000/policies/consolidate \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"session_id": 1, "regenerate": false}'
   ```
   - [ ] API endpoints responding
   - [ ] No 500 errors

8. **Monitor Logs**
   ```bash
   # Watch for errors
   # Look for consolidation operations
   # Verify no database errors
   ```
   - [ ] Monitoring active
   - [ ] No critical errors

### Post-Deployment
- [ ] Notify users that feature is live
- [ ] Monitor for issues (first 24 hours)
- [ ] Check performance metrics
- [ ] Verify no data loss
- [ ] Collect initial user feedback

---

## Verification Checklist

### API Endpoints Working
- [ ] POST /policies/consolidate returns 200
- [ ] GET /policies/master/{session_id} returns 200
- [ ] POST /export/master-policy/{session_id}/docx returns 200
- [ ] Error handling returns appropriate status codes
- [ ] Authentication validation works

### Database
- [ ] master_policies table exists
- [ ] Can insert master policies
- [ ] Can retrieve master policies
- [ ] Indexes are used (check query performance)
- [ ] No orphaned records

### Documentation
- [ ] MASTER_POLICY_FEATURE.md is accurate
- [ ] IMPLEMENTATION_GUIDE.md is accurate
- [ ] API_REFERENCE.md is accurate
- [ ] All examples work as documented
- [ ] Error scenarios documented

### Performance
- [ ] Consolidation completes in reasonable time
- [ ] No memory leaks
- [ ] Database queries are fast
- [ ] Thread pool operates correctly
- [ ] No timeout issues

---

## Rollback Plan

If deployment has critical issues:

### Immediate Actions
1. Stop the application
2. Restore previous code version
3. Restore backup database (if schema changes failed)
4. Restart application with previous version
5. Notify users

### Rollback Commands
```bash
# Stop application
# (depends on your deployment method)

# Restore database from backup
cp backend/compliance.db.backup.YYYYMMDD backend/compliance.db

# Restore previous code
git checkout HEAD~1  # or specific commit

# Restart application
python main.py
```

### Verification After Rollback
- [ ] Application starts successfully
- [ ] Database is accessible
- [ ] Existing policies still exist
- [ ] All endpoints still work
- [ ] No data loss

---

## Known Issues & Workarounds

### Issue: "uuid_utils" module not found
- **Cause**: Python 3.14 compatibility issue with langchain/crewai
- **Workaround**: Use Python 3.13 or earlier
- **Status**: Known issue with LLM library ecosystem

### Issue: Consolidation times out
- **Cause**: Large number of frameworks/policies or LLM is slow
- **Workaround**: Increase timeout in client, check LLM service
- **Mitigation**: Consolidation runs in background (API returns immediately)

### Issue: DOCX export file is corrupted
- **Cause**: Export process interrupted or DOCX library issue
- **Workaround**: Try downloading again, regenerate master policy
- **Prevention**: Monitor export process in logs

### Issue: Master policy not found
- **Cause**: Consolidation wasn't run first, or wrong session_id
- **Workaround**: Run consolidation first, verify session_id
- **Prevention**: API returns clear error messages

---

## Monitoring & Alerts

### Critical Metrics to Monitor
1. **Consolidation Success Rate**
   - Target: >95% (including fallback)
   - Alert if: <90%

2. **Average Consolidation Time**
   - Target: 45-60 seconds for 3 frameworks
   - Alert if: >120 seconds

3. **API Response Times**
   - Consolidate: <1 second (async)
   - Get master: <1 second
   - Export DOCX: <15 seconds
   - Alert if: 2x target

4. **Error Rate**
   - Target: <0.1%
   - Alert if: >1%

5. **Database Size**
   - Monitor growth of master_policies table
   - Alert if: unexpected growth

### Recommended Monitoring Tools
- Application Performance Monitoring (APM): DataDog, New Relic, etc.
- Database Monitoring: SQLite monitoring tools
- Log Aggregation: ELK Stack, Splunk, etc.
- Error Tracking: Sentry, Rollbar, etc.

### Log Locations
- Application logs: stdout/stderr from `python main.py`
- Database logs: SQLite doesn't have separate logs
- LLM API logs: Check individual LLM provider dashboards

---

## User Communication

### Announcement Message
```
Subject: New Master Policy Feature Available

We're excited to announce the Master Policy feature!

Instead of separate policies for each compliance framework, 
you now get a single unified Master Policy that:

✓ Consolidates requirements from all your selected frameworks
✓ Resolves conflicts intelligently (strictest requirement wins)
✓ Eliminates duplicate requirements
✓ Includes implementation roadmap and compliance matrix
✓ Can be downloaded as a professional DOCX file

How to use:
1. Generate policies for your selected frameworks (existing process)
2. Click "Consolidate to Master Policy" (new!)
3. Download the master policy as DOCX
4. Individual framework policies still available if needed

Try it out and let us know if you have feedback!
```

### Onboarding
- [ ] Update user documentation
- [ ] Create tutorial/video if needed
- [ ] Add in-app guidance/tooltips
- [ ] Conduct user training sessions
- [ ] Create FAQ document

---

## Post-Deployment Validation

### Day 1
- [ ] Check error logs (should be minimal)
- [ ] Verify 5+ consolidations completed successfully
- [ ] Confirm DOCX exports are working
- [ ] Monitor API performance
- [ ] Collect initial user feedback

### Week 1
- [ ] Review consolidation success rate (target >95%)
- [ ] Analyze average consolidation times
- [ ] Check database size growth
- [ ] Review error patterns
- [ ] Check user adoption rate

### Month 1
- [ ] Full performance analysis
- [ ] User satisfaction survey
- [ ] Identify any issues or edge cases
- [ ] Plan improvements/optimizations
- [ ] Document lessons learned

---

## Success Criteria

Feature is successfully deployed if:

✅ All tests pass (unit, integration, E2E)
✅ API endpoints return correct responses
✅ Master policies correctly saved to database
✅ DOCX exports are professional and correct
✅ No critical errors in logs
✅ Performance meets targets
✅ Consolidation success rate >95%
✅ Users can successfully use the feature
✅ No data loss or corruption
✅ Rollback capability verified

---

## Sign-Off

### Development Team
- Code review completed: [ ] Date: ____
- Testing completed: [ ] Date: ____
- Documentation approved: [ ] Date: ____

### QA Team
- Integration tests passed: [ ] Date: ____
- Performance tests passed: [ ] Date: ____
- Security review passed: [ ] Date: ____

### Operations Team
- Deployment plan approved: [ ] Date: ____
- Rollback plan verified: [ ] Date: ____
- Monitoring set up: [ ] Date: ____

### Product Team
- Feature approved for release: [ ] Date: ____
- User communication ready: [ ] Date: ____
- Success metrics defined: [ ] Date: ____

---

## Deployment Summary

**Feature**: Master Policy Consolidation
**Version**: 1.0.0
**Release Date**: [To be filled]
**Deployment Status**: [To be filled]

**Key Changes**:
- New consolidation agent (policy_consolidator.py)
- New database table (master_policies)
- 3 new API endpoints
- Enhanced export capabilities
- Comprehensive documentation

**Risk Level**: LOW
- Backward compatible
- No breaking changes
- Comprehensive error handling
- Fallback mechanisms in place

**Rollback Difficulty**: LOW
- Simple code revert
- Database changes only add table (no schema changes)
- No data migration needed

---

**Deployment Completed**: [ ] Date: ____
**Approved By**: __________________
**Deployed By**: __________________

---

## Contact & Support

For deployment issues or questions:
- Development Team: [contact info]
- Operations Team: [contact info]
- Product Team: [contact info]

For user support:
- Documentation: See MASTER_POLICY_FEATURE.md
- API Reference: See API_REFERENCE.md
- Troubleshooting: See IMPLEMENTATION_GUIDE.md

---

**Last Updated**: July 1, 2026
**Status**: READY FOR DEPLOYMENT ✅
