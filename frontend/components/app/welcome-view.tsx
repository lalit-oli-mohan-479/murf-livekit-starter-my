'use client';

import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { 
  ShieldAlert, 
  CheckCircle2, 
  Lock, 
  HelpCircle, 
  PhoneCall, 
  ShieldCheck, 
  UserCheck, 
  ArrowRight,
  Sparkles
} from 'lucide-react';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  micError?: string | null;
  isConnecting?: boolean;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  micError,
  isConnecting,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="mx-auto w-full max-w-6xl px-4 py-8 md:py-16 animate-in fade-in duration-700">
      
      {/* 1. Header/Navbar */}
      <header className="mb-12 flex flex-col items-center justify-between gap-4 border-b border-border/20 pb-6 md:flex-row">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 rounded-xl p-2.5 border border-primary/20">
            <span className="text-2xl">🏦</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
              Jan Dhan Seva <span className="text-primary text-sm font-semibold px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20">जन धन सेवा</span>
            </h1>
            <p className="text-xs text-muted-foreground">National Financial Literacy Campaign</p>
          </div>
        </div>
        
        <nav className="flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <a href="#schemes" className="hover:text-primary transition-colors">Government Schemes</a>
          <a href="#safety" className="hover:text-primary transition-colors">Safety Guidelines</a>
          <div className="h-4 w-px bg-border/40"></div>
          <div className="flex items-center gap-1.5 text-xs text-primary font-semibold px-3 py-1 rounded-full bg-primary/10">
            <PhoneCall className="size-3" />
            <span>Fraud Help: 1915</span>
          </div>
        </nav>
      </header>

      {/* Mic Error Block */}
      {micError && (
        <div className="mb-8 rounded-2xl border border-destructive/30 bg-destructive/10 p-5 text-left backdrop-blur-md animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-start gap-3">
            <ShieldAlert className="text-destructive mt-0.5 size-5 shrink-0" />
            <div>
              <h3 className="text-foreground text-sm font-bold tracking-tight">
                Microphone Access Denied / Blocked
              </h3>
              <p className="text-muted-foreground mt-1 text-xs leading-relaxed text-pretty md:text-sm">
                Aarav needs microphone access to hear and talk to you. Please enable your microphone:
              </p>
              <ul className="text-muted-foreground mt-2 list-inside list-disc text-xs space-y-1">
                <li>Click the **Lock/Site Settings** icon next to the website address in your URL bar.</li>
                <li>Toggle the **Microphone** setting to **Allow**.</li>
                <li>Reload the page and click "Start Call" again.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 2. Hero Section (2-Columns) */}
      <div className="grid grid-cols-1 gap-12 items-center lg:grid-cols-12 mb-16">
        
        {/* Left Column: Website Branding Copy */}
        <div className="lg:col-span-7 text-left space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-semibold text-primary uppercase tracking-wide">
            <Sparkles className="size-3" />
            <span>Empowering India's Citizens</span>
          </div>
          
          <h2 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl leading-tight">
            Sashakt Citizen,<br />
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Surakshit Banking
            </span>
          </h2>
          
          <p className="text-base text-muted-foreground leading-relaxed max-w-xl">
            Welcome to the National Financial Literacy Campaign platform. We believe that every citizen deserves safe, simple, and reliable access to financial tools and state benefits. 
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-card/20 border border-border/10">
              <ShieldCheck className="text-primary mt-1 size-5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-foreground">Safe & Secure</h4>
                <p className="text-[11px] text-muted-foreground">Learn safe digital banking rules.</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-xl bg-card/20 border border-border/10">
              <UserCheck className="text-primary mt-1 size-5 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-foreground">Bilingual AI Guide</h4>
                <p className="text-[11px] text-muted-foreground">Talk naturally in Hindi, Hinglish, or English.</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-4 border-t border-border/10">
            <span className="text-xs text-muted-foreground">Supported by:</span>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-muted/40 text-[10px] font-bold text-muted-foreground tracking-wider uppercase">
              🏦 Government Welfare Schemes
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-muted/40 text-[10px] font-bold text-muted-foreground tracking-wider uppercase">
              🤖 Murf Falcon Voice TTS
            </div>
          </div>
        </div>

        {/* Right Column: Interaction Welcome Box */}
        <div className="lg:col-span-5">
          <section className="bg-card/30 border border-border/40 rounded-3xl p-8 text-center shadow-2xl backdrop-blur-xl hover:border-primary/20 transition-all duration-500">
            {/* Active Status Badge */}
            <div className="bg-primary/10 border-primary/20 text-primary inline-flex items-center gap-1.5 rounded-full border px-3 py-0.5 text-xs font-semibold tracking-wider">
              <CheckCircle2 className="size-3" />
              LIVE GUIDE AVAILABLE
            </div>

            {/* Aarav Avatar */}
            <div className="relative mt-6 mx-auto w-fit">
              <div className="border-primary/20 absolute -inset-2 rounded-full border bg-gradient-to-tr from-primary/30 to-accent/20 blur-sm"></div>
              <div className="relative size-28 overflow-hidden rounded-full border-2 border-primary bg-muted bg-slate-800">
                <Image
                  src="/aarav-avatar.png"
                  alt="Aarav - Financial Guide"
                  fill
                  className="object-cover"
                  priority
                />
              </div>
              <span className="absolute right-1 bottom-1 flex h-4 w-4">
                <span className="bg-primary absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"></span>
                <span className="bg-primary relative inline-flex h-4 w-4 rounded-full border border-card"></span>
              </span>
            </div>

            {/* Title & Info */}
            <h3 className="text-foreground mt-5 text-2xl font-bold tracking-tight">
              Talk to Aarav (आरव)
            </h3>
            <p className="text-muted-foreground mt-2 text-xs leading-relaxed max-w-xs mx-auto">
              Your AI-powered digital guide. Ask him about savings account options, pension schemes, or calculate interest rates in real-time.
            </p>

            {/* Safe Banking Guardrail Warning */}
            <div className="border-primary/10 bg-primary/5 mt-6 flex items-start gap-2.5 rounded-2xl border p-3.5 text-left max-w-sm mx-auto">
              <Lock className="text-primary mt-0.5 size-4 shrink-0" />
              <p className="text-[11px] leading-relaxed text-muted-foreground">
                <strong className="text-foreground font-bold">Safety Guardrail:</strong> Aarav will <span className="underline decoration-destructive decoration-2">NEVER</span> ask for your ATM PIN, UPI PIN, OTP, or password. Keep your credentials private.
              </p>
            </div>

            {/* Action CTA Button */}
            <Button
              size="lg"
              onClick={onStartCall}
              disabled={isConnecting}
              className="bg-primary hover:bg-primary/95 text-primary-foreground mt-8 h-12 w-full max-w-xs rounded-full font-bold tracking-wider uppercase transition-all duration-300 shadow-[0_0_15px_rgba(var(--primary),0.3)] hover:shadow-[0_0_25px_rgba(var(--primary),0.5)] cursor-pointer flex items-center justify-center gap-2"
            >
              {isConnecting ? 'Connecting...' : startButtonText || 'Start Talking'}
              <ArrowRight className="size-4" />
            </Button>

            {/* Language help info */}
            <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground">
              <HelpCircle className="size-3" />
              <span>Hindi, Hinglish, and English supported.</span>
            </div>
          </section>
        </div>

      </div>

      {/* 3. Government Schemes Feature Grid */}
      <section id="schemes" className="mb-16 scroll-mt-6">
        <div className="text-center max-w-xl mx-auto mb-10">
          <h3 className="text-2xl font-bold text-foreground">Government Social Security & Banking Schemes</h3>
          <p className="text-xs text-muted-foreground mt-2">
            Aarav can help you check eligibility and explain details of these national schemes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* PMJDY Card */}
          <div className="bg-card/20 border border-border/10 rounded-2xl p-5 hover:border-primary/20 transition-all">
            <span className="text-2xl">🏦</span>
            <h4 className="text-sm font-bold text-foreground mt-3">Jan Dhan Yojana (PMJDY)</h4>
            <p className="text-xs text-muted-foreground mt-2">
              Zero-balance savings account providing basic banking access, RuPay card, and overdraft options.
            </p>
            <div className="mt-4 pt-3 border-t border-border/10 text-[10px] text-primary font-bold">
              Min Age: 10 Years
            </div>
          </div>

          {/* APY Card */}
          <div className="bg-card/20 border border-border/10 rounded-2xl p-5 hover:border-primary/20 transition-all">
            <span className="text-2xl">👴</span>
            <h4 className="text-sm font-bold text-foreground mt-3">Atal Pension Yojana (APY)</h4>
            <p className="text-xs text-muted-foreground mt-2">
              Guaranteed monthly pension scheme of up to ₹5,000 for workers in the unorganized sector.
            </p>
            <div className="mt-4 pt-3 border-t border-border/10 text-[10px] text-primary font-bold">
              Age limit: 18 - 40 Years
            </div>
          </div>

          {/* PMSBY Card */}
          <div className="bg-card/20 border border-border/10 rounded-2xl p-5 hover:border-primary/20 transition-all">
            <span className="text-2xl">🛡️</span>
            <h4 className="text-sm font-bold text-foreground mt-3">Suraksha Bima (PMSBY)</h4>
            <p className="text-xs text-muted-foreground mt-2">
              Accidental death and disability insurance cover of ₹2 Lakhs for a premium of just ₹20/year.
            </p>
            <div className="mt-4 pt-3 border-t border-border/10 text-[10px] text-primary font-bold">
              Age limit: 18 - 70 Years
            </div>
          </div>

          {/* PMJJBY Card */}
          <div className="bg-card/20 border border-border/10 rounded-2xl p-5 hover:border-primary/20 transition-all">
            <span className="text-2xl">❤️</span>
            <h4 className="text-sm font-bold text-foreground mt-3">Jeevan Jyoti Bima (PMJJBY)</h4>
            <p className="text-xs text-muted-foreground mt-2">
              Life insurance coverage of ₹2 Lakhs for any cause of death with a yearly premium of ₹436.
            </p>
            <div className="mt-4 pt-3 border-t border-border/10 text-[10px] text-primary font-bold">
              Age limit: 18 - 50 Years
            </div>
          </div>
        </div>
      </section>

      {/* 4. Safety Tips / Fraud Prevention */}
      <section id="safety" className="mb-16 scroll-mt-6 bg-linear-to-r from-primary/5 via-accent/5 to-primary/5 border border-primary/20 rounded-3xl p-6 md:p-8 text-left">
        <div className="flex flex-col md:flex-row gap-6 items-center">
          <div className="bg-primary/10 rounded-2xl p-4 border border-primary/20">
            <ShieldAlert className="size-8 text-primary" />
          </div>
          <div className="space-y-2">
            <h4 className="text-lg font-bold text-foreground">Surakshit Banking Guidelines (सुरक्षित बैंकिंग)</h4>
            <p className="text-xs text-muted-foreground">
              Always follow these safe banking rules. Reporting online financial fraud promptly can help block and retrieve stolen funds.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 text-xs">
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="text-destructive font-bold">❌</span>
                <span>Never share OTP or UPI PIN</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="text-destructive font-bold">❌</span>
                <span>Do not click suspicious links</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="text-primary font-bold">📞</span>
                <span>Report fraud immediately to 1915</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Footer */}
      <footer className="border-t border-border/20 pt-8 text-center space-y-4 text-xs text-muted-foreground">
        <div className="flex justify-center gap-6">
          <a href="#" className="hover:text-primary transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-primary transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-primary transition-colors">Government Portal</a>
        </div>
        <p className="max-w-md mx-auto text-[11px] leading-relaxed text-muted-foreground/80">
          Disclaimer: Aarav is an AI digital guide developed for the National Financial Literacy Campaign. The answers provided are for educational purposes. For official banking and scheme actions, please visit your nearest bank branch or the official government scheme portals.
        </p>
        <p className="pt-2 text-[10px] text-muted-foreground/60">
          © 2026 National Financial Literacy Initiative. All Rights Reserved.
        </p>
      </footer>

    </div>
  );
};
