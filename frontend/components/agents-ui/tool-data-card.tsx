'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useRoomContext } from '@livekit/components-react';
import { RoomEvent } from 'livekit-client';
import { X, Coins, Landmark, Calculator, ExternalLink, ShieldCheck, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface ToolDataPayload {
  type: string;
  tool: 'gold_silver_price' | 'scheme_lookup' | 'fd_calculator' | string;
  data: any;
}

export function ToolDataCard() {
  const room = useRoomContext();
  const [currentData, setCurrentData] = useState<ToolDataPayload | null>(null);

  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (
      payload: Uint8Array,
      participant: any,
      kind: any,
      topic?: string
    ) => {
      try {
        const text = new TextDecoder().decode(payload);
        const parsed = JSON.parse(text);
        if (parsed.type === 'tool_data' || parsed.type === 'tool-data') {
          console.log('Received tool data on frontend:', parsed);
          setCurrentData(parsed);
        }
      } catch (err) {
        // ignore non-JSON or other data packets
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);

    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room]);

  if (!currentData) return null;

  const handleDismiss = () => setCurrentData(null);

  return (
    <AnimatePresence mode="wait">
      {currentData && (
        <motion.div
          key={JSON.stringify(currentData.data)}
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="fixed top-20 right-4 z-50 w-full max-w-sm sm:max-w-md bg-slate-900/90 border border-amber-500/30 text-slate-100 rounded-2xl p-4 shadow-2xl backdrop-blur-xl select-text"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
            <div className="flex items-center gap-2">
              {currentData.tool === 'gold_silver_price' && (
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/40">
                  <Coins className="h-4 w-4" />
                </div>
              )}
              {currentData.tool === 'scheme_lookup' && (
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/40">
                  <Landmark className="h-4 w-4" />
                </div>
              )}
              {currentData.tool === 'fd_calculator' && (
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                  <Calculator className="h-4 w-4" />
                </div>
              )}

              <div>
                <h4 className="text-xs font-bold tracking-wider uppercase text-slate-200">
                  {currentData.tool === 'gold_silver_price' && 'Live Bullion Rates / सर्राफा भाव'}
                  {currentData.tool === 'scheme_lookup' && 'Government Scheme / सरकारी योजना'}
                  {currentData.tool === 'fd_calculator' && 'FD Return Calculator / एफडी रिटर्न'}
                </h4>
                <p className="text-[10px] text-slate-400 font-medium">Real-Time Data pushed to screen</p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleDismiss}
              className="h-7 w-7 rounded-full text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>

          {/* Body Content based on tool */}
          {currentData.tool === 'gold_silver_price' && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-amber-950/40 border border-amber-500/20 rounded-xl p-2.5">
                  <span className="text-[10px] text-amber-400/80 uppercase font-semibold block">Gold 24K / 24 कैरेट</span>
                  <span className="text-lg font-extrabold text-amber-300">₹{currentData.data.gold_24k}</span>
                  <span className="text-[10px] text-slate-400 block font-medium">per gram / प्रति ग्राम</span>
                </div>
                <div className="bg-amber-950/20 border border-amber-500/20 rounded-xl p-2.5">
                  <span className="text-[10px] text-amber-400/80 uppercase font-semibold block">Gold 22K / 22 कैरेट</span>
                  <span className="text-lg font-extrabold text-amber-200">₹{currentData.data.gold_22k}</span>
                  <span className="text-[10px] text-slate-400 block font-medium">per gram / प्रति ग्राम</span>
                </div>
              </div>

              {currentData.data.silver && (
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-2 flex items-center justify-between px-3">
                  <span className="text-xs font-medium text-slate-300">Silver Rate / चांदी का भाव:</span>
                  <span className="text-sm font-bold text-slate-100">₹{currentData.data.silver} / gram</span>
                </div>
              )}

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3 text-emerald-400" />
                  {currentData.data.source}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {currentData.data.timestamp}
                </span>
              </div>
            </div>
          )}

          {currentData.tool === 'scheme_lookup' && (
            <div className="space-y-2.5 text-xs">
              <div>
                <h3 className="text-sm font-bold text-blue-300">
                  {currentData.data.name} ({currentData.data.name_hindi})
                </h3>
              </div>

              <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-2.5 space-y-1.5">
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Required Documents / आवश्यक दस्तावेज:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {currentData.data.documents?.map((doc: string, idx: number) => (
                      <span
                        key={idx}
                        className="bg-blue-950/60 text-blue-200 border border-blue-500/30 px-2 py-0.5 rounded-md text-[10px] font-medium"
                      >
                        ✓ {doc}
                      </span>
                    ))}
                  </div>
                </div>

                {currentData.data.benefits?.length > 0 && (
                  <div className="pt-1">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">Key Benefits / लाभ:</span>
                    <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-0.5 mt-0.5">
                      {currentData.data.benefits.slice(0, 3).map((b: string, idx: number) => (
                        <li key={idx}>{b}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-[10px] pt-1">
                <span className="text-slate-400">Verified: {currentData.data.data_as_of}</span>
                {currentData.data.official_url && (
                  <a
                    href={currentData.data.official_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 underline underline-offset-2"
                  >
                    Official Portal <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          )}

          {currentData.tool === 'fd_calculator' && (
            <div className="space-y-2 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-2 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">Principal Amount</span>
                  <span className="text-base font-bold text-white">₹{currentData.data.principal}</span>
                </div>
                <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-2 text-center">
                  <span className="text-[10px] text-slate-400 uppercase block font-semibold">Tenure</span>
                  <span className="text-base font-bold text-white">{currentData.data.duration_years} Years</span>
                </div>
              </div>

              <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-emerald-400 uppercase font-semibold block">Interest Earned</span>
                  <span className="text-lg font-black text-emerald-300">₹{currentData.data.interest_earned}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Final Maturity</span>
                  <span className="text-lg font-black text-white">₹{currentData.data.maturity_amount}</span>
                </div>
              </div>

              <div className="text-[10px] text-slate-400 text-center font-medium">
                {currentData.data.rate_source} ({currentData.data.rate} p.a.)
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
