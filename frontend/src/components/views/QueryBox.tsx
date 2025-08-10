import React from "react";
import { apiFetch } from "../../lib/api";

type QueryBoxProps = {
  onResults: (rows: any[]) => void;
  onLoadingChange?: (loading: boolean) => void; // NEW
};

const MIN_CHARS = 3;
const DEBOUNCE_MS = 400;

export default function QueryBox({
  onResults,
  onLoadingChange,
}: QueryBoxProps) {
  const [question, setQuestion] = React.useState("");
  const [debouncedQ, setDebouncedQ] = React.useState("");
  const [loading, _setLoading] = React.useState(false);
  const [err, setErr] = React.useState<string>("");
  const [noMatches, setNoMatches] = React.useState(false);

  // keep parent informed about loading changes
  const setLoading = React.useCallback(
    (v: boolean) => {
      _setLoading(v);
      onLoadingChange?.(v);
    },
    [onLoadingChange]
  );

  // Debounce input
  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(question), DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [question]);

  // AbortController to cancel in-flight requests
  const abortRef = React.useRef<AbortController | null>(null);

  async function runQuery(q: string) {
    // cancel any in-flight request
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setErr("");
    setNoMatches(false);

    try {
      const data = await apiFetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
        signal: controller.signal,
      });

      let results: any[] = [];
      if (Array.isArray(data)) results = data;
      else if (data?.ok === false)
        throw new Error(data?.reason || "Query failed");
      else if (Array.isArray(data?.matches)) results = data.matches;

      onResults(results);
      if (results.length === 0) setNoMatches(true);
    } catch (e: any) {
      if (e?.name === "AbortError") return; // ignore cancels
      setErr(e?.message || "Error");
      onResults([]);
    } finally {
      setLoading(false);
    }
  }

  // Auto-search when user types >= MIN_CHARS
  React.useEffect(() => {
    const q = debouncedQ.trim();
    if (q.length >= MIN_CHARS) {
      runQuery(q);
    } else {
      // below threshold: clear state/results and cancel in-flight
      onResults([]);
      setNoMatches(false);
      setErr("");
      abortRef.current?.abort();
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQ]);

  // Cancel in-flight on unmount
  React.useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const canSearch = question.trim().length >= MIN_CHARS;

  return (
    <div className="card space-y-3">
      <h2 className="text-lg font-semibold">Ask a Question</h2>
      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && canSearch && !loading) {
              runQuery(question.trim());
            }
          }}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
          placeholder={`Type at least ${MIN_CHARS} characters...`}
        />
        <button
          className="btn btn-primary"
          onClick={() => runQuery(question.trim())}
          disabled={loading || !canSearch}
          title={!canSearch ? `Enter at least ${MIN_CHARS} characters` : ""}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {!canSearch && question.trim().length > 0 && (
        <div className="text-xs text-gray-500">
          Enter at least {MIN_CHARS} characters to search.
        </div>
      )}

      {err && <div className="text-sm text-red-600">{err}</div>}
      {noMatches && !err && !loading && (
        <div className="text-sm text-gray-500">No matches found.</div>
      )}
    </div>
  );
}
