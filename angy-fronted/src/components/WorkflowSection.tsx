import React from 'react';
import { CadCrosshair } from './CadCrosshair';
import { Eye, MessageSquare, Zap, BookOpen } from 'lucide-react';

export const WorkflowSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'OBSERVE',
      subtitle: 'Heron watches your model as you design',
      desc: 'Seamlessly tracks rooms, wall assemblies, door clearances, and stairs in the background without slowing your workstation.',
      icon: Eye
    },
    {
      num: '02',
      title: 'ADVISE',
      subtitle: 'Flags issues and suggests fixes in plain language',
      desc: 'Pinpoints non-compliant conditions and cites the exact IBC chapter or local municipal amendment in plain terms.',
      icon: MessageSquare
    },
    {
      num: '03',
      title: 'ACT',
      subtitle: 'With your approval, it makes the edit in the model',
      desc: 'One-click transaction commits CAD changes directly to Revit or Rhino elements with full rollback capability.',
      icon: Zap
    },
    {
      num: '04',
      title: 'LEARN',
      subtitle: "Picks up your firm's standards over time",
      desc: 'Memorizes firm graphic naming conventions, custom families, line weights, and partition schedules.',
      icon: BookOpen
    }
  ];

  return (
    <section id="workflow-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          WHY US // BUILT TO WORK THE WAY YOU DO
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Fits into your process instead of replacing it.
        </h2>
        <p className="mt-4 text-sm md:text-base font-mono text-[#5c5c56]">
          Heron watches quietly, speaks up when something needs attention, and only acts when you say so,
          so you stay in control the whole way through.
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
