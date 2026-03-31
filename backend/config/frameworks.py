"""
Compliance Frameworks Registry
All supported frameworks with metadata for org-type matching.
"""

from typing import Dict, List, Any

# ─── Framework Definitions ───────────────────────────────────────────────────

FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "GDPR": {
        "name": "General Data Protection Regulation",
        "region": "EU/EEA",
        "authority": "European Data Protection Board (EDPB)",
        "version": "2016/679",
        "color": "#3B82F6",
        "icon": "🇪🇺",
        "description": "EU regulation for data protection and privacy of individuals.",
        "applies_to": [
            "eu_operations", "eu_customers", "personal_data", "healthcare",
            "ecommerce", "saas", "fintech", "hr_systems", "analytics"
        ],
        "industries": [
            "healthcare", "finance", "ecommerce", "saas", "retail",
            "education", "government", "media", "telecom", "insurance"
        ],
        "triggers": ["eu", "europe", "gdpr", "personal data", "privacy", "international"],
        "key_articles": ["Article 5", "Article 6", "Article 32", "Article 33", "Article 34", "Article 83"],
        "max_fine": "€20M or 4% annual turnover",
        "notification_window": "72 hours",
    },

    "HIPAA": {
        "name": "Health Insurance Portability and Accountability Act",
        "region": "United States",
        "authority": "U.S. Department of Health & Human Services (HHS)",
        "version": "45 CFR Parts 160 & 164",
        "color": "#10B981",
        "icon": "🏥",
        "description": "US law protecting sensitive patient health information.",
        "applies_to": [
            "healthcare", "medical_records", "phi", "health_insurance",
            "telemedicine", "medical_devices", "lab_results", "prescriptions"
        ],
        "industries": [
            "healthcare", "hospitals", "clinics", "insurance", "pharma",
            "medical_devices", "health_tech", "telemedicine", "biotech"
        ],
        "triggers": ["health", "medical", "hospital", "clinic", "patient", "phi", "hipaa", "healthcare"],
        "key_articles": ["Privacy Rule", "Security Rule", "Breach Notification Rule", "HITECH Act"],
        "max_fine": "$1.9M per violation category annually",
        "notification_window": "60 days",
    },

    "ISO27001": {
        "name": "ISO/IEC 27001:2022 Information Security Management",
        "region": "International",
        "authority": "International Organization for Standardization (ISO)",
        "version": "ISO/IEC 27001:2022",
        "color": "#6366F1",
        "icon": "🔒",
        "description": "International standard for information security management systems.",
        "applies_to": [
            "information_security", "isms", "data_protection", "risk_management",
            "cloud_services", "outsourcing", "supply_chain", "it_services"
        ],
        "industries": [
            "technology", "finance", "government", "defense", "telecom",
            "consulting", "manufacturing", "logistics", "energy", "saas"
        ],
        "triggers": ["security", "iso", "information", "isms", "certification", "technology", "it"],
        "key_articles": ["Clause 4-10", "Annex A Controls", "Control 5.24", "Control 8.12"],
        "max_fine": "Loss of certification",
        "notification_window": "Immediate incident management",
    },

    "NIST_CSF": {
        "name": "NIST Cybersecurity Framework 2.0",
        "region": "United States (Global Adoption)",
        "authority": "National Institute of Standards and Technology (NIST)",
        "version": "CSF 2.0",
        "color": "#F59E0B",
        "icon": "🛡️",
        "description": "Framework for improving critical infrastructure cybersecurity.",
        "applies_to": [
            "critical_infrastructure", "federal_agencies", "cybersecurity",
            "risk_management", "incident_response", "supply_chain"
        ],
        "industries": [
            "government", "defense", "energy", "finance", "healthcare",
            "manufacturing", "transportation", "water", "technology"
        ],
        "triggers": ["government", "federal", "nist", "cyber", "critical", "infrastructure", "defense"],
        "key_articles": ["Govern", "Identify", "Protect", "Detect", "Respond", "Recover"],
        "max_fine": "Contract penalties, federal funding loss",
        "notification_window": "Varies by agency",
    },

    "PCI_DSS": {
        "name": "Payment Card Industry Data Security Standard",
        "region": "Global",
        "authority": "PCI Security Standards Council",
        "version": "PCI DSS v4.0",
        "color": "#EF4444",
        "icon": "💳",
        "description": "Security standards for organizations handling payment card data.",
        "applies_to": [
            "payment_processing", "card_data", "ecommerce", "pos_systems",
            "payment_gateways", "card_storage", "merchant", "acquiring"
        ],
        "industries": [
            "ecommerce", "retail", "hospitality", "finance", "payment_processors",
            "banks", "merchants", "pos_vendors", "saas_payments"
        ],
        "triggers": ["payment", "credit card", "ecommerce", "retail", "merchant", "pos", "transaction"],
        "key_articles": ["Req 1-12", "SAQ", "ROC", "Network Segmentation"],
        "max_fine": "$5,000-$100,000/month from card brands",
        "notification_window": "Immediately to acquiring bank",
    },

    "SOC2": {
        "name": "SOC 2 Type II — Trust Service Criteria",
        "region": "United States (Global Recognition)",
        "authority": "American Institute of CPAs (AICPA)",
        "version": "2017 Trust Service Criteria",
        "color": "#8B5CF6",
        "icon": "📋",
        "description": "Audit standard for service organizations on security and availability.",
        "applies_to": [
            "saas", "cloud_services", "data_processing", "managed_services",
            "b2b_software", "enterprise_software", "hosting"
        ],
        "industries": [
            "saas", "cloud", "technology", "consulting", "finance",
            "hr_tech", "analytics", "data_services", "managed_services"
        ],
        "triggers": ["saas", "cloud", "b2b", "enterprise", "software", "service", "audit"],
        "key_articles": ["CC1-CC9", "Availability", "Confidentiality", "Processing Integrity", "Privacy"],
        "max_fine": "Client contract penalties, lost business",
        "notification_window": "Per contractual SLAs",
    },

    "CCPA": {
        "name": "California Consumer Privacy Act / CPRA",
        "region": "California, USA",
        "authority": "California Privacy Protection Agency (CPPA)",
        "version": "CCPA + CPRA 2023",
        "color": "#F97316",
        "icon": "🌴",
        "description": "California privacy law granting consumers rights over personal data.",
        "applies_to": [
            "california_consumers", "personal_information", "data_brokers",
            "large_businesses", "data_selling", "targeted_advertising"
        ],
        "industries": [
            "technology", "retail", "media", "advertising", "finance",
            "ecommerce", "data_brokers", "insurance", "automotive"
        ],
        "triggers": ["california", "us", "consumer", "data broker", "advertising", "privacy", "ccpa"],
        "key_articles": ["Right to Know", "Right to Delete", "Right to Opt-Out", "Right to Correct"],
        "max_fine": "$7,500 per intentional violation",
        "notification_window": "72 hours for security breach",
    },

    "DPDP": {
        "name": "Digital Personal Data Protection Act 2023",
        "region": "India",
        "authority": "Data Protection Board of India",
        "version": "DPDP Act 2023",
        "color": "#EC4899",
        "icon": "🇮🇳",
        "description": "India's comprehensive data protection law for digital personal data.",
        "applies_to": [
            "india_operations", "indian_users", "personal_data", "data_fiduciary",
            "cross_border_transfer", "consent_management"
        ],
        "industries": [
            "technology", "fintech", "ecommerce", "healthcare", "banking",
            "telecom", "education", "government", "manufacturing"
        ],
        "triggers": ["india", "indian", "dpdp", "data fiduciary", "rupee", "bharat"],
        "key_articles": ["Data Principal Rights", "Consent", "Data Fiduciary Obligations", "Cross-Border Transfer"],
        "max_fine": "₹250 crores per violation",
        "notification_window": "Prompt notification to Data Protection Board",
    },

    "SOX": {
        "name": "Sarbanes-Oxley Act",
        "region": "United States",
        "authority": "Securities and Exchange Commission (SEC)",
        "version": "SOX 2002",
        "color": "#14B8A6",
        "icon": "📊",
        "description": "US law on financial reporting and corporate accountability.",
        "applies_to": [
            "public_companies", "financial_reporting", "audit_controls",
            "internal_controls", "it_controls", "financial_data"
        ],
        "industries": [
            "finance", "banking", "public_companies", "accounting",
            "investment", "insurance", "real_estate", "manufacturing"
        ],
        "triggers": ["public company", "listed", "sec", "financial", "audit", "sox", "stock exchange"],
        "key_articles": ["Section 302", "Section 404", "Section 409", "Section 802"],
        "max_fine": "$5M fine or 20 years imprisonment",
        "notification_window": "Real-time disclosure of material changes",
    },

    "FedRAMP": {
        "name": "Federal Risk and Authorization Management Program",
        "region": "United States Federal Government",
        "authority": "GSA / Joint Authorization Board (JAB)",
        "version": "FedRAMP 2024",
        "color": "#0EA5E9",
        "icon": "🏛️",
        "description": "Security assessment for cloud services used by US federal agencies.",
        "applies_to": [
            "federal_agencies", "cloud_services_federal", "government_contracts",
            "saas_government", "infrastructure_government"
        ],
        "industries": [
            "government_tech", "defense_contractors", "cloud_providers",
            "federal_contractors", "national_security"
        ],
        "triggers": ["federal", "government contract", "fedramp", "dod", "us government", "agency"],
        "key_articles": ["Low/Moderate/High Baselines", "NIST SP 800-53", "Continuous Monitoring"],
        "max_fine": "Contract termination, debarment",
        "notification_window": "1 hour for security incidents",
    },
}

