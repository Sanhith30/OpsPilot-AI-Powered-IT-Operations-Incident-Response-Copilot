/**
 * OpsPilot Application Constants & RBAC Persona Definitions
 */

export const DEMO_PERSONAS = [
  {
    userId: 1,
    name: 'Arun Kumar',
    email: 'arun@opspilot.local',
    role: 'L1_ENGINEER',
    roleName: 'L1 Support Engineer',
    badge: 'L1',
    description: 'Read-only operational triage; cannot request or approve remediations.',
  },
  {
    userId: 2,
    name: 'Priya Sharma',
    email: 'priya@opspilot.local',
    role: 'L2_ENGINEER',
    roleName: 'L2 SRE Engineer',
    badge: 'L2',
    description: 'Can request remediations & run verifications; cannot approve executions.',
  },
  {
    userId: 3,
    name: 'Rahul Verma',
    email: 'rahul@opspilot.local',
    role: 'MANAGER',
    roleName: 'Incident Commander',
    badge: 'Manager',
    description: 'Full approval & execution authority for operational remediations.',
  },
  {
    userId: 4,
    name: 'Meena Rao',
    email: 'meena@opspilot.local',
    role: 'ADMIN',
    roleName: 'System Administrator',
    badge: 'Admin',
    description: 'Complete administrative, RBAC, and operational privileges.',
  },
];

export const INCIDENT_STATUSES = {
  OPEN: { label: 'Open', color: 'critical' },
  INVESTIGATING: { label: 'Investigating', color: 'warning' },
  MITIGATED: { label: 'Mitigated', color: 'healthy' },
  RESOLVED: { label: 'Resolved', color: 'healthy' },
  CLOSED: { label: 'Closed', color: 'info' },
};

export const INCIDENT_SEVERITIES = {
  CRITICAL: { label: 'P1 - Critical', color: 'critical' },
  HIGH: { label: 'P2 - High', color: 'warning' },
  MEDIUM: { label: 'P3 - Medium', color: 'info' },
  LOW: { label: 'P4 - Low', color: 'info' },
};

export const REMEDIATION_STATUSES = {
  PENDING_APPROVAL: { label: 'Pending Approval', color: 'warning', icon: '⏳' },
  APPROVED: { label: 'Approved', color: 'cyan', icon: '✅' },
  REJECTED: { label: 'Rejected', color: 'critical', icon: '❌' },
  REQUEST_MORE_INFO: { label: 'More Info Needed', color: 'warning', icon: '❓' },
  EXECUTING: { label: 'Executing', color: 'purple', icon: '⚡' },
  COMPLETED: { label: 'Completed', color: 'info', icon: '⚙️' },
  FAILED: { label: 'Failed', color: 'critical', icon: '💥' },
  VERIFIED: { label: 'Verified Safe', color: 'healthy', icon: '🛡️' },
  VERIFICATION_FAILED: { label: 'Verification Failed', color: 'critical', icon: '⚠️' },
};
