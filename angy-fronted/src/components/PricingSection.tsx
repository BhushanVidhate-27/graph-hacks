import React from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { Check, Sparkles, Award } from 'lucide-react';
import { PricingPlan } from '../types';

export const PricingSection: React.FC = () => {
  const plans: PricingPlan[] = [
    {
      id: 'free',
      name: 'Developer',
      tagline: 'For individuals and contributors exploring graph traversals locally.',
      priceMonthly: 0,
      priceYearly: 0,
      credits: 'Up to 10 microservices',
      features: [
        'Local FalkorDB container support',
        'Basic Cypher natural language queries',
        'Ground truth fact evaluation',
        'Community Discord access',
        'Standard traversal speed'
      ],
      cta: 'Explore in Demo'
    },
    {
      id: 'standard',
      name: 'Team',
      tagline: 'For fast-growing engineering teams managing distributed services.',
      priceMonthly: 0,
      priceYearly: 0,
      credits: 'Up to 50 microservices',
      highlighted: true,
      features: [
        'Helio Cypher Natural Language Agent',
        'Automated blast radius calculation',
        'Live on-call rotation synchronization',
        'Slack & PagerDuty notification hooks',
        'Expertise volume vs. recency weighting',
        'Email & Slack support'
      ],
      cta: 'Test Team Tier'
    },
    {
      id: 'business',
      name: 'Scale',
      tagline: 'For multi-team engineering organizations needing full architectural provenance.',
      priceMonthly: 0,
      priceYearly: 0,
      credits: 'Unlimited microservices',
      features: [
        'Everything in Team',
        'Helio FalkorDB Web Console',
        'Automated 90-day staleness decay alerts',
        'SUPERSEDES architectural decision audit',
        'Audit logs & honest negative detection',
        'API & Cypher query export',
        'Priority support'
      ],
      cta: 'Test Scale Tier'
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      tagline: 'For security-sensitive fintechs and enterprises needing airgapped compliance.',
      priceMonthly: 0,
      priceYearly: 0,
      credits: 'Custom dedicated nodes',
      features: [
        'On-premise airgapped FalkorDB cluster',
        'Custom entity resolution algorithms',
        'Dedicated graph solutions architect',
        'Custom RBAC & enterprise SSO',
        'Strict 99.99% uptime SLA',
        '24/7 incident response'
      ],
      cta: 'Contact for Enterprise'
    }
  ];

  return (
    <section id="pricing-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-12">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2 flex items-center justify-center gap-1.5">
          <Award className="w-3.5 h-3.5" />
          <span>PRICING // YET TO DECIDE (HACKATHON PROJECT)</span>
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight mb-4">
          Yet to decide (Hackathon Project)
        </h2>
        <p className="text-sm font-mono text-[#5c5c56] max-w-xl mx-auto">
          Commercial pricing is yet to be finalized as this is an active Hackathon project for 
          <span className="text-[#e15c46] font-bold"> Graph Hacks Track 03: Company Brain</span>. All capabilities are currently open for evaluation.
        </p>

        {/* Hackathon Badge Pill */}
        <div className="mt-6 inline-flex items-center gap-2 bg-[#f4f4ec] cad-border px-4 py-2 font-mono text-xs text-[#282828]">
          <span className="w-2 h-2 rounded-full bg-[#e15c46] animate-pulse" />
          <span className="font-bold">STATUS:</span>
          <span className="text-[#e15c46] font-bold uppercase">YET TO DECIDE (HACKATHON PROJECT)</span>
          <span className="text-[#5c5c56]">· All Tiers Open for Demo</span>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
        {plans.map((p) => (
          <div
            key={p.id}
            className={`cad-border p-6 flex flex-col justify-between relative transition-all duration-300 ${
              p.highlighted ? 'bg-[#282828] text-white shadow-2xl scale-[1.02]' : 'bg-[#f4f4ec] text-[#282828]'
            }`}
          >
            <CadCrosshair position="tl" />
            <CadCrosshair position="tr" />
            <CadCrosshair position="bl" />
            <CadCrosshair position="br" />

            {p.highlighted && (
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-[#e15c46] text-white font-mono text-[10px] font-bold px-3 py-1 uppercase tracking-wider shadow-lg flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                <span>RECOMMENDED</span>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-mono font-bold text-xl uppercase tracking-wider">
                  {p.name}
                </h3>
                <span className={`font-mono text-[10px] px-2 py-0.5 cad-border ${p.highlighted ? 'border-white/30 text-white/80' : 'border-[#282828]/20 text-[#5c5c56]'}`}>
                  GRAPH TIER
                </span>
              </div>

              <div className="mb-4">
                <div className="font-mono text-lg md:text-xl font-bold tracking-tight text-[#e15c46] uppercase">
                  Yet to decide
                </div>
                <div className={`font-mono text-[11px] mt-0.5 ${p.highlighted ? 'text-white/60' : 'text-[#5c5c56]'}`}>
                  (Hackathon Project)
                </div>
                <div className={`font-mono text-xs mt-2 ${p.highlighted ? 'text-white/80 font-bold' : 'text-[#282828] font-bold'}`}>
                  {p.credits}
                </div>
              </div>

              <p className={`font-mono text-xs leading-relaxed mb-6 cad-border-b pb-4 ${
                p.highlighted ? 'text-white/70 border-white/20' : 'text-[#5c5c56] border-[#282828]/20'
              }`}>
                {p.tagline}
              </p>

              {/* Features List */}
              <div className="space-y-3 font-mono text-xs mb-8">
                {p.features.map((f, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <Check className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${p.highlighted ? 'text-[#e15c46]' : 'text-[#e15c46]'}`} />
                    <span className={p.highlighted ? 'text-white/90' : 'text-[#282828]'}>{f}</span>
                  </div>
                ))}
              </div>
            </div>

            <HeronButton
              variant={p.highlighted ? 'brand' : 'outline'}
              className="w-full justify-center"
            >
              {p.cta}
            </HeronButton>
          </div>
        ))}
      </div>

      {/* Credit Explanation Note */}
      <div className="mt-8 text-center font-mono text-[11px] text-[#5c5c56]">
        Pricing: Yet to decide (Hackathon Project) · FalkorDB graph engine runs locally in Docker or via managed cloud cluster.
      </div>

    </section>
  );
};
