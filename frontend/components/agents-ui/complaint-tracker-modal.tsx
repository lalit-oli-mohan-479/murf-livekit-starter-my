'use client';

import React, { useState, useEffect } from 'react';
import { Search, ShieldAlert, CheckCircle2, Clock, AlertTriangle, FileText, Lock, UserCheck, RefreshCw, X, HelpCircle, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TicketData {
  reference_id: string;
  caller_name: string;
  contact_method: string;
  reason_category: string;
  issue_summary: string;
  steps_already_taken: string;
  urgency: string;
  caller_language: string;
  status: string;
  created_at: string;
}

const NON_DECISION_SCENARIOS = [
  {
    icon: ShieldAlert,
    title: '1. Unauthorized Transactions & Account Fraud',
    color: 'border-red-500/40 bg-red-950/20 text-red-400',
    badge: 'Emergency Escalation',
    example: 'Caller reports money deducted without OTP or PIN.',
    why: 'Agent cannot authorize financial refunds or overturn security flags. Instant ticket created for Bank Cyber Desk.',
  },
  {
    icon: Lock,
    title: '2. Account Freeze & KYC Rejection',
    color: 'border-amber-500/40 bg-amber-950/20 text-amber-400',
    badge: 'High Priority Escalation',
    example: 'Aadhaar/PAN mismatch causing account freeze.',
    why: 'Agent cannot bypass regulatory compliance checks. Ticket escalated to Branch Manager for document review.',
  },
  {
    icon: FileText,
    title: '3. Loan Waivers & Interest Rate Reductions',
    color: 'border-blue-500/40 bg-blue-950/20 text-blue-400',
    badge: 'Policy Constraint',
    example: 'Kisan credit loan waiver or interest rate concession request.',
    why: 'Agent is not empowered to grant financial waivers or modify loan contracts without Credit Committee sanction.',
  },
  {
    icon: UserCheck,
    title: '4. Nominee Payouts & Death Claim Settlement',
    color: 'border-purple-500/40 bg-purple-950/20 text-purple-400',
    badge: 'Legal Constraint',
    example: 'Claiming funds from deceased account holder’s Jan Dhan account.',
    why: 'Agent cannot verify legal heirship or death certificates. Transferred to Senior Settlement Officer.',
  },
];

export function ComplaintTrackerModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'tracker' | 'scenarios'>('tracker');
  const [searchRef, setSearchRef] = useState('');
  const [tickets, setTickets] = useState<TicketData[]>([]);
  const [searchedTicket, setSearchedTicket] = useState<TicketData | null | 'not_found'>(null);
  const [loading, setLoading] = useState(false);

  const fetchAllTickets = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/escalations');
      const json = await res.json();
      if (json.success && Array.isArray(json.data)) {
        setTickets(json.data);
      }
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAllTickets();
    }
  }, [isOpen]);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchRef.trim()) {
      setSearchedTicket(null);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`/api/escalations?ref=${encodeURIComponent(searchRef.trim())}`);
      const json = await res.json();
      if (json.success && json.data && json.data.reference_id) {
        setSearchedTicket(json.data);
      } else {
        setSearchedTicket('not_found');
      }
    } catch (err) {
      setSearchedTicket('not_found');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[85vh] flex flex-col bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden text-slate-100">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 p-4 px-6 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold tracking-wide">Jan Dhan Support & Escalation Portal</h2>
              <p className="text-xs text-slate-400">Track complaints, search reference IDs, and view AI guardrail boundaries</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 bg-slate-950/40 px-6 gap-4">
          <button
            onClick={() => setActiveTab('tracker')}
            className={`py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'tracker'
                ? 'border-amber-400 text-amber-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="h-3.5 w-3.5" /> Complaint Tracker
          </button>
          <button
            onClick={() => setActiveTab('scenarios')}
            className={`py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-all flex items-center gap-2 ${
              activeTab === 'scenarios'
                ? 'border-amber-400 text-amber-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <HelpCircle className="h-3.5 w-3.5" /> Non-Decision Boundaries
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === 'tracker' && (
            <div className="space-y-5">
              {/* Search Bar */}
              <form onSubmit={handleSearch} className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Enter Escalation Reference ID (e.g. ESC-34036)..."
                    value={searchRef}
                    onChange={(e) => {
                      setSearchRef(e.target.value);
                      if (!e.target.value) setSearchedTicket(null);
                    }}
                    className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-amber-500/60 rounded-xl transition-all"
                  />
                </div>
                <Button type="submit" variant="default" className="bg-amber-500 text-slate-950 hover:bg-amber-400 font-bold rounded-xl px-5">
                  Search
                </Button>
                <Button type="button" variant="outline" onClick={fetchAllTickets} className="border-slate-800 hover:bg-slate-800 rounded-xl">
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </form>

              {/* Searched Ticket Result */}
              {searchedTicket && searchedTicket !== 'not_found' && (
                <div className="bg-slate-950 border border-amber-500/40 rounded-xl p-4 space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-400 uppercase">Ref ID:</span>
                      <span className="text-base font-black text-amber-300 tracking-wider">{searchedTicket.reference_id}</span>
                    </div>
                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                      searchedTicket.status === 'Resolved'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : searchedTicket.status === 'In Progress'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}>
                      ● {searchedTicket.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-400">Caller Name:</span>
                      <p className="font-bold text-slate-200">{searchedTicket.caller_name}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Urgency:</span>
                      <p className="font-bold text-amber-400">{searchedTicket.urgency}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Category:</span>
                      <p className="font-bold text-slate-200">{searchedTicket.reason_category}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Created At:</span>
                      <p className="font-bold text-slate-200">{searchedTicket.created_at}</p>
                    </div>
                  </div>

                  <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs">
                    <span className="text-slate-400 block mb-1 font-semibold">Sanitized Issue Summary:</span>
                    <p className="text-slate-200 leading-relaxed">{searchedTicket.issue_summary}</p>
                  </div>
                </div>
              )}

              {searchedTicket === 'not_found' && (
                <div className="bg-rose-950/20 border border-rose-500/30 rounded-xl p-4 text-center text-xs text-rose-300">
                  No complaint found matching Reference ID "<span className="font-bold">{searchRef}</span>". Please check your ID and try again.
                </div>
              )}

              {/* List of All Complaints */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>Recent Escalations ({tickets.length})</span>
                  <span className="text-[10px] text-slate-500 font-normal">Real-time SQLite Data</span>
                </h3>

                {tickets.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
                    No active complaint tickets recorded yet. Ask Aarav to trigger an escalation or status check!
                  </div>
                ) : (
                  <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                    {tickets.map((t) => (
                      <div key={t.reference_id} className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 hover:border-slate-700 transition-colors space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-amber-300">{t.reference_id}</span>
                            <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                              {t.reason_category}
                            </span>
                          </div>
                          <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                            t.status === 'Resolved'
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                              : t.status === 'In Progress'
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          }`}>
                            {t.status}
                          </span>
                        </div>

                        <p className="text-xs text-slate-300 line-clamp-2">{t.issue_summary}</p>

                        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-900">
                          <span>Caller: <strong>{t.caller_name}</strong> ({t.contact_method})</span>
                          <span>{t.created_at}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'scenarios' && (
            <div className="space-y-4 text-xs">
              <div className="bg-amber-950/30 border border-amber-500/30 rounded-xl p-3 text-amber-300 text-xs">
                <strong>🤖 Agent Guardrail Rule:</strong> Aarav is strictly prohibited from taking binding legal or financial decisions. In high-risk scenarios, it automatically generates a human help request and redacts sensitive PII.
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {NON_DECISION_SCENARIOS.map((sc, idx) => {
                  const IconComp = sc.icon;
                  return (
                    <div key={idx} className={`border rounded-xl p-4 space-y-2.5 bg-slate-950/80 ${sc.color}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <IconComp className="h-4 w-4" />
                          <h4 className="font-bold text-slate-100">{sc.title}</h4>
                        </div>
                        <span className="text-[9px] uppercase font-extrabold px-2 py-0.5 rounded bg-black/40 border border-current">
                          {sc.badge}
                        </span>
                      </div>

                      <div className="space-y-1">
                        <span className="text-[10px] text-slate-400 uppercase font-semibold">User Query Example:</span>
                        <p className="text-slate-200 italic">"{sc.example}"</p>
                      </div>

                      <div className="pt-2 border-t border-slate-800/80">
                        <span className="text-[10px] text-amber-400 uppercase font-semibold">Why Agent Escalates:</span>
                        <p className="text-slate-300 text-[11px] leading-snug mt-0.5">{sc.why}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="border-t border-slate-800 p-3 px-6 bg-slate-950/60 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5" /> PII Masking & Database Verification Active
          </span>
          <Button size="sm" variant="ghost" onClick={onClose} className="text-slate-300 hover:text-white text-xs">
            Close Portal
          </Button>
        </div>

      </div>
    </div>
  );
}
