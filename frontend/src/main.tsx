import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import cytoscape from "cytoscape";
import "./styles.css";

type LocaleCode = "en" | "zh-TW" | "zh-CN" | "ja";
type Catalog = Record<string, string>;
type Claim = { id: string; statement: string; type: string; status: string; authors: string[]; dependencies: string[]; evidence_ids: string[] };
type Evidence = {
  id: string; type: string; title: string; producer: string; scope: string; path?: string; uri?: string; locator?: string; sha256?: string;
  metadata?: { bundle?: { format: string; schema_version: number; profile: string; producer: { name: string; version: string }; provenance?: { commit?: string } | null; result_status?: string | null } };
};
type AuditIssue = { code: string; severity: string; message_id: string; subject_id?: string; details: Record<string, string> };
type ReportData = {
  project: { name: string; root: string };
  claims: Claim[];
  evidence: Evidence[];
  verifications: unknown[];
  audit: { status: "PASS" | "FAIL"; errors: number; warnings: number; issues: AuditIssue[] };
  locales: Record<LocaleCode, Catalog>;
  language: { default: LocaleCode; source: string; supported: boolean };
};
type LoomMode = "all" | "claims" | "gaps";
type SelectedItem = { id: string; kind: "claim" | "evidence"; title: string; meta: string } | null;

const payloadElement = document.getElementById("rigorgraph-data");
if (!payloadElement?.textContent) throw new Error("RigorGraph report data is missing");
const data = JSON.parse(payloadElement.textContent) as ReportData;

const languageNames: Record<LocaleCode, string> = { en: "English", "zh-TW": "繁體中文", "zh-CN": "简体中文", ja: "日本語" };
const gapStatuses = new Set(["DRAFT", "PROPOSED", "UNDER_REVIEW", "UNCERTAIN"]);

function interpolate(template: string, values: Record<string, unknown> = {}) {
  return template.replace(/\{([^}]+)\}/g, (_, key: string) => String(values[key] ?? `{${key}}`));
}

function useTranslator(language: LocaleCode) {
  return (id: string, values: Record<string, unknown> = {}) => interpolate(data.locales[language]?.[id] ?? data.locales.en[id] ?? id, values);
}

function initialLanguage(): LocaleCode {
  const saved = localStorage.getItem("rigorgraph-language") as LocaleCode | null;
  return saved && saved in languageNames ? saved : data.language.default;
}

