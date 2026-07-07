# Master Policy Consolidation - API Reference

## Endpoints

### 1. POST `/policies/consolidate`

**Consolidate all generated policies into a unified master policy**

#### Authentication
- Required: Bearer token (JWT)
- Role Required: Compliance Officer or Admin

#### Request Body
```json
{
  "session_id": 42,
  "regenerate": false
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | integer | Yes | Session ID from profiling step |
| `regenerate` | boolean | No (default: false) | If true, deletes existing and recreates |

#### Success Response (200)
```json
{
  "master_policy_id": "MASTER-2026-001",
  "title": "Unified Compliance Master Policy for Acme Corp",
  "frameworks": ["gdpr", "iso-27001", "soc2"],
  "domains_count": 8,
  "executive_summary": "This master policy consolidates requirements from 3 compliance frameworks...",
  "created_at": "2026-07-01T10:30:00.123456"
}
```

#### Error Responses

**400 - Bad Request**
```json
{
  "detail": "session_id is required"
}
```

**404 - Not Found**
```json
{
  "detail": "Session not found"
}
```
OR
```json
{
  "detail": "No policies found for this session"
}
```

**500 - Server Error**
```json
{
  "detail": "Consolidation failed: [error details]"
}
```

#### Notes
- If master policy already exists and `regenerate=false`, returns existing policy
- Consolidation typically takes 30-60 seconds
- Uses background thread pool (API returns immediately)
- Automatic fallback if AI consolidation fails

#### Example Request
```bash
curl -X POST http://localhost:8000/policies/consolidate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{
    "session_id": 42,
    "regenerate": false
  }'
```

---

### 2. GET `/policies/master/{session_id}`

**Retrieve the consolidated master policy for a session**

#### Authentication
- Required: Bearer token (JWT)
- Role Required: Any authenticated user with read access

#### Path Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_id` | integer | Yes | Session ID |

#### Success Response (200)
```json
{
  "master_policy_id": "MASTER-2026-001",
  "title": "Unified Compliance Master Policy for Acme Corp",
  "version": "1.0",
  "executive_summary": "This master policy consolidates requirements from 3 compliance frameworks (GDPR, ISO 27001, SOC2) into a unified, organization-wide compliance strategy...",
  "aligned_frameworks": ["gdpr", "iso-27001", "soc2"],
  "consolidation_notes": "Conflicts resolved using strictest requirement principle. ISO 27001 MFA requirement (12 chars) used over GDPR (8 chars) requirement.",
  "domains": [
    {
      "domain_name": "Access Control & Identity Management",
      "domain_description": "Unified requirements for access control, authentication, and identity lifecycle management across all frameworks.",
      "integrated_requirements": [
        {
          "requirement_id": "REQ-001",
          "title": "Multi-Factor Authentication (MFA) for Administrative Access",
          "description": "All administrative and privileged access must be protected with multi-factor authentication using at least two of the following factors: something you know (password), something you have (token/device), something you are (biometric).",
          "frameworks": ["iso-27001", "gdpr", "soc2"],
          "framework_references": [
            "ISO 27001:A.9.4.2",
            "GDPR Article 32(1)(b)",
            "SOC 2 CC6.2"
          ],
          "is_mandatory": true,
          "max_penalty": "€20 million (GDPR) or 4% annual revenue",
          "implementation_steps": [
            "Identify all administrative roles",
            "Select MFA solution (TOTP, hardware tokens, or biometric)",
            "Deploy and test MFA solution",
            "Create enforcement policy",
            "Train users and monitor compliance"
          ],
          "responsibility": "IT Security & IAM Team"
        },
        {
          "requirement_id": "REQ-002",
          "title": "Periodic Access Review",
          "description": "Conduct quarterly reviews of all user access rights to ensure principle of least privilege. Revoke access for users who no longer require it.",
          "frameworks": ["iso-27001", "gdpr"],
          "framework_references": [
            "ISO 27001:A.9.1",
            "GDPR Article 32(1)(a)"
          ],
          "is_mandatory": true,
          "implementation_steps": [
            "Schedule quarterly review cycle",
            "Generate access reports from all systems",
            "Distribute to managers for validation",
            "Revoke unnecessary access",
            "Document and audit changes"
          ],
          "responsibility": "IT Security & Line Managers"
        }
      ]
    },
    {
      "domain_name": "Data Protection & Privacy",
      "domain_description": "Consolidated requirements for personal data protection, privacy controls, and data lifecycle management.",
      "integrated_requirements": [
        {
          "requirement_id": "REQ-010",
          "title": "Data Classification System",
          "description": "Implement and maintain a data classification system that categorizes all organizational data by sensitivity level. Minimum classifications: Public, Internal, Confidential, Restricted.",
          "frameworks": ["gdpr", "iso-27001"],
          "framework_references": [
            "GDPR Article 32",
            "ISO 27001:A.8.2"
          ],
          "is_mandatory": true,
          "implementation_steps": [
            "Define classification levels",
            "Create classification policy",
            "Tag all existing data",
            "Train staff on classification",
            "Implement automated tagging"
          ],
          "responsibility": "Data Governance & Compliance Team"
        }
      ]
    }
  ],
  "compliance_matrix": [
    {
      "control_name": "Multi-Factor Authentication",
      "gdpr": "Required",
      "iso-27001": "Required",
      "soc2": "Mandatory"
    },
    {
      "control_name": "Data Encryption (In Transit)",
      "gdpr": "Mandatory",
      "iso-27001": "Required",
      "soc2": "Required"
    }
  ],
  "implementation_roadmap": [
    {
      "phase": 1,
      "duration": "Months 1-3",
      "focus": "Foundation and Quick Wins",
      "controls": [
        "Access Control Basics",
        "MFA Implementation",
        "Data Classification"
      ]
    },
    {
      "phase": 2,
      "duration": "Months 4-6",
      "focus": "Core Operational Controls",
      "controls": [
        "Data Protection Controls",
        "Third-Party Management",
        "Encryption Standards"
      ]
    },
    {
      "phase": 3,
      "duration": "Months 7-12",
      "focus": "Advanced and Continuous Monitoring",
      "controls": [
        "Compliance Monitoring",
        "Business Continuity",
        "Annual Review Process"
      ]
    }
  ],
  "created_at": "2026-07-01T10:30:00.123456",
  "updated_at": "2026-07-01T10:35:00.123456"
}
```

