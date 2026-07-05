"use client";

import { useMemory } from "@/lib/hooks";
import { Brain, FileCode, CheckCircle, AlertTriangle } from "lucide-react";
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
    <div className="rounded-xl border border-line bg-surface p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-[#8b5cf6]" />
          <h2 className="text-base font-semibold tracking-tight text-text">
            Cognee Team Memory
          </h2>
        </div>
        <span className="inline-flex items-center rounded-full bg-[#8b5cf6]/10 px-2 py-1 text-xs font-medium text-[#8b5cf6]">
          {memoryItems.length} Lessons Active
        </span>
      </div>

      <div className="space-y-4">
        {memoryItems.map((item, idx) => (
          <div
            key={item.id || idx}
            className="flex flex-col gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-4 transition-colors hover:bg-white/[0.04]"
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-text">
                  {item.rule}
                </span>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="inline-flex items-center gap-1">
                    <FileCode className="h-3 w-3" />
                    {item.file}
                  </span>
                  <span>&bull;</span>
                  <span className="font-mono text-[10px]">{item.commit.substring(0, 7)}</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                {item.severity === "critical" && (
                  <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[10px] font-bold uppercase text-red-400">
                    Critical
                  </span>
                )}
              </div>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-gray-400">
              {item.comment}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
