import React from 'react';
import { CadCrosshair } from './CadCrosshair';

export const ProblemsSection: React.FC = () => {
  const problems = [
    {
      index: '[01]',
      label: 'VOLUME TRAP',
      title: 'Priya Sharma left in April',
      desc: "Priya has 14 commits on payments-gateway — the most. A single 'ORDER BY count DESC' returns her, technically correct on volume but wrong on recency. Helio returns both signals: Ask Ravi Menon."
    },
    {
      index: '[02]',
      label: 'CONTRADICTION',
      title: 'Stripe vs. Adyen decision conflict',
      desc: "A March doc says 'single provider, Stripe.' May Decision D-19 says 'dual provider, Adyen primary, Stripe fallback.' Without a SUPERSEDES edge, search engines present stale docs as current truth."
    },
    {
      index: '[03]',
      label: 'BLAST RADIUS',
      title: 'Cascading midnight failures',
      desc: "When a core service degrades, text search cannot trace downstream blast radius. Helio walks HAS_DEPENDENT edges to identify exact hop depth, owning teams, and on-call engineers."
    },
    {
      index: '[04]',
      label: 'HALLUCINATION',
      title: 'Invents owners when none exist',
      desc: "An LLM asked 'who owns config-service?' invents a plausible team. Helio traverses FalkorDB, detects no OWNED_BY edge, and states with confidence: 'No team owns it.' Truth, not an apology."
    }
  ];

  return (
    <section id="problems-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Section Header */}
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          THE 4 FAILURE MODES // WHY FLAT SEARCH FAILS
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Enterprise search tells you where documents live, not what is true.
        </h2>
        <p className="mt-4 text-sm md:text-base font-mono text-[#5c5c56]">
          A hallucinated ownership chain looks exactly like a correct one because both are plausible prose.
          Helio replaces probabilistic guessing with deterministic Cypher traversals over real organizational edges.
        </p>
      </div>

      {/* 4 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {problems.map((item) => (
          <div
            key={item.index}
            className="bg-[#f4f4ec] cad-border p-6 flex flex-col justify-between relative group hover:bg-[#282828] hover:text-white transition-colors duration-300"
          >
            <CadCrosshair position="tl" />
            <CadCrosshair position="tr" />
            <CadCrosshair position="bl" />
            <CadCrosshair position="br" />

            <div>
              <div className="flex items-center justify-between font-mono text-xs text-[#5c5c56] group-hover:text-white/60 mb-6">
                <span className="font-bold text-[#e15c46]">{item.label}</span>
                <span>{item.index}</span>
              </div>

              <h3 className="font-mono font-bold text-xl uppercase mb-4 leading-snug">
                {item.title}
              </h3>
            </div>

            <p className="font-mono text-xs text-[#5c5c56] group-hover:text-white/80 leading-relaxed pt-6 cad-border-t border-[#282828]/20 group-hover:border-white/20">
              {item.desc}
            </p>
          </div>
        ))}
      </div>

    </section>
  );
};
