"use client";

import React, { useEffect, useState } from "react";
import {
  ArrowUpRight,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import {
  getTransactions,
  submitTransaction,
  type Transaction,
} from "./actions";

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [inputText, setInputText] = useState("");
  const [inputAmount, setInputAmount] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(true);

  const syncLedgerState = async () => {
    const data = await getTransactions();
    setTransactions(data);
  };

  useEffect(() => {
    void syncLedgerState();

    if (!isPolling) return;

    const streamPollingTrigger = setInterval(() => {
      void syncLedgerState();
    }, 2000);

    return () => clearInterval(streamPollingTrigger);
  }, [isPolling]);

  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputText || !inputAmount || isSubmitting) return;

    setIsSubmitting(true);

    const payload = {
      user_id: "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      raw_text: inputText,
      amount: Number.parseFloat(inputAmount),
      currency: "USD",
      transaction_timestamp: new Date().toISOString(),
    };

    const result = await submitTransaction(payload);

    if (result.success) {
      setInputText("");
      setInputAmount("");
      await syncLedgerState();
    } else {
      alert(
        "API Node Gateway disconnected. Transaction execution packet dropped.",
      );
    }

    setIsSubmitting(false);
  };

  return (
    <main className="min-h-screen bg-[#FBFBFB] p-8 font-sans text-[#111111] antialiased selection:bg-black selection:text-white md:p-16">
      <header className="mx-auto mb-12 flex max-w-5xl items-center justify-between border-b border-[#E5E5E5] pb-6">
        <div>
          <h1 className="text-lg font-medium tracking-tight uppercase">
            LEDGER.CORE
          </h1>
          <p className="mt-0.5 font-mono text-xs text-[#707070]">
            INTELLIGENT RECONCILIATION GATEWAY
          </p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsPolling((previous) => !previous)}
            className={`rounded border px-2.5 py-1 font-mono text-xs transition-colors ${
              isPolling
                ? "border-black bg-black text-white"
                : "border-[#DCDCDC] bg-transparent text-[#707070]"
            }`}
          >
            {isPolling ? "● LIVE STREAMING" : "○ STREAM PAUSED"}
          </button>
          <div className="flex items-center gap-2 rounded bg-[#F0F0F0] px-3 py-1.5 font-mono text-xs text-[#444444]">
            <ShieldCheck className="h-3.5 w-3.5 text-black" />
            SYSTEM LIVE
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-12 md:grid-cols-3">
        <section className="md:col-span-1">
          <h2 className="mb-6 text-sm font-medium uppercase tracking-wider font-mono text-[#505050]">
            Ingest Feed
          </h2>
          <form onSubmit={handleCreateTransaction} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wider font-mono text-[#707070]">
                Raw Bank Statement Text
              </label>
              <input
                type="text"
                required
                value={inputText}
                onChange={(event) => setInputText(event.target.value)}
                placeholder="e.g. AWS_RECURR_883921_SEATTLE"
                className="w-full rounded border border-[#DCDCDC] bg-white px-3 py-2 font-mono text-sm placeholder:text-[#A0A0A0] transition-colors focus:border-black focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs uppercase tracking-wider font-mono text-[#707070]">
                Amount (USD)
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={inputAmount}
                onChange={(event) => setInputAmount(event.target.value)}
                placeholder="0.00"
                className="w-full rounded border border-[#DCDCDC] bg-white px-3 py-2 font-mono text-sm placeholder:text-[#A0A0A0] transition-colors focus:border-black focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded bg-black py-2 text-xs font-medium uppercase tracking-widest text-white transition-colors hover:bg-[#222222] disabled:bg-[#808080]"
            >
              {isSubmitting ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <>
                  Commit to Bus
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>
        </section>

        <section className="md:col-span-2">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider font-mono text-[#505050]">
              Live Signal Streams
            </h2>
            <button
              onClick={syncLedgerState}
              className="text-[#707070] transition-colors hover:text-black"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="divide-y divide-[#E5E5E5] rounded border border-[#E5E5E5] bg-white">
            {transactions.length === 0 ? (
              <p className="p-8 text-center font-mono text-xs text-[#707070]">
                No active signals running on master ledger logs.
              </p>
            ) : (
              transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-5 transition-colors hover:bg-[#FAFAFA]"
                >
                  <div className="max-w-[75%] space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-medium tracking-tight text-black">
                        {transaction.clean_name || transaction.raw_text}
                      </span>
                      {transaction.clean_name && (
                        <span className="rounded bg-[#F0F0F0] px-2 py-0.5 font-mono text-[9px] uppercase tracking-wider text-[#555555]">
                          {transaction.category}
                        </span>
                      )}
                    </div>
                    {transaction.clean_name && (
                      <p className="truncate font-mono text-xs text-[#707070]">
                        Raw Signature: {transaction.raw_text}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-col items-end space-y-2">
                    <span className="font-mono text-sm font-medium tracking-tight">
                      ${transaction.amount.toFixed(2)}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {transaction.status === "PROCESSED" ? (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5 text-black" />
                          <span className="font-mono text-[10px] uppercase tracking-wider text-black">
                            Cleaned
                          </span>
                        </>
                      ) : transaction.status === "PENDING" ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin text-[#707070]" />
                          <span className="font-mono text-[10px] uppercase tracking-wider text-[#707070]">
                            AI Processing
                          </span>
                        </>
                      ) : (
                        <>
                          <AlertTriangle className="h-3.5 w-3.5 text-red-600" />
                          <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-red-600">
                            Anomaly
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
