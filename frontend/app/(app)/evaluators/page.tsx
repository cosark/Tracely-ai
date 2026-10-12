import { DocLink } from "@/app/components/DocLink";
import { EvaluatorsManager } from "@/app/components/EvaluatorsManager";

export const metadata = { title: "Evaluators · Tracely" };

/** Every evaluator in one place. They are still the columns of the traces table — this is the
 *  same editor, reachable without first finding the "Add Column" button on a grid. */
export default function EvaluatorsPage() {
  return (
    <div className="space-y-6">
      <header className="reveal">
        <div className="flex items-center gap-3">
          <h1 className="font-display text-[26px] font-extrabold tracking-tight">Evaluators</h1>
          <DocLink path="/product/evaluators" />
        </div>
        <p className="mt-1.5 max-w-3xl text-[14px] text-fg-muted">
          The checks that grade every new run — deterministic structural checks and LLM-judge rubrics. Each one is a
          column on the Traces table; a <span className="text-fg">FAIL</span> on a non-advisory evaluator fails the
          run, feeds failure clustering, and can fire an alert.
        </p>
      </header>
      <EvaluatorsManager />
    </div>
  );
}
