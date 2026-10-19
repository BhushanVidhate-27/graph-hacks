export type ViewMode = 'website' | 'chat-widget' | 'dashboard' | 'viewport';

export interface Violation {
  id: string;
  code: string;
  title: string;
  description: string;
  category: 'egress' | 'accessibility' | 'safety' | 'clearance';
  x: number; // percentage on canvas
  y: number; // percentage on canvas
  status: 'flagged' | 'remediated' | 'ignored';
  elementId: string;
  recommendation: string;
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