#### Error Responses

**404 - Not Found**
```json
{
  "detail": "Session not found"
}
```
OR
```json
{
  "detail": "No master policy found. Run consolidation first."
}
```

**500 - Server Error**
```json
{
  "detail": "Failed to retrieve master policy: [error details]"
}
```

#### Notes
- Retrieval is instant (policy is cached in database)
- Full policy structure with all requirements included
- Framework references are complete and traceable
- Ready for display in UI or further processing

#### Example Request
```bash
curl -X GET http://localhost:8000/policies/master/42 \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 3. POST `/export/master-policy/{session_id}/docx`

**Export the consolidated master policy as a professional DOCX file**

#### Authentication
- Required: Bearer token (JWT)
- Role Required: Any authenticated user with read access

#### Path Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_id` | integer | Yes | Session ID |

#### Success Response (200)
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="{org_name}_master_policy.docx"`
- Body: Binary DOCX file (typically 200-500KB)

#### Error Responses

**404 - Not Found**
```json
{
  "detail": "Session not found"
}
```
OR
```json
{
  "detail": "No master policy found. Run consolidation first."
}
```

**500 - Server Error**
```json
{
  "detail": "Export failed: [error details]"
}
```

#### Document Structure

The exported DOCX includes:

1. **Cover Page**
   - Document title and organization name
   - Aligned frameworks
   - Confidentiality notice
   - Document attributes table

2. **Executive Summary**
   - High-level compliance overview
   - Scope and objectives

3. **Master Policy Content**
   - One section per domain (8 domains)
   - Each domain includes:
     - Domain description
     - Integrated requirements (with all frameworks listed)
     - Implementation steps
     - Responsibility assignments
     - Framework citations

4. **Compliance Control Matrix**
   - Shows which frameworks require each control
   - Status per framework (Mandatory/Required)

5. **Implementation Roadmap**
   - Phase 1-3 breakdown
   - Duration and focus for each phase
   - Key controls per phase

6. **Professional Formatting**
   - Custom header/footer with org name and page numbers
   - Color-coded sections (dark blue headings, light blue tables)
   - Proper margins and spacing
   - Calibri font, professional styling

#### Notes
- Export takes 5-10 seconds
- File is immediately downloadable
- Can be opened in MS Word, LibreOffice, Google Docs
- Suitable for printing and distribution

#### Example Request (cURL)
```bash
curl -X POST http://localhost:8000/export/master-policy/42/docx \
  -H "Authorization: Bearer eyJhbGc..." \
  --output "Acme_Corp_master_policy.docx"
