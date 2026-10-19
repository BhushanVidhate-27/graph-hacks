import React, { useState } from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { Check, Sparkles } from 'lucide-react';
import { PricingPlan } from '../types';

export const PricingSection: React.FC = () => {
  const [isYearly, setIsYearly] = useState(false);

  const plans: PricingPlan[] = [
    {
      id: 'free',
      name: 'Free',
      tagline: "For individuals exploring Heron's chat and suggestions.",
      priceMonthly: 0,
      priceYearly: 0,
      credits: '500 credits / month',
      features: [
        'Chat widget: ask about your model',
        'Single active CAD project',
        'Basic building code queries',
        'Community support',
        'Standard latency'
      ],
      cta: 'Get Started'
    },
    {
      id: 'standard',
      name: 'Standard',
      tagline: 'For individuals and small firms ready to let Heron edit inside Revit.',
      priceMonthly: 99,
      priceYearly: 90,
      credits: '5,000 credits / month',
      highlighted: true,
      features: [
        'In-tool agent in Revit & Rhino',
        'Suggestions as you design',
        'Direct edit on approval',
        'Unlimited active projects',
        'Learns basic firm standards',
        'Email support'
      ],
      cta: 'Start Free Trial'
    },
    {
      id: 'business',
      name: 'Business',
      tagline: 'For medium firms and collaborative, multi-office teams.',
      priceMonthly: 295,
      priceYearly: 290,
      credits: '50,000 credits / month',
      features: [
        'Everything in Standard',
        'Heron Dashboard web oversight',
        'Team view & shared approvals',
        'Firm standards knowledge RAG',
        'Admin, SSO & audit logs',
        'API & model data export',
        'Email & live chat support'
      ],
      cta: 'Contact Sales'
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      tagline: 'For large firms, universities, and multi-office deployments.',
      priceMonthly: 0,
      priceYearly: 0,
      credits: 'Custom credits allocation',
      features: [
        'Custom local LLM deployment option',
        'Unlimited seats & enterprise SSO',
        'Dedicated BIM integration specialist',
        'Custom code amendments training',
        'Strict private cloud / on-premise SLA',
        '24/7 dedicated support'
      ],
      cta: 'Talk to Enterprise'
    }
  ];

  return (
    <section id="pricing-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-12">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          PRICING // PAY FOR THE HOURS YOU GET BACK
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight mb-4">
          Transparent plans for every practice
        </h2>
        <p className="text-sm font-mono text-[#5c5c56]">
          Start free, then let Heron work inside your tools. Move up, down, or cancel whenever you like.
        </p>

        {/* Billing Toggle */}
        <div className="mt-8 inline-flex items-center gap-3 bg-[#f4f4ec] cad-border p-1.5 font-mono text-xs">
          <button
            onClick={() => setIsYearly(false)}
            className={`px-4 py-2 transition-colors ${
              !isYearly ? 'bg-[#282828] text-white font-bold' : 'text-[#5c5c56] hover:text-[#282828]'
            }`}
          >
            MONTHLY
          </button>
          <button
            onClick={() => setIsYearly(true)}
            className={`px-4 py-2 transition-colors flex items-center gap-2 ${
              isYearly ? 'bg-[#e15c46] text-white font-bold' : 'text-[#5c5c56] hover:text-[#282828]'
            }`}
          >
            <span>YEARLY</span>
            <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded">SAVE 15%</span>
          </button>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
        {plans.map((p) => {
          const price = p.name === 'Enterprise' ? 'Custom' : `$${isYearly ? p.priceYearly : p.priceMonthly}`;
          return (
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
                  <span>MOST POPULAR</span>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-mono font-bold text-xl uppercase tracking-wider">
                    {p.name}
                  </h3>
                  <span className={`font-mono text-[10px] px-2 py-0.5 cad-border ${p.highlighted ? 'border-white/30 text-white/80' : 'border-[#282828]/20 text-[#5c5c56]'}`}>
                    CAD AGENT
                  </span>
                </div>

                <div className="mb-4">
                  <div className="font-mono text-3xl md:text-4xl font-bold tracking-tight">
                    {price}
                    {p.name !== 'Enterprise' && (
                      <span className={`text-xs font-normal ${p.highlighted ? 'text-white/60' : 'text-[#5c5c56]'}`}>
                        /month
                      </span>
                    )}
                  </div>
                  <div className={`font-mono text-xs mt-1 ${p.highlighted ? 'text-[#e15c46]' : 'text-[#e15c46]'}`}>
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
          );
        })}
      </div>

      {/* Credit Explanation Note */}
      <div className="mt-8 text-center font-mono text-[11px] text-[#5c5c56]">
        10 credits = 1 Q&A, 1 project upload, 1 model scan/check, or 1 permit-ready compliance report export.
      </div>

    </section>
  );
};
