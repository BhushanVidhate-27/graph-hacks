import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HeronButton } from './HeronButton';
import { 
  Database, ShieldCheck, Download, AlertTriangle, CheckCircle2, 
  GitBranch, Server, Users, Clock, AlertOctagon, RefreshCw 
} from 'lucide-react';

export const DashboardSimulator: React.FC = () => {
  const [selectedTeam, setSelectedTeam] = useState('All');
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const services = [
    {
      name: 'payments-gateway',
      team: 'Platform',
      tier: 'Tier 1',
      sla: '99.99%',
      onCall: 'Ravi Menon',
      blastRadius: 4,
      staleness: 'Fresh (2026-09-28)',
      status: 'healthy',
      trapNote: 'Priya Sharma (14 commits) departed. Ravi Menon active.'
    },
    {
      name: 'ledger-service',
      team: 'Ledger',
      tier: 'Tier 1',
      sla: '99.95%',
      onCall: 'Diego Alvarez',
      blastRadius: 2,
      staleness: 'Fresh (2026-10-14)',
      status: 'healthy',
      trapNote: 'Diego Alvarez on-call this week (Ravi also on rotation).'
    },
    {
      name: 'checkout-api',
      team: 'Payments',
      tier: 'Tier 1',
      sla: '99.99%',
      onCall: 'Mei Lin',
      blastRadius: 3,
      staleness: 'Fresh (2026-10-02)',
      status: 'healthy',
      trapNote: 'Directly cascades if payments-gateway dies.'
    },
    {
      name: 'config-service',
      team: 'UNOWNED (NULL)',
      tier: 'Tier 2',
      sla: 'None',
      onCall: 'None',
      blastRadius: 2,
      staleness: 'Stale (>120 days)',
      status: 'orphan',
      trapNote: 'Fact 04: The failure test. No OWNED_BY edge exists in graph.'
    },
    {
      name: 'dispute-service',
      team: 'Risk',
      tier: 'Tier 2',
      sla: 'EMPTY (Missing)',
      onCall: 'Aisha Rao',
      blastRadius: 1,
      staleness: 'Expiring (valid_to 2026-06-30)',
      status: 'warning',
      trapNote: 'SLA property missing in CSV schema.'
    },
    {
      name: 'fraud-engine',
      team: 'Risk',
      tier: 'Tier 1',
      sla: '99.9%',
      onCall: 'Carlos Ruiz',
      blastRadius: 3,
      staleness: 'Fresh (2026-10-11)',
      status: 'healthy',
      trapNote: 'Dependent on payments-gateway stream.'
    }
  ];

  const filtered = selectedTeam === 'All' 
    ? services 
    : services.filter((s) => s.team === selectedTeam);

  const handleExportCypher = () => {
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  return (
    <div className="max-w-7xl mx-auto my-8 p-4 md:p-8 select-none">
      
      {/* Dashboard Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#282828] text-white p-6 cad-border mb-8">
        <div>
          <div className="flex items-center gap-2 text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-1">
            <Database className="w-4 h-4" />
            <span>FALKORDB KNOWLEDGE GRAPH // CONSOLE</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-mono font-bold uppercase tracking-tight">
            Helio Company Brain Topology
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCypher}
            className="flex items-center gap-2 px-4 py-2 bg-[#e15c46] text-white font-mono text-xs font-bold hover:bg-white hover:text-[#282828] cad-border transition-colors uppercase tracking-wider"
          >
            <Download className="w-4 h-4" />
            <span>{downloadSuccess ? 'EXPORTED CYPHER DUMP' : 'EXPORT CYPHER GRAPH'}</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Total Graph Nodes</div>
          <div className="font-mono text-3xl font-bold text-[#282828]">2,400+</div>
          <div className="font-mono text-[10px] text-emerald-700 font-bold mt-2 flex items-center gap-1">
            <span>● 120 Persons · 20 Services · 5 Teams</span>
          </div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Ground Truth Score</div>
          <div className="font-mono text-3xl font-bold text-[#e15c46]">100%</div>
          <div className="font-mono text-[10px] text-[#5c5c56] mt-2">20/20 hand-planted facts passed</div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Unowned Services (Honest Negatives)</div>
          <div className="font-mono text-3xl font-bold text-amber-600">1</div>
          <div className="font-mono text-[10px] text-amber-700 font-bold mt-2">config-service (No OWNED_BY)</div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Decisions Provenance</div>
          <div className="font-mono text-3xl font-bold text-[#282828]">40 ADRs</div>
          <div className="font-mono text-[10px] text-emerald-700 font-bold mt-2">D-19 supersedes March doc</div>
        </div>

      </div>

      {/* Main Table: Microservices & Ownership Graph */}
      <div className="bg-[#f4f4ec] cad-border p-6 relative">
        <CadCrosshair position="tl" />
        <CadCrosshair position="tr" />
        <CadCrosshair position="bl" />
        <CadCrosshair position="br" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 cad-border-b mb-6 font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-[#e15c46]" />
            <span className="text-sm font-bold text-[#282828] uppercase">
              Microservices Directory (:Service Nodes)
            </span>
          </div>

          {/* Team Filter Pills */}
          <div className="flex flex-wrap gap-1 text-xs">
            {['All', 'Platform', 'Ledger', 'Payments', 'Risk'].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedTeam(t)}
                className={`px-3 py-1 cad-border font-bold uppercase transition-colors ${
                  selectedTeam === t
                    ? 'bg-[#282828] text-white'
                    : 'bg-white text-[#282828] hover:bg-[#ecece4]'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Services Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="bg-[#ecece4] text-[#5c5c56] uppercase border-b border-[#282828]/20">
                <th className="p-3">Service Name</th>
                <th className="p-3">Owning Team</th>
                <th className="p-3">Tier</th>
                <th className="p-3">On-Call Person</th>
                <th className="p-3">Blast Radius</th>
                <th className="p-3">Freshness</th>
                <th className="p-3">Ground Truth Diagnostic</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#282828]/10 bg-white">
              {filtered.map((s) => (
                <tr key={s.name} className="hover:bg-[#fcfcf8] transition-colors">
                  <td className="p-3 font-bold text-[#282828]">
                    <div className="flex items-center gap-1.5">
                      <Server className="w-3.5 h-3.5 text-[#e15c46]" />
                      <span>{s.name}</span>
                    </div>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 cad-border text-[10px] font-bold ${
                      s.team.includes('NULL') ? 'bg-amber-100 text-amber-800 border-amber-300' : 'bg-[#ecece4] text-[#282828]'
                    }`}>
                      {s.team}
                    </span>
                  </td>
                  <td className="p-3 text-[11px] text-[#5c5c56]">{s.tier}</td>
                  <td className="p-3 font-bold text-[#282828]">{s.onCall}</td>
                  <td className="p-3">
                    <span className="font-bold text-[#e15c46]">{s.blastRadius} hops</span>
                  </td>
                  <td className="p-3 text-[11px] text-[#5c5c56]">{s.staleness}</td>
                  <td className="p-3 text-[10px] text-[#5c5c56] italic">{s.trapNote}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
};
