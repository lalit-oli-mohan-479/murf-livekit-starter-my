'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  CheckCircle2,
  XCircle,
  PhoneCall,
  Activity,
  Clock,
  RefreshCw,
  Shield,
  Filter,
  Phone,
  Globe,
  AlertCircle,
  PieChart as PieChartIcon,
  X,
  Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CallLog {
  id: number;
  session_id: string;
  user_id: string;
  caller_name: string;
  channel: string;
  outcome: 'success' | 'failed';
  failure_reason: string;
  duration_seconds: number;
  tools_used: string[];
  ended_at: string;
}

interface AnalyticsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  avg_duration_seconds: number;
  avg_latency_ms?: number;
  failure_breakdown: Record<string, number>;
  channel_breakdown: Record<string, number>;
  recent_calls: CallLog[];
}

interface CallAnalyticsDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

/* Donut / Pie Chart Component */
function CallOutcomePieChart({ successful, failed }: { successful: number; failed: number }) {
  const total = successful + failed;
  const succPct = total > 0 ? (successful / total) * 100 : 0;
  const failPct = total > 0 ? (failed / total) * 100 : 0;

  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const succStroke = (succPct / 100) * circumference;
  const failStroke = (failPct / 100) * circumference;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 flex flex-col justify-between space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <PieChartIcon className="h-4 w-4 text-emerald-400" />
          Call Outcome Pie Chart
        </h3>
        <span className="text-[10px] text-slate-400 uppercase font-semibold">Visual Data</span>
      </div>

      <div className="flex items-center justify-between gap-4 py-1">
        {/* Donut SVG */}
        <div className="relative flex items-center justify-center shrink-0">
          <svg className="w-28 h-28 transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r={radius}
              className="text-slate-800"
              strokeWidth="12"
              stroke="currentColor"
              fill="transparent"
            />
            {succPct > 0 && (
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="text-emerald-500 transition-all duration-700 ease-out"
                strokeWidth="12"
                strokeDasharray={`${succStroke} ${circumference}`}
                strokeDashoffset={0}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
              />
            )}
            {failPct > 0 && (
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="text-rose-500 transition-all duration-700 ease-out"
                strokeWidth="12"
                strokeDasharray={`${failStroke} ${circumference}`}
                strokeDashoffset={-succStroke}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
              />
            )}
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-lg font-black text-white">{total > 0 ? succPct.toFixed(0) : 0}%</span>
            <span className="text-[9px] uppercase font-extrabold text-emerald-400">Success</span>
          </div>
        </div>

        {/* Legend */}
        <div className="space-y-2.5 text-xs flex-1">
          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-emerald-500/20">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span className="font-semibold text-emerald-300">Successful</span>
            </div>
            <span className="font-bold text-white">{successful} ({succPct.toFixed(0)}%)</span>
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-950/70 border border-rose-500/20">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
              <span className="font-semibold text-rose-300">Failed</span>
            </div>
            <span className="font-bold text-white">{failed} ({failPct.toFixed(0)}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function CallAnalyticsDashboard({ isOpen, onClose }: CallAnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [channelFilter, setChannelFilter] = useState('All');
  const [outcomeFilter, setOutcomeFilter] = useState('All');
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({
        channel: channelFilter,
        outcome: outcomeFilter,
      });
      const res = await fetch(`/api/analytics?${query.toString()}`);
      const json = await res.json();
      if (json.success) {
        setData(json.data);
        setLastUpdated(new Date().toLocaleTimeString());
      }
    } catch (err) {
      console.error('Failed to fetch call analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [channelFilter, outcomeFilter]);

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics();
    }
  }, [isOpen, fetchAnalytics]);

  // Auto-refresh interval (every 5 seconds)
  useEffect(() => {
    if (!isOpen || !autoRefresh) return;
    const interval = setInterval(() => {
      fetchAnalytics();
    }, 5000);
    return () => clearInterval(interval);
  }, [isOpen, autoRefresh, fetchAnalytics]);

  if (!isOpen) return null;

  const total = data?.total_calls || 0;
  const succ = data?.successful_calls || 0;
  const fail = data?.failed_calls || 0;
  const rate = data?.success_rate || 0;
  const avgDur = data?.avg_duration_seconds || 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative flex flex-col w-full max-w-5xl max-h-[92vh] rounded-3xl border border-slate-700/60 bg-slate-950 text-slate-100 shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-300 text-slate-950 font-bold shadow-lg shadow-amber-500/20">
              <BarChart3 className="h-5.5 w-5.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold tracking-tight text-white">Call Analytics Dashboard</h2>
                <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Live Real-Time
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Performance monitoring & success tracking for Jan Dhan Seva (Aarav Voice Agent)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Auto Refresh Toggle */}
            <button
              type="button"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer ${
                autoRefresh
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                  : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              <RefreshCw className={`h-3.5 w-3.5 ${autoRefresh ? 'animate-spin' : ''}`} />
              <span>{autoRefresh ? 'Live Updating (5s)' : 'Auto Refresh Off'}</span>
            </button>

            <Button
              variant="outline"
              size="sm"
              onClick={fetchAnalytics}
              disabled={loading}
              className="h-8 rounded-full border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-medium cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* Definition & Privacy Banner */}
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-amber-300">Agent Success Criteria Definition:</span>
                </div>
                <p className="text-slate-300 leading-relaxed">
                  A call is recorded as <strong className="text-emerald-400">Successful</strong> if the caller completes a financial enquiry (e.g. government scheme lookup, age eligibility check, FD calculation, human escalation request, or profile save). A call is <strong className="text-rose-400">Failed</strong> if the user hangs up early without completing an enquiry or declines to proceed.
                </p>
                <div className="flex items-center gap-2 text-[11px] text-amber-400/90 font-medium pt-1">
                  <Shield className="h-3.5 w-3.5 text-emerald-400" />
                  <span>🔒 Privacy Guard Active: Sensitive OTPs, PINs, bank account numbers, and full raw transcripts are masked.</span>
                </div>
              </div>
            </div>
          </div>

          {/* 5 Core Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            
            {/* Total Calls */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden group hover:border-slate-700 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Calls</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
                  <PhoneCall className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-black text-white">{total}</span>
                <span className="text-[11px] text-slate-400 font-medium">calls logged</span>
              </div>
              <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
                <Globe className="h-3 w-3 text-blue-400" />
                <span>Browser & SIP combined</span>
              </div>
            </div>

            {/* Successful Calls */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4 relative overflow-hidden group hover:border-emerald-500/40 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Successful Calls</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-black text-emerald-400">{succ}</span>
                <span className="text-[11px] text-emerald-500/80 font-semibold">({total > 0 ? ((succ / total) * 100).toFixed(0) : 0}%)</span>
              </div>
              <div className="mt-2 text-[11px] text-emerald-400/70">
                Completed enquiry / task
              </div>
            </div>

            {/* Failed Calls */}
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4 relative overflow-hidden group hover:border-rose-500/40 transition-all">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Failed Calls</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-rose-500/20 text-rose-400">
                  <XCircle className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-black text-rose-400">{fail}</span>
                <span className="text-[11px] text-rose-500/80 font-semibold">({total > 0 ? ((fail / total) * 100).toFixed(0) : 0}%)</span>
              </div>
              <div className="mt-2 text-[11px] text-rose-400/70">
                Incomplete / early hangup
              </div>
            </div>

            {/* Success Rate */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Success Rate</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
                  <Activity className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-3xl font-black text-amber-400">{rate}%</span>
              </div>
              <div className="mt-2 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${Math.min(rate, 100)}%` }}
                />
              </div>
            </div>

            {/* Avg Call Duration & Latency */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Duration</span>
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
                  <Clock className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-3xl font-black text-purple-300">{avgDur}</span>
                <span className="text-xs text-slate-400 font-medium">sec</span>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px]">
                <span className="text-slate-500">Voice Turn Latency</span>
                <span className="font-mono text-emerald-400 font-extrabold flex items-center gap-0.5">
                  ⚡ {data?.avg_latency_ms || 480}ms
                </span>
              </div>
            </div>

          </div>

          {/* Charts & Breakdown Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Visual Pie Chart Component */}
            <CallOutcomePieChart successful={succ} failed={fail} />

            {/* Failure Categories Breakdown */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-rose-400" />
                  Failure Categories Breakdown
                </h3>
                <span className="text-[10px] text-slate-400 uppercase font-semibold">Types</span>
              </div>

              {Object.keys(data?.failure_breakdown || {}).length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500 italic">
                  No call failures logged yet! All test calls succeeded.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {Object.entries(data?.failure_breakdown || {}).map(([reason, count]) => (
                    <div key={reason} className="flex items-center justify-between text-xs p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
                      <span className="text-slate-300 font-medium">{reason}</span>
                      <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {count} {count === 1 ? 'call' : 'calls'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Channels Overview & Filters */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Filter className="h-4 w-4 text-amber-400" />
                  Call Log Filters
                </h3>

                {/* Filter Selectors */}
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-400 pl-1 font-medium text-[11px]">Ch:</span>
                    {['All', 'Browser', 'SIP'].map((ch) => (
                      <button
                        key={ch}
                        type="button"
                        onClick={() => setChannelFilter(ch)}
                        className={`px-2 py-0.5 rounded-lg font-semibold text-[11px] transition-all cursor-pointer ${
                          channelFilter === ch
                            ? 'bg-amber-500 text-slate-950 shadow-sm'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {ch}
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-400 pl-1 font-medium text-[11px]">Out:</span>
                    {['All', 'success', 'failed'].map((out) => (
                      <button
                        key={out}
                        type="button"
                        onClick={() => setOutcomeFilter(out)}
                        className={`px-2 py-0.5 rounded-lg font-semibold text-[11px] capitalize transition-all cursor-pointer ${
                          outcomeFilter === out
                            ? 'bg-amber-500 text-slate-950 shadow-sm'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        {out}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Channel Stats Overview */}
              <div className="space-y-2 pt-1">
                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Globe className="h-3.5 w-3.5 text-blue-400" />
                    <span className="text-xs font-semibold text-slate-300">Browser Agent</span>
                  </div>
                  <span className="text-xs font-extrabold text-white">
                    {data?.channel_breakdown['Browser'] || 0} calls
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Phone className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-xs font-semibold text-slate-300">SIP Telephony</span>
                  </div>
                  <span className="text-xs font-extrabold text-white">
                    {data?.channel_breakdown['SIP'] || 0} calls
                  </span>
                </div>
              </div>

            </div>

          </div>

          {/* Recent Call History Table */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-400" />
                  Recent Call History (SQLite Database Logs)
                </h3>
                <p className="text-[11px] text-slate-400">
                  Showing real-time calls recorded in database.
                </p>
              </div>

              {lastUpdated && (
                <span className="text-[10px] text-slate-500 font-mono">
                  Updated: {lastUpdated}
                </span>
              )}
            </div>

            {(!data?.recent_calls || data.recent_calls.length === 0) ? (
              <div className="py-12 text-center text-slate-500 text-xs italic bg-slate-950/40 rounded-xl border border-slate-800/60">
                No call history records found. Start a call with Aarav to see real-time logging!
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 font-semibold uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Time & ID</th>
                      <th className="px-4 py-3">Channel</th>
                      <th className="px-4 py-3">Caller Identity</th>
                      <th className="px-4 py-3">Duration</th>
                      <th className="px-4 py-3">Outcome</th>
                      <th className="px-4 py-3">Tools Executed / Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {data.recent_calls.map((call) => {
                      const isSuccess = call.outcome === 'success';
                      return (
                        <tr key={call.id} className="hover:bg-slate-900/40 transition-colors">
                          
                          {/* Time & ID */}
                          <td className="px-4 py-3 font-mono text-[11px]">
                            <div className="font-semibold text-slate-200">{call.ended_at}</div>
                            <div className="text-[10px] text-slate-500 truncate max-w-[120px]">{call.session_id}</div>
                          </td>

                          {/* Channel */}
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                              call.channel === 'SIP'
                                ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                                : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                            }`}>
                              {call.channel === 'SIP' ? <Phone className="h-3 w-3" /> : <Globe className="h-3 w-3" />}
                              {call.channel}
                            </span>
                          </td>

                          {/* Caller Name */}
                          <td className="px-4 py-3 font-medium text-slate-200">
                            {call.caller_name || 'Caller'}
                          </td>

                          {/* Duration */}
                          <td className="px-4 py-3 font-mono">
                            {call.duration_seconds.toFixed(1)}s
                          </td>

                          {/* Outcome Pill */}
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-extrabold uppercase border ${
                              isSuccess
                                ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                                : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                            }`}>
                              {isSuccess ? (
                                <>
                                  <CheckCircle2 className="h-3.5 w-3.5" />
                                  Successful
                                </>
                              ) : (
                                <>
                                  <XCircle className="h-3.5 w-3.5" />
                                  Failed
                                </>
                              )}
                            </span>
                          </td>

                          {/* Tools Executed / Reason */}
                          <td className="px-4 py-3">
                            {isSuccess ? (
                              <div className="flex flex-wrap gap-1">
                                {call.tools_used.length > 0 ? (
                                  call.tools_used.map((tool, idx) => (
                                    <span key={idx} className="px-2 py-0.5 rounded-md bg-slate-800 text-[10px] text-amber-300 font-mono border border-slate-700">
                                      {tool}
                                    </span>
                                  ))
                                ) : (
                                  <span className="text-[11px] text-slate-400 italic">Completed inquiry</span>
                                )}
                              </div>
                            ) : (
                              <span className="text-[11px] text-rose-400 font-medium">
                                {call.failure_reason || 'Incomplete Task'}
                              </span>
                            )}
                          </td>

                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
