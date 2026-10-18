import { DemoConsole } from "@/components/demo-console";
import { SiteHeader } from "@/components/site-header";

/**
 * The live demo.
 *
 * A separate route rather than a landing section, because the landing page is
 * a product page and the demo is the product working. Judges open this
 * directly from the nav — so it carries the same header, sliced from the same
 * source file, rather than a second copy that can drift.
 */
export default function DemoPage() {
  return (
    <>
      <SiteHeader />
      <div className="helio-route">
        <p className="helio-kicker">Live — connected to the deployed agent</p>
        <h1 className="helio-title">Ask the company graph</h1>
        <p className="helio-lede">
          This is the real agent on{" "}
          <code>helio-brain.onrender.com</code>, not a recording. Every answer is
          a live graph traversal, and every node in the trail is a row the
          backend actually returned.
        </p>

        <div className="helio-console">
          <DemoConsole />
        </div>
      </div>
    </>
  );
}