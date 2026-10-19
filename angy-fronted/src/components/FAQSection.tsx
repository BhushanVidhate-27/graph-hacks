import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { Plus, Minus } from 'lucide-react';
import { FAQItem } from '../types';

export const FAQSection: React.FC = () => {
  const [openId, setOpenId] = useState<string>('faq1');

  const faqs: FAQItem[] = [
    {
      id: 'faq1',
      question: 'Why is a graph traversal better than vector search or RAG?',
      answer:
        'Vector search checks semantic similarity between text chunks. It cannot tell if Priya left the company 6 months ago, cannot compute a 3-hop dependency cascade, and treats superseded docs as equally valid. Helio uses FalkorDB to traverse real organizational edges with temporal properties, using text search only at the leaves.'
    },
    {
      id: 'faq2',
      question: 'How does Helio prevent the LLM from hallucinating ownership?',
      answer:
        'The agent is strictly bounded by Cypher query results. If a service like config-service has no OWNED_BY edge in the graph, the agent receives an explicit empty set and returns: "The graph contains no OWNED_BY edge. No team owns it." 5 of our 20 ground-truth questions have no answer in the graph, and Helio passes all 5.'
    },
    {
      id: 'faq3',
      question: 'How is the Priya Sharma volume vs. recency trap resolved?',
      answer:
        'Priya Sharma has 14 commits on payments-gateway — the highest in the company. A naive ORDER BY count DESC returns her, even though she left in April. Helio returns volume and recency as two distinct signals: "Ravi Menon has worked on it most recently (2026-09-28). Priya Sharma has the most commits (14), but her last touch was 2026-04-15 and is flagged as stale. Ask Ravi Menon."'
    },
    {
      id: 'faq4',
      question: 'How are conflicting decisions handled (Stripe vs. Adyen)?',
      answer:
        'Helio models architectural decisions with SUPERSEDES edges. A March doc says "single provider, Stripe." Decision D-19 (2026-05-06) established "dual provider, Adyen primary, Stripe fallback." Because D-19 supersedes the earlier doc, the graph proves the March document is obsolete.'
    },
    {
      id: 'faq5',
      question: 'Which graph database powers Helio and how is it deployed?',
      answer:
        'Helio runs on FalkorDB (Cypher query language). The entire system runs via Docker Compose with synthetic seed generation, automated schema indexing, and a single-origin API entrypoint.'
    }
  ];

  return (
    <section id="faq-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="mb-12 max-w-2xl">
        <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
          FAQS // GROUND TRUTH & ARCHITECTURE
        </div>
        <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight">
          Got Questions? We've Got Verified Answers.
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
