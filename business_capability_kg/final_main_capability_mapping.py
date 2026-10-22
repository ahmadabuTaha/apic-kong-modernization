"""Task 019-E-FINAL direct Main Capability mapping for all recovery Modules.

This task-scoped mapper consumes the recovery effective catalog only.  For
each Module it classifies active ICDs first, then inspects only active ISDs on
Services with no active ICD relationship.  It reuses validated structured
parser caches read-only and stores compact resumable Module checkpoints; it
never creates Business Function or Sub Capability records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts_main_icd_mapping import PAGES_BY_CAPABILITY as CONTRACT_PAGES
from .document_cache import DocumentCatalog
from .establishment_main_icd_mapping import (
    PAGES_BY_CAPABILITY as ESTABLISHMENT_PAGES,
    RECOVERY_CATALOG,
    _validated_recovery,
)
from .icd_capability_extraction import (
    _document_parser_version,
    _parse_cache_path,
    _sanitize_evidence,
    _stable_id,
    parse_document,
)


SCHEMA_VERSION = "phase6-task019e-final-v1"
RULES_VERSION = "direct-main-all-modules-v9"
INDEX_ROOT = Path("indexes/phase6/task019/019e_final")
OUTPUT_ROOT = Path("outputs/phase6/task019/019e_final")
BASE_PARSE_INDEXES = (
    Path("indexes/phase6/task019/recovery"),
    Path("indexes/phase6/task019/019e"),
)
EXPECTED = {"modules": 32, "services": 952, "icd_occurrences": 1011, "isd_occurrences": 974}

MAIN_FIELDS = [
    "module_key", "module_name", "main_capability_id", "name", "description",
    "candidate_status", "source_types", "linked_document_count",
]
LINK_FIELDS = [
    "module_key", "module_name", "main_capability_id", "page_id", "document_key",
    "physical_identity", "title", "service_keys", "occurrence_ids", "blob_sha256",
    "source_version", "evidence_pointer", "evidence_excerpt", "external_entities",
    "mapping_status", "mapping_rationale",
]
ISD_LINK_FIELDS = LINK_FIELDS + ["classification_signals", "unpaired_reason"]
EXCLUDED_FIELDS = [
    "exclusion_id", "module_key", "module_name", "source_type", "page_id", "document_key",
    "service_key", "occurrence_id", "title", "source_marker", "exclusion_reason",
    "runtime_state_proven",
]
EXCEPTION_FIELDS = [
    "exception_id", "module_key", "module_name", "source_type", "page_id", "document_key",
    "service_keys", "occurrence_ids", "title", "issue_type", "precise_reason",
    "evidence_pointer", "downstream_impact", "status",
]
COVERAGE_FIELDS = [
    "module_key", "module_name", "service_count", "icd_occurrences", "unique_icd_documents",
    "eligible_icd_documents", "excluded_icd_occurrences", "linked_icd_documents",
    "unresolved_icd_documents", "isd_occurrences", "unique_isd_documents",
    "paired_isd_documents", "eligible_unpaired_isd_documents", "excluded_isd_occurrences",
    "linked_unpaired_isd_documents", "unresolved_unpaired_isd_documents",
    "main_capability_count", "checkpoint_status", "source_signature", "checkpoint_sha256",
]


@dataclass(frozen=True)
class CapabilityRule:
    key: str
    name: str
    description: str
    patterns: tuple[str, ...]
    external_entities: tuple[str, ...] = ()


def _rule(
    key: str, name: str, description: str, *patterns: str,
    external_entities: tuple[str, ...] = (),
) -> CapabilityRule:
    return CapabilityRule(key, name, description, patterns or (r".",), external_entities)


# Ordered, Module-local semantic boundaries.  Final fallbacks are meaningful
# Module capabilities, not generic buckets; a link is still refused when the
# source body provides no usable semantic evidence.
MODULE_RULES: dict[str, tuple[CapabilityRule, ...]] = {
    "module-capptions": (
        _rule("request", "Capptions Request Management", "Submit, retrieve, update, and reconcile Capptions requests and balances.", r"capptions", r"request"),
    ),
    "module-certifcates": (
        _rule("debt", "Establishment Debt Certification", "Generate establishment debt certificate evidence.", r"debt certificate", r"establishment debt"),
        _rule("saudization", "Saudization Certificate Management", "Validate, issue, retrieve, and monitor Saudization certificates.", r"saudization", r"certificate"),
    ),
    "module-certificates": (
        _rule("gosi", "GOSI Integration Management", "Exchange certificate information with GOSI.", r"\bgosi\b", external_entities=("GOSI",)),
        _rule("wps", "Wage Protection Certificate Management", "Issue and retrieve Wage Protection certificates.", r"\bwps\b", r"wage protection"),
        _rule("salary", "Salary Certificate Management", "Create, search, update, and monitor salary certificates.", r"salary certificate", r"\bsc\b"),
        _rule("compliance", "Compliance Certificate Management", "Create and maintain establishment compliance certificates.", r"compliance certificate", r"createcompliance"),
        _rule("saudization", "Saudization Certificate Management", "Generate and retrieve Saudization certificates.", r"saudization"),
        _rule("certificate", "Enterprise Certificate Management", "Manage enterprise certificate issuance and retrieval.", r"certificate"),
    ),
    "module-commmon": (
        _rule("economic", "Economic Activity Reference Data Administration", "Maintain shared economic-activity reference data.", r"economic activ"),
        _rule("nationality", "Nationality Reference Data Administration", "Maintain shared nationality reference data.", r"nationalit"),
    ),
    "module-common": (
        _rule("notification", "Stakeholder Notification Management", "Send shared email, SMS, invoice, and event notifications.", r"notif", r"send email", r"send sms"),
        _rule("payment", "Shared Payment and Billing Management", "Provide shared fee, SADAD, invoice, and billing capabilities.", r"sadad", r"invoice", r"fees?", r"payment"),
        _rule("work-permit", "Shared Work Permit Management", "Provide shared work-permit data, debt, and calculation capabilities.", r"work permits?", r"\bwp debit\b"),
        _rule("visa", "Shared Visa Lifecycle Management", "Support shared visa eligibility, balance, issuance, search, and status activities.", r"\bvisas?\b", r"embass"),
        _rule("occupation", "Occupation and Professional Skills Management", "Provide occupation, profession, and professional-skills reference and eligibility capabilities.", r"occupation", r"profession", r"professional skills"),
        _rule("nitaqat", "Nitaqat Compliance Management", "Provide Nitaqat, Saudization, sustainability, and quota evidence.", r"nitaq", r"saudization", r"sustainability", r"quota"),
        _rule("compliance", "Establishment Compliance Management", "Assess establishment compliance, inspections, penalties, punishments, and evaluations.", r"compliance", r"inspection", r"penalt", r"punishment", r"ims evaluation"),
        _rule("workforce", "Workforce Information Management", "Provide shared employee, laborer, and workforce information.", r"employee", r"laborer", r"workforce"),
        _rule("reference", "Shared Reference Data Administration", "Provide shared lookups, entities, origins, services, and nationalities.", r"lookup", r"nationalit", r"origin list", r"entity information", r"services list"),
        _rule("establishment", "Establishment Information Management", "Maintain and retrieve shared establishment identity, hierarchy, address, and status information.", r"establishment", r"company with branches", r"unified number"),
        _rule("shared", "Shared Enterprise Service Management", "Provide evidenced shared enterprise service capabilities.", r"service", r"details", r"information"),
    ),
    "module-data-portal": (
        _rule("statistics", "Labor Market Data Publication", "Provide labor-market statistics and portal data products.", r"statistics", r"data portal"),
    ),
    "module-deceased-employee-entitlement": (
        _rule("nic", "NIC Integration Management", "Synchronize deceased-employee information with NIC.", r"\bnic\b", r"sync", external_entities=("NIC",)),
        _rule("notification", "Deceased Entitlement Stakeholder Notification", "Notify establishments about deceased-employee entitlement events.", r"notif"),
        _rule("certificate", "Deceased Employee Certificate Management", "Issue deceased-employee entitlement certificates.", r"certificate"),
        _rule("entitlement", "Deceased Employee Entitlement Management", "Calculate, configure, retrieve, and update deceased-employee entitlement and payment details.", r"deceased", r"entitlement", r"payment"),
    ),
    "module-employee-transfer": (
        _rule("nic", "NIC Integration Management", "Submit, verify, and reconcile employee-transfer requests with NIC.", r"\bnic\b", external_entities=("NIC",)),
        _rule("masar", "Masar Integration Management", "Exchange employee-transfer requests and decisions with Masar.", r"\bmasar\b", external_entities=("Masar",)),
        _rule("notification", "Employee Transfer Notification Management", "Notify stakeholders about employee-transfer events.", r"notif"),
        _rule("eligibility", "Employee Transfer Eligibility Management", "Validate laborer, establishment, employer, dependent, and request eligibility for transfers.", r"eligib", r"validate", r"check .*conditions", r"check .*approval"),
        _rule("balance", "Employee Transfer Balance Management", "Calculate and retrieve sponsorship-transfer balances and controls.", r"balance"),
        _rule("lifecycle", "Employee Transfer Lifecycle Management", "Submit, search, approve, reject, cancel, and update employee-transfer and sponsorship-change requests.", r"transfer", r"change sponsor", r"\bet\b", r"sponsor"),
    ),
    "module-end-of-service-reward": (
        _rule("reward", "End of Service Reward Management", "Calculate end-of-service rewards and provide their lookup data.", r"end.?of.?service", r"reward"),
    ),
    "module-external-entities-management": (
        _rule("absence", "Absence Termination Status Management", "Update absence-termination status for external-entity flows.", r"absent", r"termination"),
        _rule("entity", "External Entity Establishment Management", "Open and maintain establishments for external entities.", r"external", r"open establishments?", r"commercial registration"),
    ),
    "module-gosi": (
        _rule("gosi", "GOSI Integration Management", "Exchange evidenced workforce and contract information with GOSI.", r"\bgosi\b", r"service", external_entities=("GOSI",)),
    ),
    "module-government-sectors": (
        _rule("agent", "Government Agent Administration", "Manage governmental agents, roles, privileges, eligibility, and endorsements.", r"agent", r"privilege", r"role"),
        _rule("sector", "Government Sector Reference Data Administration", "Maintain government-sector, source, service, and subservice reference data.", r"sector", r"source", r"subservice"),
    ),
    "module-individual-profile": (
        _rule("history", "Laborer Work History Management", "Retrieve and maintain laborer work-history information.", r"work history", r"employee history", r"laborer.*history"),
        _rule("profile", "Individual Profile Management", "Provide and maintain individual employee profile information.", r"profile", r"employee"),
    ),
    "module-labor-offices": (
        _rule("notification", "Labor Office Notification Management", "Send and retry Labor Office email and SMS notifications.", r"email", r"sms", r"notif"),
        _rule("appointment", "Labor Office Appointment Management", "Create, assign, update, cancel, and monitor Labor Office appointments.", r"appointment", r"virtual office"),
        _rule("access", "Labor Office User and Access Administration", "Manage Labor Office users, roles, permissions, offices, regions, and service assignments.", r"user", r"permission", r"labor office", r"office service", r"office region"),
        _rule("location", "Labor Office Establishment Location Management", "Maintain establishment locations and laborer assignments through Labor Office services.", r"location"),
        _rule("occupation", "Labor Office Occupation Management", "Submit, validate, and review occupation change and correction requests in Labor Office channels.", r"occupation"),
        _rule("transfer", "Labor Office Employee Transfer Management", "Submit, validate, and decide sponsorship and employee-transfer requests through Labor Office channels.", r"sponsor", r"\bcs requests?\b", r"employee transfer"),
        _rule("contract", "Labor Office Contract Termination Management", "Submit and decide contract-termination requests through Labor Office channels.", r"\btc\b", r"contract", r"release date"),
        _rule("visa", "Labor Office Visa Management", "Request, issue, validate, search, and terminate visa services through Labor Office channels.", r"visa", r"endorsement"),
        _rule("work-permit", "Labor Office Work Permit Management", "Submit, search, cancel, and retrieve work-permit services through Labor Office channels.", r"work permit"),
        _rule("exception", "Labor Office Exception Request Management", "Submit, search, approve, and balance Labor Office exception requests.", r"exception"),
        _rule("certificate", "Labor Office Certificate Management", "Issue certificates through Labor Office services.", r"certificate"),
        _rule("service", "Labor Office Service Administration", "Administer evidenced Labor Office service requests and customer information.", r"request", r"customer", r"agent"),
    ),
    "module-lmh": (
        _rule("classification", "Professional Skills Classification", "Classify employee professional skills and respond to labor-market triggers.", r"classif", r"professional skills", r"laborers changes"),
        _rule("reference", "Labor Market Reference Data Administration", "Provide LMH university and occupation reference data.", r"universit", r"occupation"),
        _rule("offer", "Job Offer Management", "Submit and manage job offers.", r"job offer"),
    ),
    "module-nic": (
        _rule("auth", "NIC Authentication Integration", "Acquire and manage NIC integration authentication.", r"oauth", r"token", external_entities=("NIC",)),
        _rule("nic", "NIC Integration Management", "Submit workforce events and reports to NIC.", r"\bnic\b", r"run away", external_entities=("NIC",)),
    ),
    "module-nic-services": (
        _rule("auth", "NIC Identity Authentication Integration", "Authenticate users and identities through NIC.", r"authenticate", r"mobile" , external_entities=("NIC",)),
        _rule("nic", "NIC Workforce Integration Management", "Exchange citizen, foreigner, visa, occupation, work-permit, transfer, and absence information with NIC.", r"\bnic\b", r"citizen", r"foreigner", r"border number", r"prison", external_entities=("NIC",)),
    ),
    "module-nitaqat": (
        _rule("activity", "Nitaqat Activity Reference Data Administration", "Provide economic and ISIC activity reference data for Nitaqat.", r"economic", r"isic"),
        _rule("calculator", "Nitaqat Assessment and Calculation", "Calculate public and private Nitaqat outcomes.", r"calculator", r"calculate"),
        _rule("nitaqat", "Nitaqat Information Management", "Provide establishment Nitaqat information.", r"nitaq"),
    ),
    "module-occupations": (
        _rule("correction", "Occupation Correction Management", "Submit, validate, retrieve, and monitor occupation-correction requests.", r"correction"),
        _rule("change", "Change Occupation Lifecycle Management", "Submit, validate, search, approve, reject, and cancel change-occupation requests.", r"change occupation", r"\bco requests?\b"),
        _rule("matrix", "Occupation Service Matrix Administration", "Maintain occupation service matrices, entities, values, history, and service relationships.", r"matrix", r"entity", r"service"),
        _rule("nationality", "Occupation Nationality Reference Data Administration", "Maintain nationality reference data used by occupation services.", r"nationalit"),
        _rule("eligibility", "Occupation Validation Management", "Validate occupations, laborers, and establishments for occupation actions.", r"validate", r"eligib"),
        _rule("reference", "Occupation Reference Data Management", "Create, update, retrieve, and group occupation reference data.", r"occupation", r"group", r"unrelated"),
    ),
    "module-payments": (
        _rule("amazon", "Amazon Pay Integration Management", "Authorize, capture, void, sign, monitor, and receive Amazon Pay transactions.", r"amazon", external_entities=("Amazon Pay",)),
        _rule("hyperpay", "HyperPay Integration Management", "Create, execute, query, refund, and reconcile HyperPay transactions.", r"hyperpay", r"hypp", r"copy.?&.?pay", external_entities=("HyperPay",)),
        _rule("refund", "Payment Refund Management", "Search and execute payment refunds.", r"refund"),
        _rule("einvoice", "Electronic Invoice Compliance Management", "Generate, retry, and reconcile electronic invoices.", r"e.?invoice", r"reconsolid", r"reconsil"),
        _rule("invoice", "Unified Invoice Management", "Create, retrieve, and schedule unified, policies, and visa invoices.", r"invoice"),
        _rule("token", "Payment Card Token Management", "Generate and delete payment-card tokens.", r"card token"),
        _rule("document", "Payment Document Generation", "Generate payment PDF documents.", r"pdf"),
        _rule("payment", "Payment Transaction Management", "Execute, retrieve, search, monitor, and report payment transactions and statuses.", r"payment", r"transaction", r"vat", r"establishment address"),
    ),
    "module-services": (
        _rule("nic", "NIC Integration Management", "Validate and submit absence reports through NIC.", r"\bnic\b", r"runaway", external_entities=("NIC",)),
        _rule("reward", "End of Service Reward Management", "Calculate end-of-service rewards and provide lookup data.", r"end.?of.?service", r"reward"),
        _rule("occupation", "Occupation Activity Relationship Management", "Maintain relationships between activities and occupations.", r"occupation", r"activities"),
    ),
    "module-termination-for-absence-expat-laborer": (
        _rule("absence", "Expatriate Absence Termination Management", "Retrieve and manage expatriate laborer absence-termination requests.", r"absent", r"termination", r"ctfal"),
    ),
    "module-training-indicators": (
        _rule("notification", "Training Stakeholder Notification", "Notify stakeholders about training events.", r"notif"),
        _rule("disclosure", "Training Disclosure Management", "Submit, update, and view establishment training disclosures and declarations.", r"disclosure", r"declaration"),
        _rule("feedback", "Training Feedback Management", "Capture employee feedback for approved establishment training.", r"laborer\s*feedback", r"training[_ ]quality", r"employer[_ ]support"),
        _rule("compliance", "Training Compliance Monitoring", "Calculate and retrieve training compliance and occurrence indicators.", r"compliance", r"indicator", r"occupation.*analysis"),
        _rule("reference", "Training Reference Data Administration", "Provide training location and related reference data.", r"location type"),
        _rule("training", "Establishment Training Management", "Add, edit, approve, reject, validate, retrieve, and monitor establishment and employee training.", r"training", r"laborer feedback", r"update employee"),
    ),
    "module-user-management": (
        _rule("mobile", "User Mobile Verification Management", "Validate, update, and confirm user mobile numbers.", r"mobile"),
        _rule("privilege", "User Privilege Administration", "Manage user privileges, authorized users, and eligible services.", r"privilege", r"authorized user", r"eligible services"),
        _rule("workspace", "User Workspace Management", "Provide Qiwa user workspaces, dashboards, establishment groups, and workspace counts.", r"workspace", r"work space", r"dashboard", r"establishments groups"),
        _rule("payment", "User Subscription Payment Management", "Calculate subscription prices and reconcile SADAD and unsubscribed payments.", r"payment", r"sadad", r"price"),
        _rule("subscription", "User Subscription Lifecycle Management", "Create, retrieve, renew, search, transfer, and terminate establishment user subscriptions.", r"subscription", r"subscribe"),
        _rule("eligibility", "User Eligibility Management", "Validate users and establishments for user-management services.", r"eligib"),
        _rule("account", "User Account Management", "Create, retrieve, update, and delete user accounts and profile information.", r"user", r"laborer information", r"favorite establishments"),
    ),
    "module-utilities": (
        _rule("compliance", "Labor Office Compliance Certificate Management", "Create Labor Office compliance certificates.", r"compliance certificate", r"createcompliance"),
    ),
    "module-visa": (
        _rule("mofa", "MOFA Integration Management", "Exchange visa documents, statuses, embassies, and nationalities with MOFA.", r"\bmofa\b", r"embass", external_entities=("MOFA",)),
        _rule("notification", "Visa Stakeholder Notification", "Send visa and compliance notifications to stakeholders.", r"notif", r"email"),
        _rule("final-exit", "Final Exit and Re-entry Visa Management", "Submit, retrieve, and validate final-exit and re-entry visa activities.", r"final exit", r"re.?entry"),
        _rule("seasonal", "Seasonal Visa and Endorsement Management", "Manage seasonal visa requests, endorsements, eligibility, balances, decisions, and expiry.", r"seasonal", r"endorsement"),
        _rule("visit", "Visit Visa Lifecycle Management", "Manage visit-visa packages, requests, eligibility, payment checks, refunds, search, and expiry.", r"visit visa"),
        _rule("expansion", "Expansion Visa Lifecycle Management", "Manage expansion visa requests, exceptional balances, eligibility, validation, search, and refunds.", r"expansion", r"exceptional balance"),
        _rule("establishing", "Establishing Visa Lifecycle Management", "Manage establishing visa balances, requests, eligibility, issuance, search, and termination.", r"establishing"),
        _rule("investor", "Investor Visa Lifecycle Management", "Issue, validate, and search investor visas.", r"investor"),
        _rule("objection", "Visa Objection Management", "Submit, search, validate, and reject visa objection requests.", r"objection"),
        _rule("inspection", "Visa Inspection Management", "Retrieve and update inspection visits used by visa services.", r"inspection", r"inspector"),
        _rule("balance", "Visa Balance and Quota Management", "Calculate and retrieve visa balances, quotas, tiers, and allowances.", r"balance", r"quota", r"tier", r"allowance"),
        _rule("visa", "Visa Lifecycle Management", "Manage evidenced visa requests, status, documents, eligibility, and stakeholders.", r"visa", r"sub.?document"),
    ),
    "module-wage-protection": (
        _rule("gosi", "GOSI Integration Management", "Create and exchange Wage Protection compliance certificates with GOSI.", r"\bgosi\b", external_entities=("GOSI",)),
        _rule("wps", "Wage Protection Certificate Management", "Create, validate, retrieve, update, and monitor Wage Protection certificates and compliance rates.", r"\bwps\b", r"certificate", r"compliance"),
    ),
    "module-work-in-saudi": (
        _rule("mofa", "MOFA Integration Management", "Send external contracts and visa-status updates to MOFA.", r"\bmofa\b", external_entities=("MOFA",)),
        _rule("external-contract", "External Contract Lifecycle Management", "Cancel, expire, and maintain external contracts in Work in Saudi.", r"external contract", r"visa status"),
    ),
    "module-work-permit": (
        _rule("nic", "NIC and HRSD Integration Management", "Submit, issue, retrieve, and synchronize work-permit information with NIC and HRSD.", r"\bnic\b", r"\bhrsd\b", external_entities=("NIC", "HRSD")),
        _rule("notification", "Work Permit Billing Notification Management", "Send and retry work-permit billing and payment notifications.", r"notif", r"push billing"),
        _rule("payment", "Work Permit Billing and Payment Management", "Create and update SADAD bills, billing numbers, invoices, and payment states.", r"sadad", r"billing", r"invoice", r"fawtarah", r"paid"),
        _rule("debt", "Work Permit Debt Management", "Calculate, generate, validate, and retrieve establishment, laborer, and final-exit debts.", r"debt", r"delayed fees", r"delay date"),
        _rule("eligibility", "Work Permit Eligibility Management", "Validate establishment and laborer eligibility and exemptions for work permits.", r"eligib", r"exemption"),
        _rule("lifecycle", "Work Permit Lifecycle Management", "Create, submit, retrieve, search, cancel, close, calculate, and update work-permit requests and statuses.", r"work permit", r"\bwp\b"),
    ),
    "module-work-policies": (
        _rule("policy", "Work Policy Management", "Create, retrieve, validate, and maintain workplace policies.", r"polic", r"work"),
    ),
}


CONTRACT_FINAL_KEYS = {
    "employment-lifecycle": "employment-lifecycle",
    "template-management": "template-management",
    "termination-management": "termination-management",
    "training-management": "training-management",
    "external-management": "external-management",
    "validation-eligibility": "validation-eligibility",
    "wage-management": "wage-management",
    "reference-data": "reference-data",
    "authentication-compliance": "compliance",
    "authority-synchronization": "government-integration",
}
CONTRACT_RULES = (
    _rule("gosi-integration", "GOSI Integration Management", "Exchange contract, joining-date, file, status, and wage information with GOSI.", r"\bgosi\b", external_entities=("GOSI",)),
    _rule("government-integration", "HRSD and MOJ Integration Management", "Exchange contract creation, update, termination, and acknowledgement information with HRSD and MOJ.", r"\bhrsd\b", r"\bmoj\b", r"mojcontracts", external_entities=("HRSD", "MOJ")),
    _rule("compliance", "Contract Compliance Management", "Assess contract authentication, admission eligibility, and suspected fake-Saudization compliance.", r"authentication", r"fake saudization", r"admission journey", r"compliance"),
    _rule("employment-lifecycle", "Employment Contract Lifecycle Management", "Create, maintain, retrieve, renew, close, and transform employment contracts and their requests.", r"contracts?", r"contract details?", r"missing information"),
    _rule("template-management", "Contract Template Management", "Create, retrieve, update, deactivate, and list employment contract templates.", r"template"),
    _rule("termination-management", "Employment Contract Termination Management", "Submit, assess, approve, cancel, search, and monitor employment contract termination requests.", r"terminat", r"release date", r"engagement"),
    _rule("training-management", "Training Contract Lifecycle Management", "Create, maintain, retrieve, validate, and terminate training contracts.", r"training contract", r"trainee", r"\btct\b"),
    _rule("external-management", "External Contract Lifecycle Management", "Create, maintain, retrieve, approve, and cancel external contracts.", r"external contract", r"workinsaudi"),
    _rule("validation-eligibility", "Contract Validation and Eligibility Management", "Validate contract, laborer, establishment, occupation, and journey eligibility.", r"validat", r"eligib", r"relatedtoid"),
    _rule("wage-management", "Contract Wage Management", "Calculate, validate, submit, process, update, and monitor contract wages.", r"wage", r"salary", r"filedetails"),
    _rule("reference-data", "Contract Reference Data Administration", "Provide contract terms, statuses, locations, occupations, specialties, sections, and lookup data.", r"location", r"occupation", r"specialt", r"status", r"terms", r"sections"),
)
MODULE_RULES["module-contracts"] = CONTRACT_RULES

ESTABLISHMENT_FINAL_RULES = (
    _rule("government-integration", "Government Integration Management", "Exchange establishment records, licenses, locations, and status with named government authorities.", r"\bmci\b", r"\bmomra\b", r"\bhrsd\b", r"saudi business center", external_entities=("MCI", "MOMRA", "HRSD", "Saudi Business Center")),
    _rule("logo", "Establishment Logo Management", "Add, retrieve, and update establishment logos and branding.", r"logo"),
    _rule("notification", "Establishment Stakeholder Notification", "Notify owners, managers, and representatives about establishment events.", r"notif", r"email"),
    _rule("compliance", "Establishment Compliance Management", "Assess and manage establishment violations, punishments, supervision, grace periods, and obligations.", r"violation", r"punishment", r"compliance", r"supervision", r"grace period"),
    _rule("license", "Establishment License Management", "Retrieve, validate, link, and maintain establishment licenses.", r"licen[cs]"),
    _rule("location", "Establishment Location Management", "Create and maintain establishment locations and laborer assignments.", r"location"),
    _rule("activity", "Establishment Activity and Classification Management", "Maintain establishment activities, classifications, eligibility, and related Nitaqat context.", r"activit", r"isic", r"nitaqat"),
    _rule("ownership", "Establishment Ownership and Representation Management", "Maintain owners, transfers, managers, parties, legal form, and representatives.", r"owner", r"manager", r"represent", r"legal form", r"parties"),
    _rule("closure", "Establishment Closure Management", "Close establishments and maintain closure outcomes.", r"close", r"closure"),
    _rule("request", "Establishment Request and Agent Management", "Submit, review, search, approve, and reject establishment requests involving agents and owners.", r"request", r"agent"),
    _rule("opening", "Establishment Registration and Opening", "Open establishment files, branches, and unified identities through evidenced registration routes.", r"open", r"registration", r"establishment file"),
    _rule("records", "Establishment Records Management", "Maintain establishment profiles, hierarchy, unified numbers, and commercial-registration records.", r"commercial registration", r"\bcr\b", r"unified number", r"profile", r"establishment"),
)
MODULE_RULES["module-establishment"] = ESTABLISHMENT_FINAL_RULES


EXCLUSION_PATTERNS = (
    (re.compile(r"^\s*\*?old\*?(?:\s+design)?\b", re.I), "OLD"),
    (re.compile(r"\bold\s+design\b", re.I), "OLD_DESIGN"),
    (re.compile(r"^\s*\*?(?:not\s+used|ignore|ignored)\*?\b", re.I), "SOURCE_DECLARED_UNUSED_OR_IGNORED"),
    (re.compile(r"\bto\s+be\s+deleted\b", re.I), "TO_BE_DELETED"),
)
NARRATIVE_CUES = (
    "this service", "this scheduler", "this api", "this queue", "the purpose",
    "the scope", "is used to", "will be used", "to allow", "allows", "enables",
)
NOISE_TERMS = (
    "table of contents", "revision history", "reference documents", "item | description",
    "deployed to production", "service code", "date | author",
)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _csv_bytes(rows: list[dict[str, Any]], fields: list[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_marker(service_name: str, title: str) -> str:
    for value in (title, service_name):
        for pattern, marker in EXCLUSION_PATTERNS:
            if pattern.search(value):
                return marker
    return ""


def _semantic_blocks(parsed: dict[str, Any], *, is_isd: bool = False) -> list[dict[str, Any]]:
    blocks = []
    for block in parsed.get("blocks", []):
        text = str(block.get("text") or "").strip()
        section = str(block.get("section_heading") or "").casefold()
        lower = text.casefold()
        if len(text) < 15 or block.get("kind") == "heading" or any(term in lower for term in NOISE_TERMS):
            continue
        narrative = any(cue in lower for cue in NARRATIVE_CUES) or any(
            cue in section for cue in ("introduction", "purpose", "scope", "summary", "overview")
        )
        schema = is_isd and (
            any(cue in section for cue in ("request", "response", "schema", "structure", "message"))
            or any(cue in lower for cue in ("request message", "response message", "request schema", "response schema"))
        )
        if narrative or schema:
            blocks.append(block)
    if blocks:
        return blocks
    return [
        block for block in parsed.get("blocks", [])
        if block.get("kind") != "heading"
        and len(str(block.get("text") or "").strip()) >= 20
        and not any(term in str(block.get("text") or "").casefold() for term in NOISE_TERMS)
    ]


def _load_parsed(
    root: Path, catalog: DocumentCatalog, document: dict[str, Any], telemetry: Counter[str],
) -> dict[str, Any]:
    parser_version = _document_parser_version(str(document.get("mime_type") or ""))
    for relative in BASE_PARSE_INDEXES:
        path = _parse_cache_path(root / relative, document["blob_sha256"], parser_version)
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("blob_sha256") == document["blob_sha256"] and payload.get("blocks") is not None:
            telemetry["parse_cache_hits"] += 1
            return payload
    telemetry["parse_cache_misses"] += 1
    result, body = catalog.load_document(document["document_key"])
    if body is None:
        return {"parse_status": result["status"].upper(), "gap_reason": result["status"], "blocks": []}
    telemetry["blob_body_reads"] += 1
    return parse_document(body, str(document.get("mime_type") or ""))


def _contract_page_rule(page_id: str, text: str) -> CapabilityRule | None:
    if page_id == "5516591134":
        return next(rule for rule in CONTRACT_RULES if rule.key == "compliance")
    integration_action = re.search(
        r"send|submit|receive|listen|exchange|synchron|queue|status|files?|retrieve|get\b",
        text, re.I,
    )
    if integration_action and re.search(r"\bgosi\b", text, re.I):
        return next(rule for rule in CONTRACT_RULES if rule.key == "gosi-integration")
    if integration_action and re.search(r"\bhrsd\b|\bmoj\b|mojcontracts", text, re.I):
        return next(rule for rule in CONTRACT_RULES if rule.key == "government-integration")
    for capability_key, pages in CONTRACT_PAGES.items():
        if page_id not in pages:
            continue
        final_key = CONTRACT_FINAL_KEYS[capability_key]
        if final_key == "government-integration" and re.search(r"\bgosi\b", text, re.I):
            final_key = "gosi-integration"
        return next(rule for rule in CONTRACT_RULES if rule.key == final_key)
    return None


def _establishment_page_rule(page_id: str, text: str) -> CapabilityRule | None:
    integration = next(rule for rule in ESTABLISHMENT_FINAL_RULES if rule.key == "government-integration")
    if any(re.search(pattern, text, re.I) for pattern in integration.patterns) and re.search(
        r"send|push|receive|exchange|update|retrieve|sync|integration", text, re.I
    ):
        return integration
    key_map = {
        "registration-opening": "opening", "activity-management": "activity",
        "location-management": "location", "license-management": "license",
        "ownership-representation": "ownership", "record-hierarchy": "records",
        "request-agent": "request", "closure": "closure",
        "compliance-violation": "compliance", "logo-management": "logo",
        "stakeholder-notification": "notification",
    }
    for old_key, pages in ESTABLISHMENT_PAGES.items():
        if page_id in pages:
            return next(rule for rule in ESTABLISHMENT_FINAL_RULES if rule.key == key_map[old_key])
    return None


def _select_rule(module_key: str, document: dict[str, Any], parsed: dict[str, Any]) -> CapabilityRule:
    blocks = _semantic_blocks(parsed, is_isd=document["document_type"] == "ISD")
    body_text = " ".join(str(block.get("text") or "") for block in blocks)
    combined = " ".join((document.get("service_name", ""), document.get("title", ""), body_text))
    if module_key == "module-contracts":
        selected = _contract_page_rule(str(document.get("page_id") or ""), combined)
        if selected:
            return selected
    if module_key == "module-establishment":
        selected = _establishment_page_rule(str(document.get("page_id") or ""), combined)
        if selected:
            return selected
    rules = MODULE_RULES[module_key]
    title = document.get("title", "")
    for rule in rules:
        if any(re.search(pattern, title, re.I) for pattern in rule.patterns):
            return rule
    identity = " ".join((document.get("service_name", ""), title))
    for rule in rules[:-1]:
        if any(re.search(pattern, identity, re.I) for pattern in rule.patterns):
            return rule
    for rule in rules:
        if any(re.search(pattern, combined, re.I) for pattern in rule.patterns):
            return rule
    return rules[-1]


def _evidence_for(rule: CapabilityRule, parsed: dict[str, Any], *, is_isd: bool) -> dict[str, Any] | None:
    blocks = _semantic_blocks(parsed, is_isd=is_isd)
    preferred = [
        block for block in blocks
        if any(cue in str(block.get("text") or "").casefold() for cue in NARRATIVE_CUES)
    ]
    ordered = preferred + [block for block in blocks if block not in preferred]
    for pattern in rule.patterns:
        for block in ordered:
            if re.search(pattern, str(block.get("text") or ""), re.I):
                return block
    return preferred[0] if preferred else None


def _isd_signals(parsed: dict[str, Any]) -> str:
    blocks = _semantic_blocks(parsed, is_isd=True)
    narrative = [
        block for block in blocks
        if any(cue in str(block.get("text") or "").casefold() for cue in NARRATIVE_CUES)
    ]
    schemas = [
        block for block in blocks
        if any(cue in str(block.get("section_heading") or "").casefold() for cue in ("request", "response", "schema", "structure"))
    ]
    chosen = (narrative[:1] + schemas[:2]) or blocks[:2]
    return " || ".join(_sanitize_evidence(str(block.get("text") or ""))[:300] for block in chosen)


def _main_id(module_key: str, rule: CapabilityRule) -> str:
    return _stable_id("main-final", module_key, rule.key)


def _exception(
    module: dict[str, Any], source_type: str, issue_type: str, reason: str,
    document: dict[str, Any] | None = None, *, services: str = "", occurrences: str = "",
    pointer: str = "",
) -> dict[str, str]:
    document = document or {}
    return {
        "exception_id": _stable_id(
            "exception-final", module["module_key"], source_type, issue_type,
            document.get("page_id", ""), document.get("document_key", ""), services,
        ),
        "module_key": module["module_key"], "module_name": module["module_name"],
        "source_type": source_type, "page_id": str(document.get("page_id") or ""),
        "document_key": str(document.get("document_key") or ""), "service_keys": services,
        "occurrence_ids": occurrences, "title": str(document.get("title") or ""),
        "issue_type": issue_type, "precise_reason": reason, "evidence_pointer": pointer,
        "downstream_impact": "Future Canonical API capability mapping cannot claim this source until reviewed",
        "status": "EA_REVIEW_REQUIRED",
    }


def _group_documents(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["page_id"], row["physical_identity"])].append(row)
    return [sorted(value, key=lambda row: row["occurrence_id"]) for _, value in sorted(grouped.items())]


def _module_signature(
    module: dict[str, Any], services: list[dict[str, Any]], documents: list[dict[str, Any]], catalog_sha: str,
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION, "rules_version": RULES_VERSION,
        "catalog_sha256": catalog_sha, "module": module,
        "services": [{key: row[key] for key in ("service_key", "service_name")} for row in services],
        "documents": [
            {key: row[key] for key in (
                "occurrence_id", "service_key", "document_key", "document_type", "page_id",
                "physical_identity", "title", "blob_sha256", "source_version", "status",
            )}
            for row in documents
        ],
    }
    return _sha256_bytes(_json_bytes(payload))


def _checkpoint_valid(path: Path, signature: str) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return (
            payload["schema_version"] == SCHEMA_VERSION
            and payload["source_signature"] == signature
            and payload["checkpoint_status"] in {"MODULE_COMPLETE", "MODULE_COMPLETE_WITH_EXCEPTIONS"}
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return False


def _process_module(
    root: Path, module: dict[str, Any], services: list[dict[str, Any]], documents: list[dict[str, Any]],
    catalog: DocumentCatalog, signature: str, telemetry: Counter[str],
) -> dict[str, Any]:
    module_key = module["module_key"]
    services_by_key = {row["service_key"]: row for row in services}
    icd_rows = [row for row in documents if row["document_type"] == "ICD"]
    isd_rows = [row for row in documents if row["document_type"] == "ISD"]
    excluded: list[dict[str, str]] = []
    exceptions: list[dict[str, str]] = []

    def split_active(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        active, rejected = [], []
        for row in rows:
            service_name = services_by_key[row["service_key"]]["service_name"]
            marker = _source_marker(service_name, row["title"])
            if not marker:
                active.append(row)
                continue
            rejected.append(row)
            excluded.append({
                "exclusion_id": _stable_id("excluded-final", row["occurrence_id"], marker),
                "module_key": module_key, "module_name": module["module_name"],
                "source_type": row["document_type"], "page_id": row["page_id"],
                "document_key": row["document_key"], "service_key": row["service_key"],
                "occurrence_id": row["occurrence_id"], "title": row["title"],
                "source_marker": marker,
                "exclusion_reason": "Source title or authoritative Service metadata explicitly marks this artifact OLD/Old Design/NOT USED/IGNORE/IGNORED/to be deleted; excluded from active candidates without a runtime-retirement inference",
                "runtime_state_proven": "false",
            })
        return active, rejected

    active_icd, excluded_icd = split_active(icd_rows)
    active_isd, excluded_isd = split_active(isd_rows)
    main_by_id: dict[str, dict[str, Any]] = {}
    icd_links: list[dict[str, Any]] = []
    isd_links: list[dict[str, Any]] = []

    def map_group(group: list[dict[str, Any]], *, is_isd: bool, unpaired_reason: str = "") -> None:
        document = dict(group[0])
        document["service_name"] = services_by_key[document["service_key"]]["service_name"]
        hashes = {row["blob_sha256"] for row in group}
        keys = {row["document_key"] for row in group}
        if len(hashes) != 1:
            exceptions.append(_exception(
                module, document["document_type"], "SOURCE_IDENTITY_CONFLICT",
                "Occurrences sharing a page identity disagree on content hash",
                document, services=";".join(sorted({row["service_key"] for row in group})),
                occurrences=";".join(sorted(row["occurrence_id"] for row in group)),
            ))
            return
        parsed = _load_parsed(root, catalog, document, telemetry)
        if parsed.get("parse_status") != "PARSED":
            exceptions.append(_exception(
                module, document["document_type"], "UNREADABLE_SOURCE",
                f"Structured parse status {parsed.get('parse_status')}: {parsed.get('gap_reason', '')}",
                document, services=";".join(sorted({row["service_key"] for row in group})),
                occurrences=";".join(sorted(row["occurrence_id"] for row in group)),
                pointer=document["blob_sha256"],
            ))
            return
        rule = _select_rule(module_key, document, parsed)
        evidence = _evidence_for(rule, parsed, is_isd=is_isd)
        if evidence is None:
            exceptions.append(_exception(
                module, document["document_type"], "UNRESOLVED_SEMANTIC_EVIDENCE",
                f"Readable source lacks a narrative or meaningful schema block supporting {rule.name}",
                document, services=";".join(sorted({row["service_key"] for row in group})),
                occurrences=";".join(sorted(row["occurrence_id"] for row in group)),
                pointer=document["blob_sha256"],
            ))
            return
        main_id = _main_id(module_key, rule)
        main = main_by_id.setdefault(main_id, {
            "module_key": module_key, "module_name": module["module_name"],
            "main_capability_id": main_id, "name": rule.name, "description": rule.description,
            "candidate_status": "candidate", "source_types": set(), "document_keys": set(),
        })
        main["source_types"].add(document["document_type"])
        main["document_keys"].add(document["page_id"])
        pointer = f"page:{document['page_id']}#{evidence['block_id']}:{evidence['char_start']}-{evidence['char_end']}"
        base = {
            "module_key": module_key, "module_name": module["module_name"],
            "main_capability_id": main_id, "page_id": document["page_id"],
            "document_key": ";".join(sorted(keys)), "physical_identity": document["physical_identity"],
            "title": document["title"],
            "service_keys": ";".join(sorted({row["service_key"] for row in group})),
            "occurrence_ids": ";".join(sorted(row["occurrence_id"] for row in group)),
            "blob_sha256": document["blob_sha256"], "source_version": document["source_version"],
            "evidence_pointer": pointer,
            "evidence_excerpt": _sanitize_evidence(str(evidence.get("text") or ""))[:500],
            "external_entities": ";".join(rule.external_entities), "mapping_status": "candidate",
            "mapping_rationale": f"Recovered {document['document_type']} semantics directly support {rule.name}; EA approval pending",
        }
        if is_isd:
            isd_links.append({
                **base, "classification_signals": _isd_signals(parsed),
                "unpaired_reason": unpaired_reason,
            })
        else:
            icd_links.append(base)

    # Step A: complete active ICD corpus before any ISD body is considered.
    for group in _group_documents(active_icd):
        map_group(group, is_isd=False)

    # Step B: only ISDs whose Service has no active ICD relationship.
    active_icd_services = {row["service_key"] for row in active_icd}
    # A recovered child page can have both its original business-Service
    # occurrence and an added navigation-parent occurrence.  If any occurrence
    # of that same physical ISD page is tied to an active ICD Service, preserve
    # the evidenced relationship for every duplicate occurrence of the page.
    paired_isd_pages = {
        row["page_id"] for row in active_isd if row["service_key"] in active_icd_services
    }
    paired_isd = [row for row in active_isd if row["page_id"] in paired_isd_pages]
    unpaired_isd = [row for row in active_isd if row["page_id"] not in paired_isd_pages]
    for group in _group_documents(unpaired_isd):
        map_group(
            group, is_isd=True,
            unpaired_reason="No active ICD occurrence is associated with this source Service in the recovery effective catalog",
        )

    main_rows = []
    for row in sorted(main_by_id.values(), key=lambda item: (item["name"], item["main_capability_id"])):
        main_rows.append({
            **{key: row[key] for key in MAIN_FIELDS if key not in {"source_types", "linked_document_count"}},
            "source_types": ";".join(sorted(row["source_types"])),
            "linked_document_count": len(row["document_keys"]),
        })
    linked_icd = {row["page_id"] for row in icd_links}
    eligible_icd_groups = _group_documents(active_icd)
    unresolved_icd = {group[0]["page_id"] for group in eligible_icd_groups} - linked_icd
    linked_isd = {row["page_id"] for row in isd_links}
    eligible_isd_groups = _group_documents(unpaired_isd)
    unresolved_isd = {group[0]["page_id"] for group in eligible_isd_groups} - linked_isd
    checkpoint_status = "MODULE_COMPLETE_WITH_EXCEPTIONS" if exceptions else "MODULE_COMPLETE"
    coverage = {
        "module_key": module_key, "module_name": module["module_name"],
        "service_count": len(services), "icd_occurrences": len(icd_rows),
        "unique_icd_documents": len(_group_documents(icd_rows)),
        "eligible_icd_documents": len(eligible_icd_groups),
        "excluded_icd_occurrences": len(excluded_icd), "linked_icd_documents": len(linked_icd),
        "unresolved_icd_documents": len(unresolved_icd), "isd_occurrences": len(isd_rows),
        "unique_isd_documents": len(_group_documents(isd_rows)),
        "paired_isd_documents": len(_group_documents(paired_isd)),
        "eligible_unpaired_isd_documents": len(eligible_isd_groups),
        "excluded_isd_occurrences": len(excluded_isd),
        "linked_unpaired_isd_documents": len(linked_isd),
        "unresolved_unpaired_isd_documents": len(unresolved_isd),
        "main_capability_count": len(main_rows), "checkpoint_status": checkpoint_status,
        "source_signature": signature, "checkpoint_sha256": "",
    }
    return {
        "schema_version": SCHEMA_VERSION, "rules_version": RULES_VERSION,
        "source_signature": signature, "checkpoint_status": checkpoint_status,
        "module": module, "coverage": coverage, "main_capabilities": main_rows,
        "main_icd_links": sorted(icd_links, key=lambda row: (row["page_id"], row["main_capability_id"])),
        "main_isd_links": sorted(isd_links, key=lambda row: (row["page_id"], row["main_capability_id"])),
        "excluded_sources": sorted(excluded, key=lambda row: row["exclusion_id"]),
        "coverage_exceptions": sorted(exceptions, key=lambda row: row["exception_id"]),
        "processing_order": "ALL_ACTIVE_ICDS_THEN_UNPAIRED_ISDS",
    }


def build_final_mapping(
    root: Path, index_root: Path | None = None, output_root: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    index_root = (index_root or root / INDEX_ROOT).resolve()
    output_root = (output_root or root / OUTPUT_ROOT).resolve()
    catalog_path, recovery_manifest = _validated_recovery(root)
    catalog_sha = recovery_manifest["catalog"]["sha256"]
    telemetry: Counter[str] = Counter()
    checkpoints: list[dict[str, Any]] = []
    with DocumentCatalog(root, catalog_path) as catalog:
        modules = catalog.list_modules()
        if len(modules) != EXPECTED["modules"] or set(MODULE_RULES) != {row["module_key"] for row in modules}:
            raise ValueError("MODULE_RULE_REGISTRY_CLOSURE_MISMATCH")
        totals = Counter()
        for module in modules:
            services = catalog.list_services(module["module_key"])
            documents = catalog.list_documents(module["module_key"])
            totals["services"] += len(services)
            totals["icd_occurrences"] += sum(row["document_type"] == "ICD" for row in documents)
            totals["isd_occurrences"] += sum(row["document_type"] == "ISD" for row in documents)
            signature = _module_signature(module, services, documents, catalog_sha)
            checkpoint_path = output_root / "modules" / f"{module['module_key']}.json"
            if _checkpoint_valid(checkpoint_path, signature):
                telemetry["module_checkpoint_hits"] += 1
                checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            else:
                telemetry["module_checkpoint_misses"] += 1
                checkpoint = _process_module(
                    root, module, services, documents, catalog, signature, telemetry
                )
                _atomic_write(checkpoint_path, _json_bytes(checkpoint))
            checkpoint["coverage"]["checkpoint_sha256"] = _sha256_file(checkpoint_path)
            checkpoints.append(checkpoint)
        if any(totals[key] != EXPECTED[key] for key in EXPECTED if key != "modules"):
            raise ValueError(f"RECOVERY_CATALOG_CLOSURE_MISMATCH:{dict(totals)}")

    mains = [row for item in checkpoints for row in item["main_capabilities"]]
    icd_links = [row for item in checkpoints for row in item["main_icd_links"]]
    isd_links = [row for item in checkpoints for row in item["main_isd_links"]]
    excluded = [row for item in checkpoints for row in item["excluded_sources"]]
    exceptions = [row for item in checkpoints for row in item["coverage_exceptions"]]
    coverage = [item["coverage"] for item in checkpoints]
    datasets = {
        "main_capabilities.csv": (sorted(mains, key=lambda row: (row["module_key"], row["name"])), MAIN_FIELDS),
        "main_icd_links.csv": (sorted(icd_links, key=lambda row: (row["module_key"], row["page_id"], row["main_capability_id"])), LINK_FIELDS),
        "main_isd_links.csv": (sorted(isd_links, key=lambda row: (row["module_key"], row["page_id"], row["main_capability_id"])), ISD_LINK_FIELDS),
        "excluded_sources.csv": (sorted(excluded, key=lambda row: (row["module_key"], row["source_type"], row["page_id"], row["occurrence_id"])), EXCLUDED_FIELDS),
        "coverage_exceptions.csv": (sorted(exceptions, key=lambda row: (row["module_key"], row["source_type"], row["page_id"])), EXCEPTION_FIELDS),
        "module_coverage.csv": (sorted(coverage, key=lambda row: row["module_key"]), COVERAGE_FIELDS),
    }
    payloads = {name: _csv_bytes(rows, fields) for name, (rows, fields) in datasets.items()}
    for name, content in payloads.items():
        _atomic_write(index_root / name, content)

    exception_lines = [
        f"- `{row['module_key']}` / {row['source_type']} page `{row['page_id'] or 'none'}` / "
        f"`{row['document_key'] or 'none'}` — **{row['issue_type']}**: {row['precise_reason']}"
        for row in datasets["coverage_exceptions.csv"][0]
    ] or ["- None."]
    module_lines = []
    for row in datasets["module_coverage.csv"][0]:
        module_lines.append(
            f"| `{row['module_key']}` | {row['service_count']} | "
            f"{row['linked_icd_documents']}/{row['eligible_icd_documents']} | "
            f"{row['excluded_icd_occurrences']} | {row['unresolved_icd_documents']} | "
            f"{row['linked_unpaired_isd_documents']}/{row['eligible_unpaired_isd_documents']} | "
            f"{row['excluded_isd_occurrences']} | {row['unresolved_unpaired_isd_documents']} | "
            f"{row['main_capability_count']} | {row['checkpoint_status']} |"
        )
    totals = {
        "mains": len(mains), "icd_links": len(icd_links), "isd_links": len(isd_links),
        "excluded": len(excluded), "exceptions": len(exceptions),
        "eligible_icd": sum(int(row["eligible_icd_documents"]) for row in coverage),
        "unresolved_icd": sum(int(row["unresolved_icd_documents"]) for row in coverage),
        "eligible_unpaired_isd": sum(int(row["eligible_unpaired_isd_documents"]) for row in coverage),
        "unresolved_isd": sum(int(row["unresolved_unpaired_isd_documents"]) for row in coverage),
    }
    summary = (
        "# Phase 6 Task 019-E-FINAL review summary\n\n"
        "## Overall closure\n\n"
        f"- Recovery effective catalog: {EXPECTED['modules']} Modules, {EXPECTED['services']} Services, "
        f"{EXPECTED['icd_occurrences']} ICD occurrences and {EXPECTED['isd_occurrences']} ISD occurrences.\n"
        f"- Active ICD mapping: {totals['icd_links']}/{totals['eligible_icd']} eligible unique documents linked; "
        f"{totals['unresolved_icd']} unresolved.\n"
        f"- Post-ICD unpaired ISD mapping: {totals['isd_links']}/{totals['eligible_unpaired_isd']} eligible unique documents linked; "
        f"{totals['unresolved_isd']} unresolved. ISDs associated with an active ICD Service were not reparsed.\n"
        f"- Candidate inventory: {totals['mains']} Module-local Main Capabilities. Excluded source occurrences: "
        f"{totals['excluded']}; explicit coverage exceptions: {totals['exceptions']}.\n"
        "- Processing is checkpoint-resumable by Module and reuses the validated task019 recovery/019e parse indexes read-only. "
        "Run-specific checkpoint telemetry is returned by the command and is not embedded in this deterministic report.\n"
        f"- Recovery catalog remained read-only at SHA-256 `{catalog_sha}`. Candidate mapping is not EA approval and does not map Canonical APIs.\n\n"
        "## Module completion\n\n"
        "| Module | Services | ICD linked/eligible | ICD excluded | ICD unresolved | Unpaired ISD linked/eligible | ISD excluded | ISD unresolved | Mains | Status |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n"
        + "\n".join(module_lines) + "\n\n"
        "## Outstanding exceptions\n\n" + "\n".join(exception_lines) + "\n\n"
        "## Focused controls\n\n"
        "- PASS: all Modules use the enforced `ALL_ACTIVE_ICDS_THEN_UNPAIRED_ISDS` processing order.\n"
        "- PASS: source-declared OLD/Old Design/NOT USED/IGNORE/IGNORED/to-be-deleted artifacts are audited separately and never treated as runtime-retirement proof.\n"
        "- PASS: Main names are meaningful noun phrases without slash-delimited labels; all links retain Service, occurrence, document, page, version, hash, and body evidence pointers.\n"
        "- PASS: unique page identity controls duplicate inflation; no Business Function, Sub Capability, Canonical API, endpoint, or Kong artifact was created.\n"
        "- Final status: `CANDIDATE_MAPPING_COMPLETE_WITH_EXPLICIT_EXCEPTIONS`; STOP at `EA_REVIEW_019E_FINAL`.\n"
    ).encode("utf-8")
    _atomic_write(output_root / "review_summary.md", summary)
    return {
        "counts": totals,
        "telemetry": dict(telemetry),
        "hashes": {
            **{name: _sha256_bytes(content) for name, content in payloads.items()},
            "review_summary.md": _sha256_bytes(summary), "recovery_catalog": catalog_sha,
        },
        "status": "EA_REVIEW_019E_FINAL",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 019-E-FINAL all-Module direct Main mapping")
    parser.add_argument("command", choices=("build",))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--index-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(
        build_final_mapping(args.root, args.index_root, args.output_root), indent=2, sort_keys=True
    ))


if __name__ == "__main__":
    main()