# ─── Industry → Framework Mapping ────────────────────────────────────────────
INDUSTRY_FRAMEWORK_MAP: Dict[str, List[str]] = {
    "healthcare": ["HIPAA", "GDPR", "ISO27001", "SOC2"],
    "finance": ["SOX", "PCI_DSS", "GDPR", "ISO27001", "SOC2"],
    "ecommerce": ["PCI_DSS", "GDPR", "CCPA", "SOC2"],
    "saas": ["SOC2", "ISO27001", "GDPR", "CCPA"],
    "government": ["FedRAMP", "NIST_CSF", "FISMA", "ISO27001"],
    "banking": ["SOX", "PCI_DSS", "GDPR", "ISO27001", "NIST_CSF"],
    "technology": ["SOC2", "ISO27001", "GDPR", "CCPA", "NIST_CSF"],
    "retail": ["PCI_DSS", "GDPR", "CCPA", "SOC2"],
    "education": ["FERPA", "GDPR", "ISO27001"],
    "pharma": ["HIPAA", "GDPR", "ISO27001", "GxP"],
    "insurance": ["HIPAA", "SOX", "GDPR", "ISO27001"],
    "india": ["DPDP", "ISO27001", "SOC2"],
    "manufacturing": ["ISO27001", "NIST_CSF", "SOX"],
}

ALL_FRAMEWORK_IDS = list(FRAMEWORKS.keys())


def get_framework(framework_id: str) -> Dict[str, Any]:
    """Get framework metadata by ID."""
    if framework_id not in FRAMEWORKS:
        raise KeyError(f"Unknown framework: {framework_id}")
    return FRAMEWORKS[framework_id]


def get_all_frameworks() -> List[Dict[str, Any]]:
    """Get all frameworks as list with IDs included."""
    return [{"id": k, **v} for k, v in FRAMEWORKS.items()]
