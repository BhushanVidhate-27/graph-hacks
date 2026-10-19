export type ViewMode = 'website' | 'chat-widget' | 'dashboard' | 'viewport';

export interface DependencyNode {
  id: string;
  name: string;
  category: 'critical-path' | 'unowned' | 'provenance' | 'stale-edge';
  tier: string;
  owningTeam: string;
  onCall: string;
  blastRadius: string[];
  hopDepth: number;
  status: 'healthy' | 'stale' | 'orphan' | 'superseded';
  cypherQuery: string;
  summary: string;
  groundTruthFact: string;
  x: number; // percentage on visual canvas
  y: number; // percentage on visual canvas
}

export interface PricingPlan {
  id: string;
  name: string;
  tagline: string;
  priceMonthly: number;
  priceYearly: number;
  credits: string;
  features: string[];
  cta: string;
  highlighted?: boolean;
}

export interface FAQItem {
  id: string;
  question: string;
  answer: string;
}
