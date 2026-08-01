import { cn } from "../../lib/utils";
import { Button } from "./button";
import { RocketIcon, ArrowRightIcon, PhoneCallIcon } from "lucide-react";
import { LogoCloud } from "./logo-cloud-3";
import { Link } from "react-router-dom";

export function HeroSection() {
  return (
    <section className="relative mx-auto w-full max-w-5xl">
      <div
        aria-hidden="true"
        className="absolute inset-0 isolate hidden overflow-hidden contain-strict lg:block"
      >
        <div className="absolute inset-0 -top-14 isolate -z-10 bg-[radial-gradient(35%_80%_at_49%_0%,rgba(241,245,249,0.08),transparent)] contain-strict" />
      </div>

      <div
        aria-hidden="true"
        className="absolute inset-0 mx-auto hidden min-h-screen w-full max-w-5xl lg:block"
      >
        <div className="mask-y-fade absolute inset-y-0 left-0 z-10 h-full w-px bg-foreground/15" />
        <div className="mask-y-fade absolute inset-y-0 right-0 z-10 h-full w-px bg-foreground/15" />
      </div>

      <div className="relative flex flex-col items-center justify-center gap-5 pb-24 pt-28">
        <div aria-hidden="true" className="absolute inset-0 -z-10 size-full overflow-hidden">
          <div className="absolute inset-y-0 left-4 w-px bg-gradient-to-b from-transparent via-border to-border md:left-8" />
          <div className="absolute inset-y-0 right-4 w-px bg-gradient-to-b from-transparent via-border to-border md:right-8" />
          <div className="absolute inset-y-0 left-8 w-px bg-gradient-to-b from-transparent via-border/50 to-border/50 md:left-12" />
          <div className="absolute inset-y-0 right-8 w-px bg-gradient-to-b from-transparent via-border/50 to-border/50 md:right-12" />
        </div>

        <Link
          className={cn(
            "group mx-auto flex w-fit items-center gap-3 rounded-full border bg-card px-3 py-1 shadow",
            "fade-in slide-in-from-bottom-10 animate-in fill-mode-backwards transition-all delay-500 duration-500 ease-out"
          )}
          to="/dashboard"
        >
          <RocketIcon className="size-3 text-muted-foreground" />
          <span className="text-xs">New evaluator insights are live</span>
          <span className="block h-5 border-l" />
          <ArrowRightIcon className="size-3 duration-150 ease-out group-hover:translate-x-1" />
        </Link>

        <h1
          className={cn(
            "fade-in slide-in-from-bottom-10 animate-in text-balance text-center text-4xl tracking-tight fill-mode-backwards delay-100 duration-500 ease-out md:text-5xl lg:text-6xl",
            "drop-shadow-[0_0_35px_rgba(241,245,249,0.25)]"
          )}
        >
          AI-Powered Answer Evaluation
          <br />
          Built for Fast, Fair Grading
        </h1>

        <p className="fade-in slide-in-from-bottom-10 mx-auto max-w-md animate-in fill-mode-backwards text-center text-base tracking-wider text-foreground/80 delay-200 duration-500 ease-out sm:text-lg md:text-xl">
          Streamline your workflow with smart scoring, clear feedback, and
          consistent results across every student submission.
        </p>

        <div className="fade-in slide-in-from-bottom-10 flex animate-in flex-row flex-wrap items-center justify-center gap-3 fill-mode-backwards pt-2 delay-300 duration-500 ease-out">
          <Button className="rounded-full" size="lg" variant="secondary" asChild>
            <Link to="/evaluate">
              <PhoneCallIcon data-icon="inline-start" className="mr-2 size-4" />
              Start Evaluating
            </Link>
          </Button>
          <Button className="rounded-full" size="lg" asChild>
            <Link to="/dashboard">
              View Dashboard
              <ArrowRightIcon className="ms-2 size-4" data-icon="inline-end" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

export function LogosSection() {
  return (
    <section className="relative space-y-4 border-t pb-10 pt-6">
      <h2 className="text-center text-lg font-medium tracking-tight text-muted-foreground md:text-xl">
        Trusted by <span className="text-foreground">educators</span> worldwide
      </h2>
      <div className="relative z-10 mx-auto max-w-4xl">
        <LogoCloud logos={logos} />
      </div>
    </section>
  );
}

const logos = [
  {
    src: "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=120&q=80",
    alt: "Collaborative team",
  },
  {
    src: "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=120&q=80",
    alt: "Workspace",
  },
  {
    src: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=120&q=80",
    alt: "Mentoring",
  },
  {
    src: "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=120&q=80",
    alt: "Team discussion",
  },
  {
    src: "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=120&q=80",
    alt: "Planning session",
  },
  {
    src: "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=120&q=80",
    alt: "Presentation",
  },
  {
    src: "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=120&q=80",
    alt: "Code review",
  },
  {
    src: "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=120&q=80",
    alt: "Innovation",
  },
];
