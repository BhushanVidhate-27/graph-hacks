import React from 'react';
import { CadCrosshair } from './CadCrosshair';

export const ProblemsSection: React.FC = () => {
  const problems = [
    {
      index: '[01]',
      label: 'MANUAL',
      title: 'Every change is on you',
      desc: "You make each edit by hand, one at a time, even the ones you've done a hundred times before."
    },
    {
      index: '[02]',
      label: 'DISJOINTED',
      title: 'AI help sits outside your model',
      desc: "Generic AI tools can't see your project, so you keep copying, pasting, and re-explaining the same context."
    },
    {
      index: '[03]',
      label: 'BLIND',
      title: 'Nothing watches for problems',
      desc: 'Issues sit quietly in your model until you happen to spot them, if you spot them at all.'
    },
    {
      index: '[04]',
      label: 'SLOW',
      title: 'Small tasks pile up into lost days',
      desc: 'The fiddly work that fills your week is exactly the work software should be doing for you.'
    }
  ];

  return (
    <section className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Section Header */}
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          PROBLEMS // THE CURRENT REALITY
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Your design tools do what you tell them, nothing more.
        </h2>
        <p className="mt-4 text-sm md:text-base font-mono text-[#5c5c56]">
          Design software is powerful but passive. It waits for every instruction, gives no advice,
          and can't act on its own, so all the repetitive work stays on you.
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
