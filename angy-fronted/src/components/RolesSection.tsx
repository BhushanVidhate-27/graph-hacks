import React from 'react';
import { CadCrosshair } from './CadCrosshair';

export const RolesSection: React.FC = () => {
  const roles = [
    {
      title: 'INCIDENT COMMANDERS',
      desc: 'Trace blast radius and find the active on-call engineer in 3 seconds flat during outages.',
      num: '[01]'
    },
    {
      title: 'STAFF ARCHITECTS',
      desc: 'Follow SUPERSEDES chains to ensure deprecated architectural decisions are retired.',
      num: '[02]'
    },
    {
      title: 'ENGINEERING DIRECTORS',
      desc: 'Audit unowned services (like config-service) and eliminate structural blindspots.',
      num: '[03]'
    },
    {
      title: 'SITE RELIABILITY ENGINEERS',
      desc: 'Map multi-hop cascade dependencies before releasing core infrastructure changes.',
      num: '[04]'
    },
    {
      title: 'NEW HIRES & DEVELOPERS',
      desc: 'Discover who actually maintains a codebase recently, bypassing stale Confluence wikis.',
      num: '[05]'
    },
    {
      title: 'PLATFORM LEADS',
      desc: 'Keep service tiers and SLA contracts compliant across distributed engineering teams.',
      num: '[06]'
    },
    {
      title: 'SECURITY AUDITORS',
      desc: 'Visualize exact blast radius when a critical dependency requires emergency patching.',
      num: '[07]'
    },
    {
      title: 'PRODUCT MANAGERS',
      desc: 'Map cross-team service ownership to eliminate organizational blockers.',
      num: '[08]'
    }
  ];

  return (
    <section className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          USE CASES // BUILT FOR COMPLEX ENGINEERING ORGS
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          One source of truth for the entire engineering organization
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {roles.map((r) => (
          <div
            key={r.num}
            className="bg-[#f4f4ec] cad-border p-5 relative hover:bg-[#282828] hover:text-white transition-colors duration-200 group flex flex-col justify-between"
          >
            <CadCrosshair position="tl" />
            <CadCrosshair position="tr" />
            <CadCrosshair position="bl" />
            <CadCrosshair position="br" />

            <div>
              <div className="flex items-center justify-between font-mono text-[10px] text-[#5c5c56] group-hover:text-white/60 mb-3">
                <span className="text-[#e15c46] font-bold">STAKEHOLDER</span>
                <span>{r.num}</span>
              </div>
              <h3 className="font-mono font-bold text-base uppercase mb-2">
                {r.title}
              </h3>
            </div>

            <p className="font-mono text-xs text-[#5c5c56] group-hover:text-white/80 leading-relaxed pt-3 cad-border-t border-[#282828]/20 group-hover:border-white/20">
              {r.desc}
            </p>
          </div>
        ))}
      </div>

    </section>
  );
};
