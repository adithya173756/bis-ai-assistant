"use client";

import { FormEvent, useState } from "react";

type Source = {
  standard?: string;
  clause?: string;
  page?: string;
  source?: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
};

const cleanAnswer = (text: string) => {
  return text
    .replace(/\\n/g, "\n")
    .replace(/###\s*/g, "")
    .replace(/##\s*/g, "")
    .replace(/#\s*/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(
      /\*?\s*\(Standard:\s*.*?Clause:\s*.*?Page:\s*.*?\)\*?/gi,
      ""
    )
    .replace(
      /^\s*Reference Details:\s*$/gim,
      ""
    )
    .replace(
      /^\s*\*?\s*Standard:\s*.*$/gim,
      ""
    )
    .replace(
      /^\s*\*?\s*Clause:\s*.*$/gim,
      ""
    )
    .replace(
      /^\s*\*?\s*Page:\s*.*$/gim,
      ""
    )
    .replace(
      /^\s*\*\s+/gm,
      "• "
    )
    .replace(/\n{3,}/g, "\n\n")
    .trim();
};

const formatAnswer = (text: string) => {
  const cleaned = cleanAnswer(text);

  return cleaned.split("\n").map((line, index) => {
    const trimmed = line.trim();

    if (!trimmed) {
      return <div key={index} className="h-3" />;
    }

    if (/^\d+\.\s/.test(trimmed)) {
      return (
        <div key={index} className="mb-3">
          <span className="font-semibold">
            {trimmed}
          </span>
        </div>
      );
    }

    if (/^[-•]\s/.test(trimmed)) {
      return (
        <div
          key={index}
          className="mb-2 flex gap-2"
        >
          <span>•</span>
          <span>
            {trimmed.replace(/^[-•]\s*/, "")}
          </span>
        </div>
      );
    }

    return (
      <p key={index} className="mb-3">
        {trimmed}
      </p>
    );
  });
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const suggestions = [
    "What is the BIS certification process?",
    "Where can I find BIS recognized laboratories?",
    "What are the requirements for hallmarking?",
    "What products require compulsory BIS certification?",
  ];

  async function askQuestion(
    text: string
  ) {
    if (!text.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: text.trim(),
    };

    setMessages((prev) => [
      ...prev,
      userMessage,
    ]);

    setQuestion("");
    setLoading(true);

    try {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/ask`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: text.trim(),
      }),
    }
  );

      if (!response.ok) {
        throw new Error(
          "Request failed"
        );
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content:
          data.answer ||
          "I could not generate an answer.",
        sources: data.sources || [],
      };

      setMessages((prev) => [
        ...prev,
        assistantMessage,
      ]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Sorry, I could not connect to the BIS AI Assistant backend. Please make sure the FastAPI server is running.",
      };

      setMessages((prev) => [
        ...prev,
        errorMessage,
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    await askQuestion(question);
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">

      {/* Header */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">

          <div>
            <h1 className="text-xl font-bold tracking-tight">
              BIS AI Assistant
            </h1>

            <p className="text-sm text-slate-500">
              Intelligent assistant for Indian Standards & BIS Services
            </p>
          </div>

          <nav className="hidden gap-6 text-sm font-medium md:flex">
            <a
              href="#ask"
              className="hover:text-slate-600"
            >
              Ask BIS
            </a>

            <a
              href="#standards"
              className="hover:text-slate-600"
            >
              Standards
            </a>

            <a
              href="#about"
              className="hover:text-slate-600"
            >
              About
            </a>
          </nav>

        </div>
      </header>

      {/* Hero */}
      <section
        id="ask"
        className="mx-auto max-w-6xl px-6 pb-10 pt-16"
      >
        <div className="max-w-3xl">

          <div className="mb-4 inline-flex rounded-full border bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
            AI-powered BIS knowledge assistant
          </div>

          <h2 className="text-4xl font-bold tracking-tight md:text-5xl">
            Ask questions about
            <br />
            <span className="text-slate-600">
              Indian Standards & BIS Services
            </span>
          </h2>

          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
            Get understandable, source-grounded answers about BIS
            certification, standards, laboratories, hallmarking and
            conformity assessment.
          </p>

        </div>
      </section>

      {/* Search */}
      <section className="mx-auto max-w-4xl px-6">
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border bg-white p-3 shadow-lg"
        >

          <div className="flex flex-col gap-3 sm:flex-row">

            <input
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder="Ask a question about BIS..."
              className="min-h-14 flex-1 rounded-xl border-0 bg-slate-50 px-5 text-base outline-none ring-0 placeholder:text-slate-400 focus:bg-white"
              disabled={loading}
            />

            <button
              type="submit"
              disabled={
                loading ||
                !question.trim()
              }
              className="min-h-14 rounded-xl bg-slate-900 px-8 font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Thinking..." : "Ask BIS"}
            </button>

          </div>

        </form>

        {/* Suggestions */}
        {messages.length === 0 && (
          <div className="mt-6">

            <p className="mb-3 text-sm font-medium text-slate-500">
              Try asking
            </p>

            <div className="flex flex-wrap gap-2">

              {suggestions.map(
                (suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() =>
                      askQuestion(
                        suggestion
                      )
                    }
                    className="rounded-full border bg-white px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-100"
                  >
                    {suggestion}
                  </button>
                )
              )}

            </div>

          </div>
        )}
      </section>

      {/* Chat */}
      <section className="mx-auto max-w-4xl px-6 pb-20 pt-10">

        {messages.map(
          (message, index) => (
            <div
              key={index}
              className={`mb-6 flex ${
                message.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >

              <div
                className={`max-w-3xl rounded-2xl px-6 py-5 ${
                  message.role === "user"
                    ? "bg-slate-900 text-white"
                    : "border bg-white shadow-sm"
                }`}
              >

                {message.role ===
                "user" ? (
                  <p className="whitespace-pre-wrap">
                    {message.content}
                  </p>
                ) : (
                  <div className="text-[15px] leading-7 text-slate-700">
                    {formatAnswer(
                      message.content
                    )}
                  </div>
                )}

                {/* Sources */}
                {message.role ===
                  "assistant" &&
                  message.sources &&
                  message.sources.length >
                    0 && (
                    <div className="mt-6 border-t pt-5">

                      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
                        Sources
                      </h3>

                      <div className="space-y-3">

                        {message.sources.map(
                          (source, sourceIndex) => (
                            <div
                              key={
                                sourceIndex
                              }
                              className="rounded-xl border bg-slate-50 p-4"
                            >

                              <p className="font-medium text-slate-800">
                                {source.standard ||
                                  "BIS Source"}
                              </p>

                              <div className="mt-1 text-sm text-slate-500">
                                {source.clause &&
                                  source.clause !==
                                    "Not identified" && (
                                    <span>
                                      Clause:{" "}
                                      {
                                        source.clause
                                      }
                                    </span>
                                  )}

                                {source.page && (
                                  <span className="ml-3">
                                    Page:{" "}
                                    {
                                      source.page
                                    }
                                  </span>
                                )}
                              </div>

                              {source.source && (
                                <a
                                  href={
                                    source.source
                                  }
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="mt-2 inline-block text-sm font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900"
                                >
                                  View official BIS source →
                                </a>
                              )}

                            </div>
                          )
                        )}

                      </div>

                    </div>
                  )}

              </div>

            </div>
          )
        )}

        {/* Loading */}
        {loading && (
          <div className="flex justify-start">

            <div className="rounded-2xl border bg-white px-6 py-5 shadow-sm">

              <div className="flex items-center gap-2 text-sm text-slate-500">

                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />

                <span className="ml-2">
                  Searching BIS knowledge base...
                </span>

              </div>

            </div>

          </div>
        )}

      </section>

      {/* Standards */}
      <section
        id="standards"
        className="border-t bg-white"
      >
        <div className="mx-auto max-w-6xl px-6 py-16">

          <h2 className="text-2xl font-bold">
            BIS Knowledge Areas
          </h2>

          <p className="mt-3 max-w-2xl text-slate-600">
            The assistant is designed to help users navigate
            standards, certification and BIS services from
            authoritative sources.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

            {[
              "Indian Standards",
              "Product Certification",
              "Testing Laboratories",
              "Hallmarking",
            ].map((item) => (
              <div
                key={item}
                className="rounded-2xl border bg-slate-50 p-5"
              >
                <p className="font-semibold">
                  {item}
                </p>

                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Ask the assistant for relevant BIS information.
                </p>
              </div>
            ))}

          </div>

        </div>
      </section>

      {/* About */}
      <section
        id="about"
        className="border-t bg-slate-50"
      >
        <div className="mx-auto max-w-6xl px-6 py-14">

          <h2 className="text-2xl font-bold">
            About this prototype
          </h2>

          <p className="mt-3 max-w-3xl leading-7 text-slate-600">
            This prototype uses Retrieval-Augmented Generation (RAG)
            to retrieve relevant BIS information before generating an
            answer. This helps keep responses grounded in the available
            BIS knowledge sources and provides users with references
            to official BIS information.
          </p>

        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">

          <p>
            BIS AI Assistant • SIH 2026 Prototype
          </p>

          <p>
            Source-grounded Indian Standards assistance
          </p>

        </div>
      </footer>

    </main>
  );
}