function EvidenceLoom({ claims, evidence, language }: { claims: Claim[]; evidence: Evidence[]; language: LocaleCode }) {
  const container = useRef<HTMLDivElement>(null);
  const graphRef = useRef<cytoscape.Core | null>(null);
  const [mode, setMode] = useState<LoomMode>("all");
  const [selected, setSelected] = useState<SelectedItem>(null);
  const t = useTranslator(language);

  useEffect(() => {
    if (!container.current || claims.length === 0) return;
    const claimIds = new Set(claims.map((claim) => claim.id));
    const evidenceIds = new Set(evidence.map((item) => item.id));
    const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const graph = cytoscape({
      container: container.current,
      elements: [
        ...claims.map((claim) => ({ group: "nodes" as const, data: { id: `claim:${claim.id}`, label: claim.id, originalId: claim.id, kind: "claim", status: claim.status, title: claim.statement } })),
        ...evidence.map((item) => ({ group: "nodes" as const, data: { id: `evidence:${item.id}`, label: item.id, originalId: item.id, kind: "evidence", status: item.type, title: item.title } })),
        ...claims.flatMap((claim) => claim.dependencies.filter((dependency) => claimIds.has(dependency)).map((dependency) => ({ group: "edges" as const, data: { id: `dep:${dependency}->${claim.id}`, source: `claim:${dependency}`, target: `claim:${claim.id}`, kind: "dependency" } }))),
        ...claims.flatMap((claim) => claim.evidence_ids.filter((id) => evidenceIds.has(id)).map((id) => ({ group: "edges" as const, data: { id: `support:${id}->${claim.id}`, source: `evidence:${id}`, target: `claim:${claim.id}`, kind: "support" } }))),
      ],
      style: [
        { selector: "node", style: { label: "data(label)", "font-family": "ui-monospace, SFMono-Regular, Consolas, monospace", "font-size": 9, color: "#f8f7f2", "text-valign": "center", "text-halign": "center", "text-wrap": "ellipsis", "text-max-width": "72px", width: 70, height: 70, "background-color": "#3458df", "border-width": 1, "border-color": "#91a7ff", "overlay-opacity": 0 } },
        { selector: 'node[kind = "evidence"]', style: { shape: "round-rectangle", width: 84, height: 46, "background-color": "#e85f4f", "border-color": "#ffb0a3" } },
        { selector: 'node[status = "VERIFIED"]', style: { "background-color": "#087c61", "border-color": "#61d4ae" } },
        { selector: 'node[status = "REJECTED"]', style: { "background-color": "#bd3d3d", "border-color": "#ff8e8e" } },
        { selector: 'node[status = "UNCERTAIN"]', style: { "background-color": "#a96509", "border-color": "#f8ca73" } },
        { selector: 'node[status = "REVOKED"]', style: { "background-color": "#565d67", "border-color": "#aab0b9" } },
        { selector: "node:selected", style: { "border-width": 5, "border-color": "#d9ee64", "underlay-color": "#d9ee64", "underlay-opacity": .14, "underlay-padding": 12 } },
        { selector: "edge", style: { width: 1.6, "line-color": "#77808f", "target-arrow-color": "#77808f", "target-arrow-shape": "triangle", "curve-style": "bezier", opacity: .72 } },
        { selector: 'edge[kind = "support"]', style: { "line-style": "dashed", "line-dash-pattern": [5, 5], "line-color": "#e85f4f", "target-arrow-color": "#e85f4f" } },
      ],
      layout: { name: "breadthfirst", directed: true, padding: 34, spacingFactor: 1.35, animate: !reduceMotion, animationDuration: 650 },
    });
    graph.on("tap", "node", (event) => {
      const node = event.target;
      setSelected({ id: node.data("originalId"), kind: node.data("kind"), title: node.data("title"), meta: node.data("status") });
    });
    graph.on("mouseover", "node", (event) => { container.current?.classList.add("is-hovering"); event.target.connectedEdges().animate({ style: { width: 3, opacity: 1 } }, { duration: 180 }); });
    graph.on("mouseout", "node", (event) => { container.current?.classList.remove("is-hovering"); event.target.connectedEdges().animate({ style: { width: 1.6, opacity: .72 } }, { duration: 180 }); });
    graphRef.current = graph;
    return () => { graphRef.current = null; graph.destroy(); };
  }, [claims, evidence]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;
    graph.batch(() => {
      graph.elements().removeClass("is-muted is-hidden");
      if (mode === "claims") {
        graph.nodes('[kind = "evidence"]').addClass("is-hidden");
        graph.edges('[kind = "support"]').addClass("is-hidden");
      }
      if (mode === "gaps") {
        graph.nodes('[kind = "claim"]').forEach((node) => { if (!gapStatuses.has(node.data("status"))) node.addClass("is-muted"); });
        graph.nodes('[kind = "evidence"]').forEach((node) => { const connectedToGap = node.outgoers('node[kind = "claim"]').some((claim) => gapStatuses.has(claim.data("status"))); if (!connectedToGap) node.addClass("is-muted"); });
      }
    });
    graph.style().selector(".is-hidden").style({ display: "none" }).selector(".is-muted").style({ opacity: .12 }).update();
    const visible = graph.elements().filter((element) => element.style("display") !== "none" && Number(element.style("opacity")) > .2);
    if (visible.length) graph.fit(visible, 44);
  }, [mode]);

  if (!claims.length) return <div className="empty">{t("viewer.graph_empty")}</div>;
  return (
    <div className="loom-shell">
      <div className="loom-controls" aria-label={t("viewer.graph")}>
        {(["all", "claims", "gaps"] as LoomMode[]).map((item) => <button type="button" className={mode === item ? "active" : ""} aria-pressed={mode === item} onClick={() => setMode(item)} key={item}>{item === "all" ? t("viewer.overview") : t(`viewer.${item}`)}</button>)}
      </div>
      <div className="loom-stage">
        <div className="loom-grid" aria-hidden="true" />
        <div className="graph-canvas" ref={container} role="img" aria-label={t("viewer.graph")} />
        <div className="loom-legend" aria-hidden="true"><span className="claim-key">CLAIM</span><span className="evidence-key">EVIDENCE</span><span className="support-key">LINK</span></div>
      </div>
      <aside className={`loom-inspector ${selected ? "is-open" : ""}`} aria-live="polite">
        {selected ? <><div><span>{selected.kind}</span><code>{selected.id}</code></div><h3>{selected.title}</h3><p>{selected.meta}</p><button type="button" onClick={() => setSelected(null)} aria-label="Close">×</button></> : <><span>TRACE / SELECT</span><p>{t("viewer.graph")}</p><small>{claims.length} claims · {evidence.length} evidence records</small></>}
      </aside>
    </div>
  );
}

