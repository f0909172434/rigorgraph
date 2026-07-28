import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import cytoscape from "cytoscape";
import "./styles.css";

type LocaleCode = "en" | "zh-TW" | "zh-CN" | "ja";
type Catalog = Record<string, string>;
type Claim = {
  id: string;
  statement: string;
  type: string;
  status: string;
  authors: string[];
  dependencies: string[];
  evidence_ids: string[];
};
type Evidence = {
  id: string;
  type: string;
  title: string;
  producer: string;
  scope: string;
  path?: string;
  uri?: string;
  locator?: string;
  sha256?: string;
};
type AuditIssue = {
  code: string;
  severity: string;
  message_id: string;
  subject_id?: string;
  details: Record<string, string>;
};
type ReportData = {
  project: { name: string; root: string };
  claims: Claim[];
  evidence: Evidence[];
  verifications: unknown[];
  audit: {
    status: "PASS" | "FAIL";
    errors: number;
    warnings: number;
    issues: AuditIssue[];
  };
  locales: Record<LocaleCode, Catalog>;
  language: { default: LocaleCode; source: string; supported: boolean };
};

const payloadElement = document.getElementById("rigorgraph-data");
if (!payloadElement?.textContent) throw new Error("RigorGraph report data is missing");
const data = JSON.parse(payloadElement.textContent) as ReportData;

const languageNames: Record<LocaleCode, string> = {
  en: "English",
  "zh-TW": "繁體中文",
  "zh-CN": "简体中文",
  ja: "日本語",
};

function interpolate(template: string, values: Record<string, unknown> = {}) {
  return template.replace(/\{([^}]+)\}/g, (_, key: string) => String(values[key] ?? `{${key}}`));
}

function useTranslator(language: LocaleCode) {
  return (id: string, values: Record<string, unknown> = {}) =>
    interpolate(data.locales[language]?.[id] ?? data.locales.en[id] ?? id, values);
}

function initialLanguage(): LocaleCode {
  const saved = localStorage.getItem("rigorgraph-language") as LocaleCode | null;
  return saved && saved in languageNames ? saved : data.language.default;
}

function ClaimGraph({ claims, language }: { claims: Claim[]; language: LocaleCode }) {
  const container = useRef<HTMLDivElement>(null);
  const t = useTranslator(language);

  useEffect(() => {
    if (!container.current || claims.length === 0) return;
    const claimIds = new Set(claims.map((claim) => claim.id));
    const graph = cytoscape({
      container: container.current,
      elements: [
        ...claims.map((claim) => ({
          data: { id: claim.id, label: claim.id, status: claim.status, statement: claim.statement },
        })),
        ...claims.flatMap((claim) =>
          claim.dependencies.filter((dependency) => claimIds.has(dependency)).map((dependency) => ({
            data: { id: `${dependency}->${claim.id}`, source: dependency, target: claim.id },
          })),
        ),
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-family": "system-ui, sans-serif",
            "font-size": 11,
            color: "#f7f8ff",
            "text-valign": "center",
            "text-halign": "center",
            width: 62,
            height: 62,
            "background-color": "#6575ff",
            "border-width": 3,
            "border-color": "#b9c2ff",
          },
        },
        { selector: 'node[status = "VERIFIED"]', style: { "background-color": "#087f5b" } },
        { selector: 'node[status = "REJECTED"]', style: { "background-color": "#c92a2a" } },
        { selector: 'node[status = "UNCERTAIN"]', style: { "background-color": "#a55b00" } },
        { selector: 'node[status = "REVOKED"]', style: { "background-color": "#6b7280" } },
        {
          selector: "edge",
          style: {
            width: 2,
            "line-color": "#8590b8",
            "target-arrow-color": "#8590b8",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
          },
        },
      ],
      layout: { name: "breadthfirst", directed: true, padding: 24, spacingFactor: 1.4 },
    });
    graph.nodes().forEach((node) => {
      node.on("mouseover", () => node.style("border-color", "#ffffff"));
      node.on("mouseout", () => node.style("border-color", "#b9c2ff"));
    });
    return () => graph.destroy();
  }, [claims, language]);

  if (!claims.length) return <div className="empty">{t("viewer.graph_empty")}</div>;
  return <div className="graph-canvas" ref={container} role="img" aria-label={t("viewer.graph")} />;
}

