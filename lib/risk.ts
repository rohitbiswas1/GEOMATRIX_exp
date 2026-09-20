export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low';

export function riskLevel(score: number): RiskLevel {
  if (score >= 75) return 'Critical';
  if (score >= 50) return 'High';
  if (score >= 25) return 'Medium';
  return 'Low';
}

export const stages = [
  'Notification',
  'Objection / Hearing',
  'Compensation',
  'Award',
  'Possession',
  'Rehabilitation & Resettlement',
  'Legal / Dispute',
] as const;
