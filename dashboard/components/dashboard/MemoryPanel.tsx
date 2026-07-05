"use client";

import { useMemory } from "@/lib/hooks";
import { Brain, FileCode, AlertTriangle, Bug, GitPullRequest, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export function MemoryPanel() {
  const { data: memoryItems, error } = useMemory();

  if (error) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
        <AlertTriangle className="h-5 w-5" />
        <span className="text-sm font-medium">Failed to load Team Memory</span>
      </div>
    );
  }

  if (!memoryItems || memoryItems.length === 0) {
    return (
      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-white/10 text-sm text-gray-500">
        No team memory found.
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-white/10 bg-surface/50 p-6 shadow-2xl backdrop-blur-xl">
      {/* Background glow for premium feel */}
      <div className="pointer-events-none absolute -inset-px rounded-xl border border-white/5 bg-gradient-to-br from-[#8b5cf6]/10 via-transparent to-transparent opacity-50" />
      
      <div className="relative mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8b5cf6]/20 shadow-[0_0_15px_rgba(139,92,246,0.3)]">
            <Brain className="h-5 w-5 text-[#8b5cf6]" />
          </div>
          <div>
            <h2 className="text-lg font-bold tracking-tight text-white drop-shadow-md">
              Cognee Team Memory
            </h2>
            <p className="text-xs text-gray-400">Context recalled from past reviews & incidents</p>
          </div>
        </div>
        <span className="inline-flex items-center rounded-full border border-[#8b5cf6]/30 bg-[#8b5cf6]/10 px-3 py-1.5 text-xs font-semibold tracking-wide text-[#8b5cf6] shadow-[0_0_10px_rgba(139,92,246,0.2)]">
          {memoryItems.length} Lessons Active
        </span>
      </div>

      <div className="relative space-y-4">
        {memoryItems.map((item, idx) => (
          <div
            key={item.id || idx}
            className="group relative flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-[#8b5cf6]/50 hover:bg-white/[0.04] hover:shadow-[0_8px_30px_rgba(139,92,246,0.12)]"
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-white drop-shadow-sm group-hover:text-[#a78bfa] transition-colors">
                    {item.rule}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span className="inline-flex items-center gap-1.5 rounded bg-white/5 px-2 py-1 transition-colors group-hover:bg-white/10 group-hover:text-gray-300">
                    <FileCode className="h-3.5 w-3.5 text-blue-400" />
                    {item.file}
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    {item.source === "post_merge_bug" ? (
                      <Bug className="h-3.5 w-3.5 text-red-400" />
                    ) : (
                      <GitPullRequest className="h-3.5 w-3.5 text-green-400" />
                    )}
                    <span className="capitalize">{item.source.replace(/_/g, " ")}</span>
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="font-mono text-[10px] uppercase text-gray-500 border border-gray-700 bg-gray-800/50 px-1.5 py-0.5 rounded">
                      {item.commit.substring(0, 7)}
                    </span>
                  </span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <div className="flex items-center gap-2">
                  {item.severity === "critical" && (
                    <span className="flex items-center gap-1 rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-400 shadow-[0_0_8px_rgba(239,68,68,0.2)]">
                      <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
                      Critical
                    </span>
                  )}
                </div>
                <span className="flex items-center gap-1 text-[10px] text-gray-500">
                  <Clock className="h-3 w-3" />
                  {item.ts ? formatDistanceToNow(new Date(item.ts), { addSuffix: true }) : "recently"}
                </span>
              </div>
            </div>
            <p className="mt-1 text-sm leading-relaxed text-gray-300 group-hover:text-gray-200 transition-colors">
              {item.comment}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