function Metric({ index, label, value, tone = "default" }: { index: number; label: string; value: number; tone?: string }) {
  return <div className={`metric ${tone}`}><span>0{index}</span><strong>{value}</strong><p>{label}</p></div>;
}

function StatusMark({ status, children }: { status: string; children: React.ReactNode }) {
  return <span className={`status ${status}`}>{children}</span>;
}

class ErrorBoundary extends React.Component<{ language: LocaleCode; children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error) { console.error("RigorGraph viewer error", error); }
  render() {
    if (!this.state.failed) return this.props.children;
    const catalog = data.locales[this.props.language] ?? data.locales.en;
    return <main><section className="panel empty">{catalog["viewer.render_error"]}</section></main>;
  }
}

function App() {
  const [language, setLanguage] = useState<LocaleCode>(initialLanguage);
  const [tab, setTab] = useState("overview");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("ALL");
  const t = useTranslator(language);
  const openGaps = data.claims.filter((claim) => gapStatuses.has(claim.status));
  const tabs = ["overview", "graph", "claims", "evidence", "gaps"];

  useEffect(() => { document.documentElement.lang = language; localStorage.setItem("rigorgraph-language", language); }, [language]);
  const filteredClaims = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return data.claims.filter((claim) => (status === "ALL" || claim.status === status) && (!needle || claim.id.toLowerCase().includes(needle) || claim.statement.toLowerCase().includes(needle) || claim.evidence_ids.some((id) => id.toLowerCase().includes(needle))));
  }, [query, status]);

  return (
    <main>
      <header className="hero">
        <div className="hero-title"><div className="eyebrow">RIGORGRAPH / SELF-CONTAINED REPORT</div><h1>{data.project.name}</h1><p>{t("app.tagline")}</p></div>
        <div className="hero-audit" data-status={data.audit.status}>
          <svg viewBox="0 0 180 180" aria-hidden="true"><circle cx="90" cy="90" r="72"/><circle className="progress" cx="90" cy="90" r="72"/></svg>
          <div><span>AUDIT / {data.audit.status}</span><strong>{data.audit.errors + data.audit.warnings}</strong><p>{t("viewer.audit_counts", { errors: data.audit.errors, warnings: data.audit.warnings })}</p></div>
        </div>
        <label className="language-picker"><span>{t("language.label")}</span><select value={language} onChange={(event) => setLanguage(event.target.value as LocaleCode)}>{(Object.keys(languageNames) as LocaleCode[]).map((code) => <option key={code} value={code}>{languageNames[code]}</option>)}</select></label>
      </header>

      <nav className="tabs" aria-label="Report sections">{tabs.map((item, index) => <button key={item} className={tab === item ? "active" : ""} aria-pressed={tab === item} onClick={() => setTab(item)}><span>0{index + 1}</span>{t(`viewer.${item}`)}</button>)}</nav>

      {tab === "overview" && <section className="overview">
        <div className="metrics"><Metric index={1} label={t("viewer.claim_count")} value={data.claims.length}/><Metric index={2} label={t("viewer.evidence_count")} value={data.evidence.length}/><Metric index={3} label={t("viewer.verification_count")} value={data.verifications.length}/><Metric index={4} label={t("viewer.issue_count")} value={data.audit.issues.length} tone={data.audit.errors ? "danger" : "good"}/></div>
        <section className="loom-panel"><header><div><span>CORE VIEW / EVIDENCE LOOM</span><h2>{t("viewer.graph")}</h2></div><p>{t("app.disclaimer")}</p></header><EvidenceLoom claims={data.claims} evidence={data.evidence} language={language}/></section>
        <section className="gap-rail"><header><span>OPEN TRACE</span><h2>{t("viewer.gaps")}</h2></header><div>{openGaps.length ? openGaps.map((claim) => <article className="compact-card" key={claim.id}><div><code>{claim.id}</code><StatusMark status={claim.status}>{t(`status.${claim.status}`)}</StatusMark></div><p>{claim.statement}</p></article>) : <div className="empty">{t("viewer.no_results")}</div>}</div></section>
      </section>}

      {tab === "graph" && <section className="panel graph-only"><EvidenceLoom claims={data.claims} evidence={data.evidence} language={language}/></section>}

      {tab === "claims" && <section className="panel stack">
        <div className="filters"><label><span>{t("viewer.search")}</span><input aria-label={t("viewer.search")} placeholder={t("viewer.search")} value={query} onChange={(event) => setQuery(event.target.value)}/></label><label><span>{t("viewer.status")}</span><select aria-label={t("viewer.status")} value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">{t("viewer.all_statuses")}</option>{["DRAFT", "PROPOSED", "UNDER_REVIEW", "VERIFIED", "REJECTED", "UNCERTAIN", "REVOKED", "SUPERSEDED"].map((item) => <option key={item} value={item}>{t(`status.${item}`)}</option>)}</select></label></div>
        <div className="card-grid">{filteredClaims.map((claim) => <article className="record-card" key={claim.id}><div className="record-head"><code>{claim.id}</code><StatusMark status={claim.status}>{t(`status.${claim.status}`)}</StatusMark></div><h3>{claim.statement}</h3><dl><dt>{t("viewer.type")}</dt><dd>{t(`claim_type.${claim.type}`)}</dd><dt>{t("viewer.authors")}</dt><dd>{claim.authors.join(", ")}</dd><dt>{t("viewer.dependencies")}</dt><dd>{claim.dependencies.join(", ") || "—"}</dd><dt>{t("viewer.linked_evidence")}</dt><dd>{claim.evidence_ids.join(", ") || "—"}</dd></dl></article>)}</div>
        {!filteredClaims.length && <div className="empty">{t("viewer.no_results")}</div>}
      </section>}

      {tab === "evidence" && <section className="panel card-grid">{data.evidence.map((item) => <article className="record-card evidence-card" key={item.id}><div className="record-head"><code>{item.id}</code><span className="type-pill">{t(`evidence_type.${item.type}`)}</span></div><h3>{item.title}</h3><dl><dt>{t("viewer.producer")}</dt><dd>{item.producer}</dd><dt>{t("viewer.scope")}</dt><dd>{item.scope}</dd><dt>{t("viewer.locator")}</dt><dd>{item.locator || "—"}</dd><dt>{t("viewer.location")}</dt><dd>{item.path || item.uri || "—"}</dd><dt>{t("viewer.hash")}</dt><dd className="hash">{item.sha256 || "—"}</dd>{item.metadata?.bundle && <><dt>{t("viewer.bundle_profile")}</dt><dd>{item.metadata.bundle.profile}</dd><dt>{t("viewer.bundle_result")}</dt><dd>{item.metadata.bundle.result_status || "—"}</dd><dt>{t("viewer.source_commit")}</dt><dd className="hash">{item.metadata.bundle.provenance?.commit || "—"}</dd></>}</dl>{item.metadata?.bundle && <p className="evidence-boundary">{t("viewer.bundle_boundary")}</p>}</article>)}</section>}

      {tab === "gaps" && <section className="panel stack issue-stack">{data.audit.issues.map((issue) => <article className={`issue ${issue.severity}`} key={`${issue.code}-${issue.subject_id ?? "global"}`}><div><strong>{t(`severity.${issue.severity}`)}</strong><code>{issue.code}</code><span>{issue.subject_id ?? "—"}</span></div><p>{t(issue.message_id, issue.details)}</p></article>)}{!data.audit.issues.length && <div className="empty">{t("viewer.no_results")}</div>}</section>}

      <footer><p>{t("app.disclaimer")}</p><p>{t("viewer.original_content")}</p><span>RIGORGRAPH / OFFLINE / READ-ONLY</span></footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><ErrorBoundary language={data.language.default}><App /></ErrorBoundary></React.StrictMode>);