```

#### Example Request (JavaScript/Fetch)
```javascript
const response = await fetch('/export/master-policy/42/docx', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const blob = await response.blob();
const url = URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;
link.download = 'master_policy.docx';
link.click();
```

---

## Data Models

### MasterPolicyResponse

Complete response object for master policy.

```json
{
  "master_policy_id": "string",
  "title": "string",
  "version": "string (e.g., '1.0')",
  "executive_summary": "string",
  "aligned_frameworks": ["string"],
  "consolidation_notes": "string",
  "domains": [
    {
      "domain_name": "string",
      "domain_description": "string",
      "integrated_requirements": [
        {
          "requirement_id": "string",
          "title": "string",
          "description": "string",
          "frameworks": ["string"],
          "framework_references": ["string"],
          "is_mandatory": boolean,
          "max_penalty": "string (optional)",
          "implementation_steps": ["string"],
          "responsibility": "string"
        }
      ]
    }
  ],
  "compliance_matrix": [
    {
      "control_name": "string",
      "[framework_name]": "string (e.g., 'Mandatory', 'Required')"
    }
  ],
  "implementation_roadmap": [
    {
      "phase": integer,
      "duration": "string (e.g., 'Months 1-3')",
      "focus": "string",
      "controls": ["string"]
    }
  ],
  "created_at": "ISO 8601 timestamp (optional)",
  "updated_at": "ISO 8601 timestamp (optional)"
}
```

### ConsolidatedDomain

```json
{
  "domain_name": "string",
  "domain_description": "string",
  "integrated_requirements": [
    {
      "requirement_id": "string",
      "title": "string",
      "description": "string",
      "frameworks": ["string"],
      "framework_references": ["string"],
      "is_mandatory": boolean,
      "max_penalty": "string (optional)",
      "implementation_steps": ["string"],
      "responsibility": "string"
    }
  ]
}
```

### ConsolidatedRequirement

```json
{
  "requirement_id": "string",
  "title": "string",
  "description": "string",
  "frameworks": ["string"],
  "framework_references": ["string"],
  "is_mandatory": boolean,
  "max_penalty": "string (optional)",
  "implementation_steps": ["string"],
  "responsibility": "string"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Scenario |
|---|---|---|
| 200 | Success | Policy retrieved or consolidated successfully |
| 400 | Bad Request | Missing required fields or invalid session |
| 401 | Unauthorized | Invalid or missing authentication token |
| 403 | Forbidden | User lacks required role/permissions |
| 404 | Not Found | Session or policy not found |
| 500 | Server Error | Consolidation or export failed (with fallback) |

### Error Response Format

All errors return JSON:
```json
{
  "detail": "Error message explaining what went wrong"
}
```

### Common Error Scenarios

| Scenario | Status | Response |
|---|---|---|
| No token provided | 401 | `{"detail": "Not authenticated"}` |
| Invalid session ID | 404 | `{"detail": "Session not found"}` |
| Policies not generated yet | 400 | `{"detail": "No policies found for this session"}` |
| Consolidation already done | 200 | Returns existing policy |
| Export DOCX fails | 500 | `{"detail": "Export failed: [error]"}` |

---

## Authentication & Authorization

### Bearer Token Format
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Required Roles
- **Read**: ADMIN, COMPLIANCE_OFFICER, SECURITY_LEAD, EXECUTIVE, AUDITOR
- **Write**: ADMIN, COMPLIANCE_OFFICER (for consolidation)

### Token Acquisition
```bash
POST /login
{
  "email": "user@example.com",
  "password": "password123"
}

# Returns:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Rate Limiting

No explicit rate limiting on master policy endpoints.

### Considerations
- Consolidation takes 30-60 seconds
- Typical usage: 1-2 consolidations per session
- Export typically takes 5-10 seconds
- Database caches master policies for instant retrieval

### Thread Pool
- Max 4 concurrent consolidations
- Prevents system overload
- Returns immediately (background processing)

---

## Pagination & Filtering

No pagination needed (master policy is singular per session).

### Available Queries
```bash
# Get master policy (singular)
GET /policies/master/{session_id}

# Check if master policy exists
GET /policies/master/{session_id}  # 404 if not exists

# Consolidate (creates if not exists)
POST /policies/consolidate {session_id, regenerate}
```

---

## Examples

### Complete Workflow Example (Python)

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# Authentication
auth_response = requests.post(
    f"{BASE_URL}/login",
    json={"email": "user@example.com", "password": "password"}
)
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. Profile organization
org_response = requests.post(
    f"{BASE_URL}/profile",
    headers=headers,
    json={
        "description": "FinTech SaaS platform",
        "country": "USA"
    }
)
session_id = org_response.json()["session_id"]
print(f"✓ Session created: {session_id}")

# 2. Generate policies for each framework
frameworks = ["gdpr", "iso-27001", "soc2"]
for framework in frameworks:
    response = requests.post(
        f"{BASE_URL}/policies/generate",
        headers=headers,
        json={
            "framework": framework,
            "org_name": "TechCorp",
            "org_description": "FinTech SaaS platform",
            "policy_types": ["data_protection", "incident_response", "access_control"],
            "session_id": session_id
        }
    )
    print(f"✓ Generated {framework} policies")

# 3. Consolidate into master policy
consolidation = requests.post(
    f"{BASE_URL}/policies/consolidate",
    headers=headers,
    json={"session_id": session_id, "regenerate": False}
)
master_id = consolidation.json()["master_policy_id"]
print(f"✓ Consolidated: {master_id}")

# 4. Get master policy details
master = requests.get(
    f"{BASE_URL}/policies/master/{session_id}",
    headers=headers
).json()

print(f"✓ Domains: {len(master['domains'])}")
print(f"✓ Frameworks: {', '.join(master['aligned_frameworks'])}")
print(f"✓ Roadmap phases: {len(master['implementation_roadmap'])}")

# 5. Export to DOCX
export = requests.post(
    f"{BASE_URL}/export/master-policy/{session_id}/docx",
    headers=headers
)
with open(f"{session_id}_master_policy.docx", "wb") as f:
    f.write(export.content)
print(f"✓ Exported: {session_id}_master_policy.docx")
```

### Frontend Integration Example (TypeScript/React)

```typescript
interface MasterPolicyState {
  sessionId: number;
  masterPolicy: MasterPolicyResponse | null;
  loading: boolean;
  error: string | null;
}

async function consolidatePolicies(sessionId: number) {
  try {
    const response = await fetch('/policies/consolidate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        session_id: sessionId,
        regenerate: false
      })
    });

    if (!response.ok) throw new Error(await response.text());
    
    const result = await response.json();
    console.log(`✓ Master policy created: ${result.master_policy_id}`);
    
    // Fetch full policy details
    const policyResponse = await fetch(`/policies/master/${sessionId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const masterPolicy = await policyResponse.json();
    return masterPolicy;
  } catch (error) {
    console.error('Consolidation failed:', error);
    throw error;
  }
}

async function downloadMasterPolicy(sessionId: number) {
  try {
    const response = await fetch(`/export/master-policy/${sessionId}/docx`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Export failed');
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `master_policy.docx`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
}
```

---

## FAQ

**Q: How long does consolidation take?**
A: Typically 30-60 seconds depending on number of frameworks and policies. First consolidation may be slower due to LLM initialization.

**Q: What if consolidation fails?**
A: System automatically falls back to simple consolidation by merging policies by domain. User gets valid master policy.

**Q: Can I regenerate the master policy?**
A: Yes, use `POST /policies/consolidate` with `regenerate: true`. Deletes existing and creates new.

**Q: Is master policy always created?**
A: Only after `POST /policies/consolidate` is called. It's an explicit action, not automatic.

**Q: Can I update the master policy later?**
A: Currently policies are static. To change, regenerate with updated individual policies.

**Q: What frameworks are supported?**
A: Works with any combination of: GDPR, ISO 27001, HIPAA, SOC2, NIST CSF, PCI DSS, FedRAMP, DPDP, SOX, etc.

**Q: Is the master policy per organization or per session?**
A: Per session. Each profiling/generation run can have its own master policy.

**Q: Can I see what changed during consolidation?**
A: Check `consolidation_notes` field in master policy. Shows conflict resolutions.

---

## Support

For API issues or questions:
1. Check this reference documentation
2. Review error messages returned by endpoints
3. Check server logs for detailed error information
4. Test endpoints with curl/Postman first
5. Contact development team if needed

---

## Version

API Version: 1.0
Last Updated: July 2026
