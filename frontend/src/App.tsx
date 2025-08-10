import React from "react";
import QueryBox from "./components/views/QueryBox";
import Upload from "./components/views/Upload";
import QueryResultsTable from "./components/views/QueryResultsTable";
import DashboardView from "./components/views/DashboardView";

type View = "dashboard" | "upload" | "query";

export default function App() {
  const [view, setView] = React.useState<View>(getInitialView());
  const [results, setResults] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false); // NEW

  // Sync with URL hash
  React.useEffect(() => {
    const onHashChange = () => {
      const next = readHashView();
      if (next !== view) setView(next);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [view]);

  React.useEffect(() => {
    updateHash(view);
  }, [view]);

  return (
    <div className="container space-y-6 py-8">
      <Header />

      {/* Navigation */}
      <nav className="flex gap-2">
        <TabButton
          active={view === "dashboard"}
          onClick={() => setView("dashboard")}
        >
          Dashboard
        </TabButton>
        <TabButton active={view === "upload"} onClick={() => setView("upload")}>
          Upload
        </TabButton>
        <TabButton active={view === "query"} onClick={() => setView("query")}>
          Query
        </TabButton>
      </nav>

      {/* Views */}
      {view === "dashboard" && (
        <section className="space-y-6">
          <DashboardView />
        </section>
      )}

      {view === "upload" && (
        <section className="space-y-6">
          <Upload onUploaded={() => {}} />
        </section>
      )}

      {view === "query" && (
        <section className="space-y-6">
          <QueryBox
            onResults={setResults}
            onLoadingChange={setLoading} // NEW
          />
          <QueryResultsTable rows={results} loading={loading} /> {/* NEW */}
        </section>
      )}

      <footer className="text-xs text-gray-500 pt-6">© Doc Analyzer</footer>
    </div>
  );
}

function Header() {
  return (
    <header className="space-y-1">
      <h1 className="text-2xl font-bold">Doc Analyzer</h1>
      <p className="text-gray-600">
        Analyze and query legal documents using AI.
      </p>
    </header>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        "px-4 py-2 rounded-md border text-sm " +
        (active
          ? "bg-blue-600 text-white border-blue-600"
          : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50")
      }
      aria-current={active ? "page" : undefined}
    >
      {children}
    </button>
  );
}

/** Hash navigation helpers */
function getInitialView(): View {
  return readHashView() || "dashboard";
}

function readHashView(): View {
  const h = (window.location.hash || "").replace(/^#/, "").toLowerCase();
  if (h === "upload") return "upload";
  if (h === "query") return "query";
  return "dashboard";
}

function updateHash(v: View) {
  if (readHashView() !== v) {
    window.location.hash = v;
  }
}
