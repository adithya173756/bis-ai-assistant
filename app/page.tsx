"use client";

import { FormEvent, useState } from "react";

type Mode =
  | "ask"
  | "standard"
  | "certification"
  | "laboratory"
  | "hallmarking";

type Source = {
  standard?: string;
  clause?: string;
  page?: string | number;
  source?: string;
  document_type?: string;
  text?: string;
  content?: string;
};

type ApiResponse = {
  answer?: string;
  response?: string;
  sources?: Source[];
  retrieved_chunks?: Source[];
  chunks?: Source[];
  message?: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const quickQuestions = [
  "What is the BIS certification process?",
  "Where can I find BIS recognized laboratories?",
  "What are the requirements for hallmarking?",
  "What products require compulsory BIS certification?",
];

const modeConfig = {
  standard: {
    title: "Find a Standard",
    description:
      "Describe your product or application and identify relevant Indian Standards from the BIS knowledge base.",
    placeholder:
      "Example: Reinforced concrete structures used in building construction",
  },
  certification: {
    title: "Certification Guide",
    description:
      "Understand BIS certification pathways, requirements and related guidance using retrieved BIS information.",
    placeholder:
      "Example: How can I get BIS certification for my product?",
  },
  laboratory: {
    title: "Testing Laboratories",
    description:
      "Find BIS laboratory and testing information relevant to your query.",
    placeholder:
      "Example: Where can I find BIS recognized laboratories?",
  },
  hallmarking: {
    title: "Hallmarking",
    description:
      "Get evidence-backed information about BIS hallmarking requirements and processes.",
    placeholder:
      "Example: What are the requirements for gold hallmarking?",
  },
};

export default function Home() {
  const [mode, setMode] = useState<Mode>("ask");
  const [question, setQuestion] = useState("");
  const [product, setProduct] = useState("");
  const [industry, setIndustry] = useState("");
  const [informationType, setInformationType] = useState("all");

  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  async function copyAnswer() {
  if (!answer) return;

  try {
    await navigator.clipboard.writeText(answer);
    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);
  } catch (err) {
    console.error("Failed to copy answer:", err);
  }
}

  async function askQuestion(text: string) {
    const cleanQuestion = text.trim();

    if (!cleanQuestion || loading) return;

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: cleanQuestion,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: ApiResponse = await response.json();

      const generatedAnswer =
        data.answer ||
        data.response ||
        data.message ||
        "No answer was returned.";

      const retrievedSources =
        data.sources ||
        data.retrieved_chunks ||
        data.chunks ||
        [];

      setAnswer(generatedAnswer);
      setSources(Array.isArray(retrievedSources) ? retrievedSources : []);

      setTimeout(() => {
        document
          .getElementById("results")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the BIS AI service. Make sure the FastAPI backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  function submitAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    askQuestion(question);
  }

  function buildStandardQuery() {
    if (!product.trim()) return;

    let query = `
Find the applicable Indian Standard(s) for this product or application.

Product / Application:
${product.trim()}

Industry / Sector:
${industry.trim() || "Not specified"}

Information requested:
${
  informationType === "all"
    ? "All relevant information"
    : informationType
}

Please provide:
1. The most relevant Indian Standard(s), if supported by the BIS knowledge base.
2. Why the standard applies to the described product or application.
3. Relevant BIS certification information, if available.
4. Relevant testing or laboratory information, if available.
5. Source, clause and page references where available.

Use only the retrieved BIS knowledge base.
Do not invent standards, clauses, pages or requirements.
`.trim();

    askQuestion(query);
  }

  function selectService(nextMode: Mode) {
    setMode(nextMode);
    setAnswer("");
    setSources([]);
    setError("");

    setTimeout(() => {
      document
        .getElementById("workspace")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 50);
  }

  function clearAll() {
    setQuestion("");
    setProduct("");
    setIndustry("");
    setInformationType("all");
    setAnswer("");
    setSources([]);
    setError("");
    setCopied(false);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* NAVBAR */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <button
            type="button"
            onClick={() => {
              setMode("ask");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-lg font-black shadow-lg shadow-blue-600/20">
              BIS
            </div>

            <div className="text-left">
              <div className="text-sm font-bold tracking-wide">
                BIS AI Assistant
              </div>
              <div className="text-xs text-slate-400">
                Indian Standards & BIS Services
              </div>
            </div>
          </button>

          <nav className="hidden items-center gap-7 text-sm text-slate-300 md:flex">
            <a href="#ask" className="transition hover:text-white">
              Ask BIS
            </a>
            <a href="#services" className="transition hover:text-white">
              Services
            </a>
            <a href="#how-it-works" className="transition hover:text-white">
              How it works
            </a>
            <a
              href="https://www.bis.gov.in/"
              target="_blank"
              rel="noreferrer"
              className="transition hover:text-white"
            >
              Official BIS ↗
            </a>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(37,99,235,0.18),transparent_38%),radial-gradient(circle_at_bottom_left,rgba(14,165,233,0.10),transparent_32%)]" />

        <div className="relative mx-auto max-w-7xl px-5 pb-20 pt-20 lg:px-8 lg:pb-28 lg:pt-28">
          <div className="max-w-4xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-500/10 px-4 py-2 text-xs font-semibold text-blue-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              AI-powered BIS knowledge assistant
            </div>

            <h1 className="max-w-4xl text-5xl font-black leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
              Understand BIS.
              <br />
              <span className="text-blue-400">Find the right path.</span>
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
              Find Indian Standards, understand BIS certification, discover
              testing information and get evidence-backed answers from the BIS
              knowledge base.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => selectService("standard")}
                className="rounded-xl bg-blue-600 px-6 py-3.5 font-bold shadow-xl shadow-blue-600/20 transition hover:bg-blue-500"
              >
                Find a Standard
              </button>

              <button
                type="button"
                onClick={() => selectService("ask")}
                className="rounded-xl border border-white/15 bg-white/5 px-6 py-3.5 font-bold transition hover:bg-white/10"
              >
                Ask BIS
              </button>
            </div>
          </div>

          <div className="mt-14 grid max-w-5xl grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              ["01", "Standards", "Find relevant Indian Standards"],
              ["02", "Certification", "Understand BIS pathways"],
              ["03", "Testing", "Explore laboratory information"],
              ["04", "Evidence", "See source-backed answers"],
            ].map(([number, title, text]) => (
              <div
                key={number}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5"
              >
                <div className="text-xs font-bold text-blue-400">{number}</div>
                <div className="mt-3 font-bold">{title}</div>
                <div className="mt-1 text-sm leading-6 text-slate-400">
                  {text}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ASK BIS */}
      <section id="ask" className="border-b border-white/10">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="mb-8">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
              Ask BIS
            </p>
            <h2 className="mt-3 text-3xl font-black sm:text-4xl">
              What do you need to know?
            </h2>
            <p className="mt-3 max-w-2xl text-slate-400">
              Ask a question in natural language. The assistant retrieves
              relevant BIS information before generating the response.
            </p>
          </div>

          <form onSubmit={submitAsk}>
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-3 shadow-2xl shadow-black/20">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Example: What is the BIS certification process?"
                rows={4}
                className="w-full resize-none rounded-2xl bg-transparent px-4 py-3 text-lg outline-none placeholder:text-slate-600"
              />

              <div className="flex flex-col gap-3 border-t border-white/10 p-2 pt-3 sm:flex-row sm:items-center sm:justify-between">
                <span className="px-3 text-xs text-slate-500">
                  Answers are generated from retrieved BIS knowledge.
                </span>

                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="rounded-xl bg-blue-600 px-6 py-3 font-bold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? "Searching BIS..." : "Ask BIS →"}
                </button>
              </div>
            </div>
          </form>

          <div className="mt-5 flex flex-wrap gap-2">
            {quickQuestions.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setQuestion(item);
                  askQuestion(item);
                }}
                disabled={loading}
                className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition hover:border-blue-400/30 hover:bg-blue-500/10 hover:text-white disabled:opacity-40"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* SERVICES */}
      <section id="services" className="border-b border-white/10">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="mb-10">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
              BIS Services
            </p>

            <h2 className="mt-3 text-3xl font-black sm:text-4xl">
              One assistant. Multiple BIS workflows.
            </h2>
          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            <ServiceCard
              icon="⌕"
              title="Find a Standard"
              text="Describe your product and discover relevant Indian Standards."
              onClick={() => selectService("standard")}
            />

            <ServiceCard
              icon="✓"
              title="Certification Guide"
              text="Understand certification processes and requirements."
              onClick={() => selectService("certification")}
            />

            <ServiceCard
              icon="⌁"
              title="Testing Laboratories"
              text="Find relevant BIS testing and laboratory information."
              onClick={() => selectService("laboratory")}
            />

            <ServiceCard
              icon="◇"
              title="Hallmarking"
              text="Get guidance about BIS hallmarking information."
              onClick={() => selectService("hallmarking")}
            />
          </div>
        </div>
      </section>

      {/* WORKSPACE */}
      <section id="workspace" className="border-b border-white/10">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="mb-10">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
              Assistant Workspace
            </p>

            <h2 className="mt-3 text-3xl font-black sm:text-4xl">
              {mode === "ask"
                ? "Ask BIS"
                : modeConfig[mode as keyof typeof modeConfig]?.title}
            </h2>

            <p className="mt-3 max-w-3xl text-slate-400">
              {mode === "ask"
                ? "Ask any supported BIS question and receive an evidence-backed response."
                : modeConfig[mode as keyof typeof modeConfig]?.description}
            </p>
          </div>

          {/* STANDARD FINDER */}
          {mode === "standard" && (
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:p-8">
              <div className="grid gap-6 lg:grid-cols-2">
                <Field
                  label="Product / Application"
                  value={product}
                  onChange={setProduct}
                  placeholder={modeConfig.standard.placeholder}
                />

                <Field
                  label="Industry / Sector"
                  value={industry}
                  onChange={setIndustry}
                  placeholder="Example: Construction"
                />
              </div>

              <div className="mt-6">
                <label className="mb-2 block text-sm font-semibold text-slate-300">
                  Information requested
                </label>

                <select
                  value={informationType}
                  onChange={(e) => setInformationType(e.target.value)}
                  className="w-full rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-blue-500"
                >
                  <option value="all">All relevant information</option>
                  <option value="standard">
                    Applicable Indian Standard
                  </option>
                  <option value="certification">
                    BIS certification information
                  </option>
                  <option value="testing">Testing information</option>
                </select>
              </div>

              <div className="mt-7 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={buildStandardQuery}
                  disabled={loading || !product.trim()}
                  className="rounded-xl bg-blue-600 px-6 py-3 font-bold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? "Finding..." : "Find Standards →"}
                </button>

                <button
                  type="button"
                  onClick={clearAll}
                  className="rounded-xl border border-white/10 bg-white/5 px-6 py-3 font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
                >
                  Clear
                </button>
              </div>
            </div>
          )}

          {/* OTHER SERVICES */}
          {mode !== "ask" && mode !== "standard" && (
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:p-8">
              <div className="flex flex-col gap-5 sm:flex-row">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={
                    modeConfig[mode as keyof typeof modeConfig]?.placeholder
                  }
                  rows={4}
                  className="min-h-[130px] flex-1 resize-none rounded-2xl border border-white/10 bg-slate-900 p-4 text-base outline-none placeholder:text-slate-600 focus:border-blue-500"
                />

                <button
                  type="button"
                  onClick={() => askQuestion(question)}
                  disabled={loading || !question.trim()}
                  className="rounded-xl bg-blue-600 px-7 py-3 font-bold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40 sm:self-end"
                >
                  {loading ? "Searching..." : "Get Guidance →"}
                </button>
              </div>
            </div>
          )}

          {/* ASK MODE */}
          {mode === "ask" && (
            <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:p-8">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a BIS question..."
                rows={4}
                className="w-full resize-none rounded-2xl border border-white/10 bg-slate-900 p-4 text-base outline-none placeholder:text-slate-600 focus:border-blue-500"
              />

              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={() => askQuestion(question)}
                  disabled={loading || !question.trim()}
                  className="rounded-xl bg-blue-600 px-7 py-3 font-bold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {loading ? "Searching BIS..." : "Ask BIS →"}
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* RESULTS */}
      {(loading || answer || error || sources.length > 0) && (
        <section id="results" className="border-b border-white/10">
          <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
            <div className="mb-8 flex items-end justify-between gap-5">
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
                  Evidence
                </p>

                <h2 className="mt-3 text-3xl font-black">
                  BIS-grounded response
                </h2>
              </div>

              {!loading && (
                <button
                  type="button"
                  onClick={clearAll}
                  className="text-sm text-slate-500 transition hover:text-white"
                >
                  Clear result
                </button>
              )}
            </div>

            {loading && (
              <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-8">
                <div className="flex items-center gap-4">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />

                  <div>
                    <div className="font-semibold">
                      Retrieving relevant BIS evidence...
                    </div>
                    <div className="mt-1 text-sm text-slate-500">
                      Searching the knowledge base and generating a grounded
                      response.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="rounded-2xl border border-red-400/20 bg-red-500/10 p-5 text-red-300">
                {error}
              </div>
            )}

            {!loading && answer && (
              <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
                {/* ANSWER */}
                <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:p-8">
                  <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
  <div className="flex items-center gap-3">
    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/15 text-blue-400">
      AI
    </div>

    <div>
      <div className="font-bold">BIS AI Explanation</div>

      <div className="text-xs text-slate-500">
        Generated from retrieved BIS context
      </div>
    </div>
  </div>

  <button
    type="button"
    onClick={copyAnswer}
    className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/10 hover:text-white"
  >
    {copied ? "✓ Copied" : "Copy Answer"}
  </button>
</div>

                  <div className="whitespace-pre-wrap text-[15px] leading-8 text-slate-200">
                    {answer}
                  </div>
                  <div className="mt-8 border-t border-white/10 pt-6">
  <button
    type="button"
    onClick={() => {
      setQuestion("");
      setProduct("");
      setIndustry("");
      setInformationType("all");
      setAnswer("");
      setSources([]);
      setError("");

      document
        .getElementById("ask")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }}
    className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold transition hover:bg-blue-500"
  >
    Ask Another Question →
  </button>
</div>
                </div>

                {/* SOURCES */}
                <div className="space-y-4">
                  <div className="rounded-3xl border border-blue-400/15 bg-blue-500/[0.06] p-6">
                    <div className="mb-2 text-sm font-bold text-blue-300">
                      Relevant BIS Evidence
                    </div>

                    <p className="text-sm leading-6 text-slate-400">
                      The following information was retrieved from the BIS
                      knowledge base for this answer.
                    </p>
                  </div>

                  {sources.length > 0 ? (
                    sources.map((source, index) => (
                      <EvidenceCard
                        key={`${source.standard || "source"}-${index}`}
                        source={source}
                        index={index}
                      />
                    ))
                  ) : (
                    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 text-sm leading-6 text-slate-500">
                      The backend returned an answer, but no structured source
                      metadata was returned with this response.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="border-b border-white/10">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
              How it works
            </p>

            <h2 className="mt-3 text-3xl font-black sm:text-4xl">
              From BIS documents to trustworthy answers.
            </h2>

            <p className="mt-4 leading-7 text-slate-400">
              The assistant does not simply ask an AI model to answer from
              memory. It first retrieves relevant information from the BIS
              knowledge base and then asks the model to explain that evidence.
            </p>
          </div>

          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            <ProcessCard
              number="01"
              title="BIS Sources"
              text="Official BIS documents and service information form the knowledge base."
            />

            <ProcessCard
              number="02"
              title="Retrieve"
              text="Relevant pieces of information are searched for the user's question."
            />

            <ProcessCard
              number="03"
              title="Explain"
              text="Gemini explains the retrieved evidence without inventing missing information."
            />

            <ProcessCard
              number="04"
              title="Show Evidence"
              text="The interface presents available standard, clause, page and source information."
            />
          </div>
        </div>
      </section>

      {/* TRUST */}
      <section>
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-blue-500/10 to-transparent p-8 lg:p-12">
            <div className="max-w-3xl">
              <div className="text-sm font-bold uppercase tracking-[0.2em] text-blue-400">
                Built for PS 26107
              </div>

              <h2 className="mt-4 text-3xl font-black sm:text-4xl">
                BIS information, made easier to understand.
              </h2>

              <p className="mt-5 leading-8 text-slate-400">
                A unified AI-powered assistant for industries, manufacturers
                and consumers looking for Indian Standards, certification,
                testing and hallmarking information.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <a
                  href="https://www.bis.gov.in/"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-xl bg-white px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-slate-200"
                >
                  Visit Official BIS ↗
                </a>

                <button
                  type="button"
                  onClick={() => selectService("standard")}
                  className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold transition hover:bg-white/10"
                >
                  Find a Standard
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div>
            <span className="font-semibold text-slate-300">
              BIS AI Assistant
            </span>{" "}
            · SIH 2026
          </div>

          <div className="flex gap-5">
            <a
              href="https://www.bis.gov.in/"
              target="_blank"
              rel="noreferrer"
              className="transition hover:text-white"
            >
              Official BIS
            </a>

            <span>Evidence-backed AI</span>
          </div>
        </div>
      </footer>
    </main>
  );
}

/* ---------------- COMPONENTS ---------------- */

function ServiceCard({
  icon,
  title,
  text,
  onClick,
}: {
  icon: string;
  title: string;
  text: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group rounded-3xl border border-white/10 bg-white/[0.04] p-6 text-left transition hover:-translate-y-1 hover:border-blue-400/30 hover:bg-blue-500/[0.06]"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 text-xl text-blue-400">
        {icon}
      </div>

      <h3 className="mt-6 text-lg font-bold">{title}</h3>

      <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>

      <div className="mt-5 text-sm font-semibold text-blue-400 transition group-hover:translate-x-1">
        Open service →
      </div>
    </button>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm font-semibold text-slate-300">
        {label}
      </label>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        className="w-full resize-none rounded-2xl border border-white/10 bg-slate-900 p-4 text-base outline-none placeholder:text-slate-600 focus:border-blue-500"
      />
    </div>
  );
}

function EvidenceCard({
  source,
  index,
}: {
  source: Source;
  index: number;
}) {
  const standard =
    source.standard ||
    "BIS Document";

  const clause =
    source.clause ||
    "Not identified";

  const page =
    source.page !== undefined && source.page !== null
      ? String(source.page)
      : "Not available";

  const content =
    source.text ||
    source.content ||
    "";

  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
      <div className="mb-5 flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-[0.15em] text-slate-500">
          Evidence {index + 1}
        </span>

        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
          Retrieved
        </span>
      </div>

      <div className="space-y-4">
        <EvidenceMeta label="Standard" value={standard} />
        <EvidenceMeta label="Clause" value={clause} />
        <EvidenceMeta label="Page" value={page} />
      </div>

      {content && (
        <div className="mt-6 border-t border-white/10 pt-5">
          <div className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
            Relevant chunk
          </div>

          <p className="whitespace-pre-wrap text-sm leading-7 text-slate-300">
            {content}
          </p>
        </div>
      )}

      {source.source && (
        <div className="mt-5 border-t border-white/10 pt-5">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Source
          </div>

          {source.source.startsWith("http") ? (
            <a
              href={source.source}
              target="_blank"
              rel="noreferrer"
              className="mt-2 block break-all text-sm text-blue-400 hover:text-blue-300"
            >
              Official BIS source ↗
            </a>
          ) : (
            <p className="mt-2 break-words text-sm text-slate-400">
              {source.source}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function EvidenceMeta({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
        {label}
      </div>

      <div className="mt-1 font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function ProcessCard({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
      <div className="text-sm font-black text-blue-400">{number}</div>

      <h3 className="mt-5 font-bold">{title}</h3>

      <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
    </div>
  );
}