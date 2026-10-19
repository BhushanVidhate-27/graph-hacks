import React from 'react';
import { CadCrosshair } from './CadCrosshair';

export const RolesSection: React.FC = () => {
  const roles = [
    {
      title: 'ARCHITECTS',
      desc: 'Hand the repetitive modelling to Heron and keep your focus on design.',
      num: '[01]'
    },
    {
      title: 'INTERIOR DESIGNERS',
      desc: 'Get quick help with layouts, fixtures, and clearances without leaving your model.',
      num: '[02]'
    },
    {
      title: 'BIM MANAGERS',
      desc: "Keep models clean and on-standard with an agent that knows your firm's rules.",
      num: '[03]'
    },
    {
      title: 'ENGINEERS',
      desc: 'Run discipline-specific checks and edits in the model, so coordination issues surface earlier.',
      num: '[04]'
    },
    {
      title: 'DRAFTERS',
      desc: 'Skip tedious drawing cleanup and let Heron handle the repeatable parts.',
      num: '[05]'
    },
    {
      title: 'DESIGN LEADS',
      desc: "Keep quality and standards consistent across everyone's work.",
      num: '[06]'
    },
    {
      title: 'SMALL FIRMS',
      desc: 'Get the output of a bigger team without adding headcount.',
      num: '[07]'
    },
    {
      title: 'LANDSCAPE ARCHITECTS',
      desc: 'Sort grading, site elements, and layouts without manual grind.',
      num: '[08]'
    }
  ];

  return (
    <section className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          USE CASES // MADE FOR THE PEOPLE IN THE MODEL
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Built for every role in the design office
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
                <span className="text-[#e15c46] font-bold">DISCIPLINE</span>
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
