import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HeronButton } from './HeronButton';
import { 
  CheckCircle2, XCircle, AlertTriangle, ShieldCheck, FileText, 
  Building2, Users, Download, Search, Filter, History, SlidersHorizontal 
} from 'lucide-react';

export const DashboardSimulator: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState('proj-1');
  const [approvalList, setApprovalList] = useState([
    {
      id: 'app-1',
      code: 'IBC 1015.3',
      title: 'Atrium Railing Height Elevation',
      level: 'Level 04 - Atrium Edge',
      proposedEdit: 'Elevate guardrail from 36" to 42" with 0.5" tempered laminated glass infill.',
      user: 'Sarah Lin (Lead Architect)',
      time: '12 mins ago',
      status: 'pending'
    },
    {
      id: 'app-2',
      code: 'IBC 1010.1.2.1',
      title: 'Door 104 Swing Direction Inversion',
      level: 'Level 01 - Main Lobby',
      proposedEdit: 'Reverse swing direction into room interior to prevent corridor egress encroachment.',
      user: 'David Miller (BIM Coordinator)',
      time: '45 mins ago',
      status: 'pending'
    },
    {
      id: 'app-3',
      code: 'ICC A117.1 §604.3.1',
      title: 'Accessible Restroom Clearance Shift',
      level: 'Level 02 - Restroom Block',
      proposedEdit: 'Shift lavatory cabinet 10" north to ensure 60" turning radius unobstructed.',
      user: 'Elena Rostova (Interior Design)',
      time: '2 hours ago',
      status: 'approved'
    }
  ]);

  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleApprove = (id: string) => {
    setApprovalList((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'approved' } : item))
    );
  };

  const handleReject = (id: string) => {
    setApprovalList((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: 'rejected' } : item))
    );
  };

  const handleExportReport = () => {
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 3000);
  };

  return (
    <div className="max-w-7xl mx-auto my-8 p-4 md:p-8 select-none">
      
      {/* Dashboard Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#282828] text-white p-6 cad-border mb-8">
        <div>
          <div className="flex items-center gap-2 text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>HERON ENTERPRISE DASHBOARD // CLOUD OVERSIGHT</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-mono font-bold uppercase tracking-tight">
            Centralized Firm Compliance Queue
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportReport}
            className="flex items-center gap-2 px-4 py-2 bg-[#e15c46] text-white font-mono text-xs font-bold hover:bg-white hover:text-[#282828] cad-border transition-colors uppercase tracking-wider"
          >
            <Download className="w-4 h-4" />
            <span>{downloadSuccess ? 'REPORT DOWNLOADED' : 'EXPORT PERMIT REPORT'}</span>
          </button>
        </div>
      </div>

      {/* KPI Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Active Projects</div>
          <div className="font-mono text-3xl font-bold text-[#282828]">14</div>
          <div className="font-mono text-[10px] text-emerald-700 font-bold mt-2 flex items-center gap-1">
            <span>● 3 synced in real time</span>
          </div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">IBC 2024 Compliance Score</div>
          <div className="font-mono text-3xl font-bold text-[#e15c46]">96.8%</div>
          <div className="font-mono text-[10px] text-[#5c5c56] mt-2">+4.2% since automated remediation</div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Pending Edits in Queue</div>
          <div className="font-mono text-3xl font-bold text-[#282828]">
            {approvalList.filter((a) => a.status === 'pending').length}
          </div>
          <div className="font-mono text-[10px] text-[#e15c46] font-bold mt-2">Requires Lead Approval</div>
        </div>

        <div className="bg-[#f4f4ec] cad-border p-5 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <div className="font-mono text-xs text-[#5c5c56] uppercase mb-1">Hours Reclaimed This Month</div>
          <div className="font-mono text-3xl font-bold text-[#282828]">184 HRS</div>
          <div className="font-mono text-[10px] text-emerald-700 font-bold mt-2">Equivalent to 1.1 FTE drafter</div>
        </div>

      </div>

      {/* Main Grid: Projects & Approval Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left 4 Cols: Active Projects Selector */}
        <div className="lg:col-span-4 bg-[#f4f4ec] cad-border p-6 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div className="font-mono font-bold text-sm text-[#282828] uppercase mb-4 pb-3 cad-border-b flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-[#e15c46]" />
              <span>FIRM PROJECTS</span>
            </span>
            <span className="text-[11px] text-[#5c5c56]">BIM SYNC</span>
          </div>

          <div className="space-y-3 font-mono">
            {[
              { id: 'proj-1', name: 'Denver Atrium Tower', code: 'IBC 2024 / Denver Amendments', status: 'Active Sync', score: '98%' },
              { id: 'proj-2', name: 'Sydney Tech Innovation Hub', code: 'BCA / NCC 2022', status: 'Active Sync', score: '94%' },
              { id: 'proj-3', name: 'Austin Mixed-Use Residential', code: 'Austin Land Dev Code', status: 'Idle', score: '91%' }
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedProject(p.id)}
                className={`w-full text-left p-3 cad-border transition-colors ${
                  selectedProject === p.id
                    ? 'bg-[#282828] text-white'
                    : 'bg-white text-[#282828] hover:bg-[#ecece4]'
                }`}
              >
                <div className="font-bold text-xs uppercase mb-1">{p.name}</div>
                <div className={`text-[10px] ${selectedProject === p.id ? 'text-white/70' : 'text-[#5c5c56]'}`}>
                  {p.code}
                </div>
                <div className="flex items-center justify-between mt-2 pt-2 cad-border-t border-current/20 text-[10px]">
                  <span className="text-[#e15c46] font-bold">{p.status}</span>
                  <span className="font-bold">Score: {p.score}</span>
                </div>
              </button>
            ))}
          </div>

          {/* Firm Standards Rules Ingested */}
          <div className="mt-8 pt-6 cad-border-t font-mono">
            <div className="text-xs font-bold text-[#282828] uppercase mb-2">
              Learned Firm Standards (RAG):
            </div>
            <div className="space-y-1.5 text-[11px] text-[#5c5c56]">
              <div>• Kestrel Standard Partition Schedule v4</div>
              <div>• Minimum Door Clearance Rule 36" Net Clear</div>
              <div>• ADA Grab Bar Positioning Addendum 2025</div>
            </div>
          </div>
        </div>

        {/* Right 8 Cols: Pending Approval Queue */}
        <div className="lg:col-span-8 bg-[#f4f4ec] cad-border p-6 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div className="flex items-center justify-between pb-3 cad-border-b mb-6 font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-[#e15c46]" />
              <span className="text-sm font-bold text-[#282828] uppercase">
                Pending Model Edits & Approvals
              </span>
            </div>
            <span className="text-xs text-[#5c5c56]">
              {approvalList.filter((a) => a.status === 'pending').length} Action Items
            </span>
          </div>

          {/* List of Pending Items */}
          <div className="space-y-4 font-mono text-xs">
            {approvalList.map((item) => (
              <div
                key={item.id}
                className="bg-white cad-border p-5 transition-shadow hover:shadow-md"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-[#e15c46] text-white font-bold text-[10px] px-2 py-0.5">
                      {item.code}
                    </span>
                    <span className="font-bold text-[#282828] text-sm uppercase">
                      {item.title}
                    </span>
                  </div>

                  <span className="text-[10px] text-[#5c5c56]">{item.time}</span>
                </div>

                <div className="text-[11px] text-[#e15c46] font-bold mb-3">
                  LOCATION: {item.level}
                </div>

                <p className="text-xs text-[#282828] bg-[#ecece4] p-3 cad-border mb-4 leading-relaxed">
                  <span className="font-bold">PROPOSED EDIT: </span>
                  {item.proposedEdit}
                </p>

                <div className="flex items-center justify-between flex-wrap gap-3 pt-3 cad-border-t border-[#282828]/15">
                  <div className="text-[10px] text-[#5c5c56]">
                    TRIGGERED BY: <span className="font-bold text-[#282828]">{item.user}</span>
                  </div>

                  {item.status === 'pending' ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleApprove(item.id)}
                        className="px-4 py-1.5 bg-[#e15c46] text-white hover:bg-[#282828] font-bold text-[11px] cad-border transition-colors uppercase tracking-wider"
                      >
                        Approve & Commit
                      </button>
                      <button
                        onClick={() => handleReject(item.id)}
                        className="px-3 py-1.5 bg-transparent text-[#5c5c56] hover:bg-[#282828]/10 font-bold text-[11px] cad-border transition-colors uppercase"
                      >
                        Reject
                      </button>
                    </div>
                  ) : item.status === 'approved' ? (
                    <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>COMMITTED TO CAD MODEL</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-red-600 font-bold text-xs">
                      <XCircle className="w-4 h-4" />
                      <span>REJECTED & DISMISSED</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

        </div>

      </div>

    </div>
  );
};
