import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { Plus, Minus } from 'lucide-react';
import { FAQItem } from '../types';

export const FAQSection: React.FC = () => {
  const [openId, setOpenId] = useState<string>('faq1');

  const faqs: FAQItem[] = [
    {
      id: 'faq1',
      question: 'Does Heron change my model without asking?',
      answer:
        'No. Heron always shows you the proposed edit first and waits for your approval. Nothing lands in your model until you say yes, and every edit can be rolled back with standard Undo commands.'
    },
    {
      id: 'faq2',
      question: 'Which design tools does Heron Chat work in?',
      answer:
        'Revit, Rhino, ArchiCAD, and SketchUp, with more on the way. It keeps your geometric and rule context as you move between them.'
    },
    {
      id: 'faq3',
      question: 'Can it see my whole project or just the open view?',
      answer:
        'Heron reads the whole project database for the file you are working in. Its answers and edits match your real 3D geometry and spatial parameters, not a generic example.'
    },
    {
      id: 'faq4',
      question: "What if I don't like a change it made?",
      answer:
        'Every edit is executed as a named transaction (e.g. "Heron: Door Swing Inversion") and can be instantly undone or rolled back from the history log.'
    },
    {
      id: 'faq5',
      question: 'Do I need to learn special commands or scripting?',
      answer:
        'No. Talk to Heron in everyday architectural language ("Shift room partition 6 inches east to satisfy IBC 1017"). Heron parses the geometric intent and maps it to native CAD elements.'
    }
  ];

  return (
    <section id="faq-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          FAQS // FREQUENTLY ASKED QUESTIONS
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Got Questions? We've Got Answers.
        </h2>
      </div>

      <div className="space-y-4">
        {faqs.map((faq, index) => {
          const isOpen = openId === faq.id;
          return (
            <div
              key={faq.id}
              className={`cad-border transition-colors duration-300 relative ${
                isOpen ? 'bg-[#f4f4ec]' : 'bg-[#ecece4] hover:bg-[#f4f4ec]'
              }`}
            >
              <CadCrosshair position="tl" />
              <CadCrosshair position="tr" />
              <CadCrosshair position="bl" />
              <CadCrosshair position="br" />

              <button
                onClick={() => setOpenId(isOpen ? '' : faq.id)}
                className="w-full text-left p-6 flex items-center justify-between gap-4 font-mono select-none"
              >
                <div className="flex items-center gap-4">
                  <span className={`text-xs font-bold ${isOpen ? 'text-[#e15c46]' : 'text-[#5c5c56]'}`}>
                    [0{index + 1}]
                  </span>
                  <span className="font-bold text-base md:text-lg text-[#282828] uppercase">
                    {faq.question}
                  </span>
                </div>

                <div className={`w-7 h-7 flex items-center justify-center cad-border flex-shrink-0 transition-colors ${
                  isOpen ? 'bg-[#e15c46] text-white border-[#e15c46]' : 'bg-white text-[#282828]'
                }`}>
                  {isOpen ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                </div>
              </button>

              {isOpen && (
                <div className="px-6 pb-6 pt-2 font-mono text-xs md:text-sm text-[#5c5c56] leading-relaxed cad-border-t border-[#282828]/15">
                  <p className="max-w-3xl">{faq.answer}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

    </section>
  );
};
