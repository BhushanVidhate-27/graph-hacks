import React from 'react';
import { CadCrosshair } from './CadCrosshair';
import { Database, GitBranch, Clock, CheckCircle2 } from 'lucide-react';

export const WorkflowSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'GRAPH INGESTION',
      subtitle: 'Structured nodes & typed edges in FalkorDB',
      desc: 'Persons, Teams, Projects, Services, Decisions, and Documents loaded with pre-indexed Cypher properties.',
      icon: Database
    },
    {
      num: '02',
      title: 'MULTI-HOP CYPHER',
      subtitle: 'Deterministic traversal instead of fuzzy search',
      desc: 'Follows HAS_DEPENDENT and OWNED_BY paths to discover exact ripple effects and on-call escalation routes.',
      icon: GitBranch
    },
    {
      num: '03',
      title: 'TEMPORAL DECAY',
      subtitle: 'Separates historical volume from recent activity',
      desc: 'Checks edge validity dates so departed engineers are never recommended, even if they had the most commits.',
      icon: Clock
    },
    {
      num: '04',
      title: 'GROUND-TRUTH HONESTY',
      subtitle: 'Explicit negatives with zero hallucination',
      desc: 'When an edge does not exist, Helio returns a confident negative. Scored against 20 hand-planted ground truth facts.',
      icon: CheckCircle2
    }
  ];

  return (
    <section id="workflow-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          HOW IT WORKS // DETERMINISTIC GRAPH VERIFICATION
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Built on graph topology, verified against truth.
        </h2>
        <p className="mt-4 text-sm md:text-base font-mono text-[#5c5c56]">
          An LLM asked "is this answer correct?" is circular. Helio anchors the agent to a deterministic
          graph database, scoring every answer against pre-planted ground-truth facts.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {steps.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.num} className="bg-[#f4f4ec] cad-border p-6 flex flex-col justify-between relative">
              <CadCrosshair position="tl" />
              <CadCrosshair position="tr" />
              <CadCrosshair position="bl" />
              <CadCrosshair position="br" />

              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-8 h-8 bg-[#282828] text-white flex items-center justify-center font-mono font-bold text-xs">
                    {s.num}
                  </div>
                  <Icon className="w-5 h-5 text-[#e15c46]" />
                </div>

                <h3 className="font-mono font-bold text-lg text-[#282828] uppercase mb-1">
                  {s.title}
                </h3>
                <div className="font-mono text-xs font-semibold text-[#e15c46] mb-4">
                  {s.subtitle}
                </div>
              </div>

              <p className="font-mono text-xs text-[#5c5c56] leading-relaxed pt-4 cad-border-t">
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>

    </section>
  );
};