function Metric({ label, value, tone = "default" }: { label: string; value: number; tone?: string }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

class ErrorBoundary extends React.Component<
  { language: LocaleCode; children: React.ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error) {
    console.error("RigorGraph viewer error", error);
  }

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

  useEffect(() => {
    document.documentElement.lang = language;
    localStorage.setItem("rigorgraph-language", language);
  }, [language]);

  const filteredClaims = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return data.claims.filter(
      (claim) =>
        (status === "ALL" || claim.status === status) &&
        (!needle ||
          claim.id.toLowerCase().includes(needle) ||
          claim.statement.toLowerCase().includes(needle) ||
          claim.evidence_ids.some((id) => id.toLowerCase().includes(needle))),
    );
  }, [query, status]);

  const openGaps = data.claims.filter((claim) =>
    ["DRAFT", "PROPOSED", "UNDER_REVIEW", "UNCERTAIN"].includes(claim.status),
  );
  const tabs = ["overview", "graph", "claims", "evidence", "gaps"];

  return (
    <main>
      <header className="hero">
        <div>
          <div className="eyebrow">RIGORGRAPH / {data.project.root}</div>
          <h1>{data.project.name}</h1>
          <p>{t("app.tagline")}</p>
        </div>
        <label className="language-picker">
          <span>{t("language.label")}</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value as LocaleCode)}>
            {(Object.keys(languageNames) as LocaleCode[]).map((code) => (
              <option key={code} value={code}>{languageNames[code]}</option>
            ))}
          </select>
        </label>
      </header>

      <section className="audit-banner" data-status={data.audit.status}>
        <span className="pulse" />
        <strong>{t(data.audit.status === "PASS" ? "viewer.audit_pass" : "viewer.audit_fail")}</strong>
        <span>{t("viewer.audit_counts", { errors: data.audit.errors, warnings: data.audit.warnings })}</span>
      </section>

      <nav className="tabs" aria-label="Report sections">
        {tabs.map((item) => (
          <button
            key={item}
            className={tab === item ? "active" : ""}
            aria-pressed={tab === item}
            onClick={() => setTab(item)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                setTab(item);
              }
            }}
          >
            {t(`viewer.${item}`)}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <section className="panel stack">
          <div className="metrics">
            <Metric label={t("viewer.claim_count")} value={data.claims.length} />
            <Metric label={t("viewer.evidence_count")} value={data.evidence.length} />
            <Metric label={t("viewer.verification_count")} value={data.verifications.length} />
            <Metric label={t("viewer.issue_count")} value={data.audit.issues.length} tone={data.audit.errors ? "danger" : "good"} />
          </div>
          <div className="split">
            <div>
              <h2>{t("viewer.graph")}</h2>
              <ClaimGraph claims={data.claims} language={language} />
            </div>
            <div>
              <h2>{t("viewer.gaps")}</h2>
              {openGaps.length ? openGaps.map((claim) => (
                <article className="compact-card" key={claim.id}>
                  <div><code>{claim.id}</code><span className={`status ${claim.status}`}>{t(`status.${claim.status}`)}</span></div>
                  <p>{claim.statement}</p>
                </article>
              )) : <div className="empty">{t("viewer.no_results")}</div>}
            </div>
          </div>
        </section>
      )}

      {tab === "graph" && <section className="panel"><ClaimGraph claims={data.claims} language={language} /></section>}

      {tab === "claims" && (
        <section className="panel stack">
          <div className="filters">
            <input aria-label={t("viewer.search")} placeholder={t("viewer.search")} value={query} onChange={(event) => setQuery(event.target.value)} />
            <select aria-label={t("viewer.status")} value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="ALL">{t("viewer.all_statuses")}</option>
              {["DRAFT", "PROPOSED", "UNDER_REVIEW", "VERIFIED", "REJECTED", "UNCERTAIN", "REVOKED", "SUPERSEDED"].map((item) => (
                <option key={item} value={item}>{t(`status.${item}`)}</option>
              ))}
            </select>
          </div>
          <div className="card-grid">
            {filteredClaims.map((claim) => (
              <article className="record-card" key={claim.id}>
                <div className="record-head"><code>{claim.id}</code><span className={`status ${claim.status}`}>{t(`status.${claim.status}`)}</span></div>
                <h3>{claim.statement}</h3>
                <dl>
                  <dt>{t("viewer.type")}</dt><dd>{t(`claim_type.${claim.type}`)}</dd>
                  <dt>{t("viewer.authors")}</dt><dd>{claim.authors.join(", ")}</dd>
                  <dt>{t("viewer.dependencies")}</dt><dd>{claim.dependencies.join(", ") || "—"}</dd>
                  <dt>{t("viewer.linked_evidence")}</dt><dd>{claim.evidence_ids.join(", ") || "—"}</dd>
                </dl>
              </article>
            ))}
          </div>
          {!filteredClaims.length && <div className="empty">{t("viewer.no_results")}</div>}
        </section>
      )}

      {tab === "evidence" && (
        <section className="panel card-grid">
          {data.evidence.map((item) => (
            <article className="record-card" key={item.id}>
              <div className="record-head"><code>{item.id}</code><span className="type-pill">{t(`evidence_type.${item.type}`)}</span></div>
              <h3>{item.title}</h3>
              <dl>
                <dt>{t("viewer.producer")}</dt><dd>{item.producer}</dd>
                <dt>{t("viewer.scope")}</dt><dd>{item.scope}</dd>
                <dt>{t("viewer.locator")}</dt><dd>{item.locator || "—"}</dd>
                <dt>{t("viewer.location")}</dt><dd>{item.path || item.uri || "—"}</dd>
                <dt>{t("viewer.hash")}</dt><dd className="hash">{item.sha256 || "—"}</dd>
              </dl>
            </article>
          ))}
        </section>
      )}

      {tab === "gaps" && (
        <section className="panel stack">
          {data.audit.issues.map((issue) => (
            <article className={`issue ${issue.severity}`} key={`${issue.code}-${issue.subject_id ?? "global"}`}>
              <div><strong>{t(`severity.${issue.severity}`)}</strong><code>{issue.code}</code><span>{issue.subject_id ?? "—"}</span></div>
              <p>{t(issue.message_id, issue.details)}</p>
            </article>
          ))}
          {!data.audit.issues.length && <div className="empty">{t("viewer.no_results")}</div>}
        </section>
      )}

      <footer>
        <p>{t("app.disclaimer")}</p>
        <p>{t("viewer.original_content")}</p>
      </footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary language={data.language.default}><App /></ErrorBoundary>
  </React.StrictMode>,
);
