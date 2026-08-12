'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Loader2, PhoneOff, RefreshCw, CheckCircle2, Shield, ClipboardList } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ComplaintTrackerModal } from '@/components/agents-ui/complaint-tracker-modal';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, y: 0 },
    hidden: { opacity: 0, y: 15 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.4, ease: 'easeOut' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, connectionState, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  
  const [hasConnectedOnce, setHasConnectedOnce] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);
  const [isCheckingMic, setIsCheckingMic] = useState(false);
  const [showLowBandwidthNotice, setShowLowBandwidthNotice] = useState(false);
  const [isPortalOpen, setIsPortalOpen] = useState(false);

  const isConnectingState = connectionState === 'connecting' || isCheckingMic;

  // Track if we ever successfully connect to show Call Ended state on disconnect
  useEffect(() => {
    if (isConnected) {
      setHasConnectedOnce(true);
      setIsCheckingMic(false);
    }
  }, [isConnected]);

  // Monitor connection duration to warn about slow internet/low-bandwidth
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isConnectingState) {
      timer = setTimeout(() => {
        setShowLowBandwidthNotice(true);
      }, 10000);
    } else {
      setShowLowBandwidthNotice(false);
    }
    return () => clearTimeout(timer);
  }, [isConnectingState]);

  // Handle start call with microphone permissions validation
  const handleStartCall = async () => {
    setMicError(null);
    setIsCheckingMic(true);

    try {
      // Prompt/check microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Stop track immediately to release resource
      stream.getTracks().forEach((track) => track.stop());
    } catch (err: any) {
      console.error('Microphone check failed:', err);
      setIsCheckingMic(false);
      if (
        err.name === 'NotAllowedError' ||
        err.name === 'PermissionDeniedError' ||
        err.message?.toLowerCase().includes('denied')
      ) {
        setMicError(
          'Microphone permission was denied. Please allow microphone access in your browser settings to talk to Aarav.'
        );
      } else {
        setMicError('Microphone error: ' + err.message);
      }
      return;
    }

    try {
      await start();
    } catch (err: any) {
      console.error('Failed to start session:', err);
      setIsCheckingMic(false);
      setMicError('Connection failed: ' + err.message);
    }
  };

  const handleStartAgain = () => {
    setHasConnectedOnce(false);
    setMicError(null);
    setIsCheckingMic(false);
  };

  return (
    <div className="relative flex min-h-svh w-full items-center justify-center bg-radial from-slate-900 via-slate-950 to-black p-4 select-none overflow-hidden">
      
      {/* Top Floating Action Header */}
      <div className="fixed top-4 left-4 z-50 flex items-center gap-3">
        <button
          type="button"
          onClick={() => setIsPortalOpen(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-slate-700/60 text-slate-200 text-xs font-bold shadow-lg backdrop-blur-md transition-all hover:scale-105 active:scale-95 cursor-pointer"
        >
          <ClipboardList className="h-4 w-4 text-amber-400" />
          <span>Track Complaint & AI Boundaries</span>
        </button>
      </div>

      <AnimatePresence mode="wait">
        
        {/* 1. Ready / Welcome state */}
        {!isConnected && !isConnectingState && !hasConnectedOnce && (
          <MotionWelcomeView
            key="welcome"
            {...VIEW_MOTION_PROPS}
            startButtonText={appConfig.startButtonText}
            onStartCall={handleStartCall}
            micError={micError}
            isConnecting={false}
          />
        )}

        {/* 2. Connecting State */}
        {isConnectingState && !isConnected && (
          <motion.div
            key="connecting"
            {...VIEW_MOTION_PROPS}
            className="bg-card/40 border-border/50 flex max-w-md flex-col items-center justify-center rounded-3xl border p-10 text-center shadow-2xl backdrop-blur-xl"
          >
            <div className="relative">
              <div className="absolute inset-0 animate-ping rounded-full bg-primary/20"></div>
              <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 border border-primary/20 text-primary">
                <Loader2 className="h-10 w-10 animate-spin" />
              </div>
            </div>
            <h2 className="text-foreground mt-6 text-2xl font-extrabold tracking-tight">
              Connecting to Aarav...
            </h2>
            <p className="text-primary mt-1 text-sm font-medium">
              आरव से जुड़ रहे हैं...
            </p>
            <p className="text-muted-foreground mt-4 text-xs leading-relaxed max-w-xs">
              Setting up a secure financial literacy session. Please ensure your microphone is ready.
            </p>
            {showLowBandwidthNotice && (
              <div className="mt-4 rounded-xl border border-yellow-500/20 bg-yellow-500/10 p-3 text-left animate-in fade-in slide-in-from-top-2 duration-300">
                <p className="text-[10px] text-yellow-600 dark:text-yellow-400 font-medium leading-normal">
                  ⚠️ <strong>Slow connection detected / धीमा इंटरनेट कनेक्शन।</strong> Aarav is taking longer than usual to connect. Please check your network.
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* 3. Connected / Session state */}
        {isConnected && (
          <MotionSessionView
            key="session-view"
            {...VIEW_MOTION_PROPS}
            supportsChatInput={appConfig.supportsChatInput}
            supportsVideoInput={appConfig.supportsVideoInput}
            supportsScreenShare={appConfig.supportsScreenShare}
            isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
            audioVisualizerType={appConfig.audioVisualizerType || 'wave'}
            audioVisualizerColor={
              resolvedTheme === 'dark'
                ? appConfig.audioVisualizerColorDark || '#eab308'
                : appConfig.audioVisualizerColor || '#eab308'
            }
            audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
            audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
            audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
            audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
            audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
            audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
            audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
            className="fixed inset-0"
          />
        )}

        {/* 4. Call ended state */}
        {!isConnected && !isConnectingState && hasConnectedOnce && (
          <motion.div
            key="call-ended"
            {...VIEW_MOTION_PROPS}
            className="bg-card/40 border-border/50 flex max-w-md flex-col items-center justify-center rounded-3xl border p-10 text-center shadow-2xl backdrop-blur-xl"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 border border-destructive/20 text-destructive">
              <PhoneOff className="h-8 w-8" />
            </div>
            
            <h2 className="text-foreground mt-6 text-2xl font-extrabold tracking-tight">
              Call Completed
            </h2>
            <p className="text-destructive mt-1 text-sm font-medium">
              बातचीत समाप्त हुई
            </p>
            
            <div className="mt-6 w-full rounded-2xl bg-black/5 p-4 text-left dark:bg-white/5 text-xs text-muted-foreground space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="text-primary size-4 shrink-0" />
                <span>Financial literacy session with Aarav completed.</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="text-primary size-4 shrink-0" />
                <span>Remember: Keep your banking PINs and passwords safe.</span>
              </div>
            </div>

            <Button
              size="lg"
              onClick={handleStartAgain}
              className="bg-primary hover:bg-primary/95 text-primary-foreground mt-8 h-12 w-full rounded-full font-bold tracking-wider uppercase flex items-center justify-center gap-2 cursor-pointer"
            >
              <RefreshCw className="size-4" />
              Start Call Again
            </Button>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Complaint Tracker & Non-Decision Scenarios Portal Modal */}
      <ComplaintTrackerModal isOpen={isPortalOpen} onClose={() => setIsPortalOpen(false)} />
    </div>
  );
}
