import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const artifactToolPath = pathToFileURL(
  "C:/Users/HOANG PHI LONG DANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs",
).href;
const { SpreadsheetFile, Workbook } = await import(artifactToolPath);

const inputPath = process.argv[2] ?? "C:/tmp/berlin_hausverwaltungen_task1_build.json";
const outputPath = process.argv[3] ?? "output/berlin-hausverwaltungen-task1-2026-11-09.xlsx";
const previewDir = process.argv[4] ?? "C:/tmp/berlin_hausverwaltungen_previews";

const input = JSON.parse(await fs.readFile(inputPath, "utf8"));
if (input.account_intelligence_mode === "production") {
  if (!input.run_manifest || !Array.isArray(input.dossiers)) {
    throw new Error("production workbook requires run_manifest and dossiers");
  }
  const dossierIds = new Set(input.dossiers.map((item) => String(item.company_id ?? item.thesis?.company_id ?? "")));
  const dossiersById = new Map(input.dossiers.map((item) => [String(item.company_id ?? item.thesis?.company_id ?? ""), item]));
  const requiredLineageFields = ["rank_audit", "dossier_hash", "semantic_review_ids", "strongest_claim_ids", "projection_run_id"];
  for (const row of input.priority_rows ?? []) {
    const dossier = dossiersById.get(String(row.company_id ?? ""));
    if (!dossierIds.has(String(row.company_id ?? "")) || requiredLineageFields.some((field) => row[field] === undefined || row[field] === null || row[field] === "") || String(row.dossier_hash ?? "") !== String(dossier?.dossier_hash ?? "")) {
      throw new Error(`priority row lacks dossier lineage: ${row.company_id ?? ""}`);
    }
  }
}
const workbook = Workbook.create();

workbook.colorScheme = {
  name: "Berlin Hausverwaltungen",
  themeColors: {
    accent1: "#1D4ED8",
    accent2: "#0F766E",
    bg1: "#FFFFFF",
    tx1: "#0F172A",
  },
};

const headers = Object.keys(input.rows[0]);
const priorityHeaders = headers;
const titleFill = "#0F172A";
const headerFill = "#1D4ED8";
const lightFill = "#EFF6FF";
const borderColor = "#CBD5E1";

function columnLetter(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

const explicitUnknownFields = new Set([
  "Portfolio Size",
  "Portfolio Potential",
  "Structural Lead Fit",
  "Evidence Coverage",
]);

function normalizeCell(value, header) {
  if ((value === undefined || value === null || value === "") && explicitUnknownFields.has(header)) {
    return "Unknown";
  }
  return value === undefined ? null : value;
}

function writeIntro(sheet, title, note, lastColumn) {
  sheet.showGridLines = false;
  sheet.mergeCells(`A1:${lastColumn}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: titleFill,
    font: { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 16 },
    horizontalAlignment: "left",
    verticalAlignment: "middle",
    rowHeightPx: 32,
  };
  sheet.mergeCells(`A2:${lastColumn}2`);
  sheet.getRange("A2").values = [[note]];
  sheet.getRange(`A2:${lastColumn}2`).format = {
    fill: lightFill,
    font: { name: "Aptos", color: "#334155", size: 10 },
    wrapText: true,
    verticalAlignment: "middle",
    rowHeightPx: 36,
  };
}

function writeTableSheet({ name, title, note, rows, tableName, tabColor }) {
  const sheet = workbook.worksheets.add(name);
  const lastColumn = columnLetter(headers.length - 1);
  writeIntro(sheet, title, note, lastColumn);
  const tableStartRow = 4;
  const tableEndRow = tableStartRow + rows.length;
  const headerRange = `${columnLetter(0)}${tableStartRow}:${lastColumn}${tableStartRow}`;
  const dataRange = `${columnLetter(0)}${tableStartRow + 1}:${lastColumn}${tableEndRow}`;
  const fullRange = `${columnLetter(0)}${tableStartRow}:${lastColumn}${tableEndRow}`;
  sheet.getRange(headerRange).values = [headers];
  sheet.getRange(dataRange).values = rows.map((row) => headers.map((header) => normalizeCell(row[header], header)));
  const table = sheet.tables.add(fullRange, true, tableName);
  table.style = "TableStyleMedium2";
  table.showHeaders = true;
  table.showFilterButton = true;
  table.showTotals = false;
  table.showBandedRows = true;
  sheet.getRange(headerRange).format = {
    fill: headerFill,
    font: { name: "Aptos", bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "middle",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: borderColor },
    rowHeightPx: 42,
  };
  sheet.getRange(dataRange).format = {
    font: { name: "Aptos", size: 10, color: "#0F172A" },
    verticalAlignment: "top",
    wrapText: true,
    rowHeightPx: 34,
  };
  sheet.getRange(`${columnLetter(0)}${tableStartRow}:${lastColumn}${tableEndRow}`).format.borders = {
    preset: "all",
    style: "thin",
    color: borderColor,
  };
  const numericColumns = ["A", "P", "T", "U"];
  for (const column of numericColumns) {
    sheet.getRange(`${column}${tableStartRow + 1}:${column}${tableEndRow}`).setNumberFormat("0");
    sheet.getRange(`${column}${tableStartRow + 1}:${column}${tableEndRow}`).format.horizontalAlignment = "center";
  }
  const widths = {
    A: 8,
    B: 20,
    C: 34,
    D: 32,
    E: 24,
    F: 34,
    G: 32,
    H: 12,
    I: 16,
    J: 18,
    K: 16,
    L: 16,
    M: 14,
    N: 14,
    O: 16,
    P: 14,
    Q: 18,
    R: 18,
    S: 20,
    T: 16,
    U: 18,
    V: 16,
    W: 18,
    X: 16,
    Y: 16,
    Z: 12,
    AA: 28,
    AB: 18,
    AC: 48,
    AD: 34,
    AE: 42,
    AF: 22,
  };
  for (const [column, width] of Object.entries(widths)) {
    sheet.getRange(`${column}1:${column}${tableEndRow}`).format.columnWidth = width;
  }
  sheet.getRange(`C${tableStartRow + 1}:G${tableEndRow}`).format.wrapText = true;
  sheet.getRange(`AC${tableStartRow + 1}:AE${tableEndRow}`).format.wrapText = true;
  sheet.getRange(`T${tableStartRow + 1}:U${tableEndRow}`).conditionalFormats.add("dataBar", {
    color: "#60A5FA",
    gradient: true,
    showValue: true,
  });
  sheet.freezePanes.freezeRows(tableStartRow);
  sheet.freezePanes.freezeColumns(3);
  sheet.tabColor = tabColor;
  return { sheet, table, tableEndRow };
}

const overview = writeTableSheet({
  name: "Berlin Hausverwaltungen",
  title: "Berlin Hausverwaltungen — Qualified Company Overview",
  note: "320 accepted companies from the canonical discovery dataset. Unknown is preserved as unknown, not treated as negative evidence. Use Lead Tier, Structural Lead Fit, Evidence Coverage, Buying Signal, and Next Action together.",
  rows: input.rows,
  tableName: "BerlinHausverwaltungen",
  tabColor: "#1D4ED8",
});

const priority = writeTableSheet({
  name: "Top 30 Leads",
  title: "Top 30 Berlin Hausverwaltung Leads",
  note: "Ranked shortlist from the canonical dossier projection. Each row must resolve to a rank audit, semantic review, promoted claim, and source lineage.",
  rows: input.priority_rows,
  tableName: "Top30Leads",
  tabColor: "#0F766E",
});

function writeSimpleSheet({ name, title, note, headers: simpleHeaders, rows, tableName, tabColor, widths }) {
  const sheet = workbook.worksheets.add(name);
  const lastColumn = columnLetter(simpleHeaders.length - 1);
  writeIntro(sheet, title, note, lastColumn);
  const tableStartRow = 4;
  const tableEndRow = tableStartRow + rows.length;
  const headerRange = `A${tableStartRow}:${lastColumn}${tableStartRow}`;
  const dataRange = `A${tableStartRow + 1}:${lastColumn}${tableEndRow}`;
  const fullRange = `A${tableStartRow}:${lastColumn}${tableEndRow}`;
  sheet.getRange(headerRange).values = [simpleHeaders];
  sheet.getRange(dataRange).values = rows.map((row) => simpleHeaders.map((header) => normalizeCell(row[header])));
  const table = sheet.tables.add(fullRange, true, tableName);
  table.style = "TableStyleMedium4";
  sheet.getRange(headerRange).format = {
    fill: headerFill,
    font: { name: "Aptos", bold: true, color: "#FFFFFF", size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "middle",
    wrapText: true,
    rowHeightPx: 42,
    borders: { preset: "all", style: "thin", color: borderColor },
  };
  sheet.getRange(dataRange).format = {
    font: { name: "Aptos", size: 10, color: "#0F172A" },
    verticalAlignment: "top",
    wrapText: true,
    rowHeightPx: 42,
    borders: { preset: "all", style: "thin", color: borderColor },
  };
  for (const [column, width] of Object.entries(widths)) {
    sheet.getRange(`${column}1:${column}${tableEndRow}`).format.columnWidth = width;
  }
  sheet.freezePanes.freezeRows(tableStartRow);
  sheet.tabColor = tabColor;
  return sheet;
}

writeSimpleSheet({
  name: "KPI Definitions",
  title: "KPI Definitions and Qualification Logic",
  note: "These KPIs separate structural customer fit from timing and contact-readiness. Evidence Coverage is a control metric; it prevents a strong score from hiding major research gaps.",
  headers: ["KPI", "Why it matters", "Values / method", "Weight", "Decision use"],
  rows: input.kpis,
  tableName: "KpiDefinitions",
  tabColor: "#7C3AED",
  widths: { A: 24, B: 56, C: 62, D: 14, E: 48 },
});

writeSimpleSheet({
  name: "Source Notes",
  title: "Source Notes, Scope, and Limitations",
  note: "Use this sheet to interpret the overview responsibly. The workbook is an evidence-backed prospecting list, not a guarantee that every company is active, reachable, or a fit for a specific offer.",
  headers: ["Topic", "Definition / limitation"],
  rows: input.sources.slice(1).map((row) => ({ Topic: row[0], "Definition / limitation": row[1] })),
  tableName: "SourceNotes",
  tabColor: "#64748B",
  widths: { A: 24, B: 110 },
});

if (input.account_intelligence_mode === "production") {
  const dossierRows = input.dossiers.map((item) => ({
    company_id: item.company_id ?? item.thesis?.company_id ?? "",
    offer_id: item.offer_id ?? "",
    offer_version: item.offer_version ?? "",
    dossier_version: item.dossier_version ?? "",
    dossier_hash: item.dossier_hash ?? "",
    why_this_account: item.thesis?.why_this_account ?? "",
    why_now: item.thesis?.why_now ?? "",
    recommended_action: item.thesis?.recommended_action ?? "",
  }));
  const thesisRows = input.dossiers.map((item) => ({ company_id: item.company_id ?? item.thesis?.company_id ?? "", ...(item.thesis ?? {}) }));
  const timelineRows = input.dossiers.flatMap((item) => (item.timeline ?? []).map((event) => ({ company_id: item.company_id ?? item.thesis?.company_id ?? "", ...event })));
  const evidenceRows = input.dossiers.flatMap((item) => (item.claims ?? []).map((claim) => ({ company_id: item.company_id ?? item.thesis?.company_id ?? "", ...claim })));
  const gapRows = input.dossiers.map((item) => ({
    company_id: item.company_id ?? item.thesis?.company_id ?? "",
    research_gap_impact: item.thesis?.research_gap_impact ?? "",
    decision_relevant_gaps: (item.thesis?.hypotheses ?? []).map((hypothesis) => hypothesis.decision_relevant_gap).filter(Boolean).join("; "),
    recommended_action: item.thesis?.recommended_action ?? "",
  }));
  writeSimpleSheet({ name: "Account Dossiers", title: "Account Dossiers", note: "Durable dossier identity and concise account rationale.", headers: Object.keys(dossierRows[0] ?? { company_id: "" }), rows: dossierRows, tableName: "AccountDossiers", tabColor: "#0F766E", widths: { A: 18, B: 24, C: 18, D: 18, E: 70, F: 48, G: 48, H: 42 } });
  writeSimpleSheet({ name: "Account Theses", title: "Account Theses", note: "Validated account thesis, indicators, and recommended action.", headers: Object.keys(thesisRows[0] ?? { company_id: "" }), rows: thesisRows, tableName: "AccountTheses", tabColor: "#0F766E", widths: { A: 18, B: 42, C: 42, D: 42 } });
  writeSimpleSheet({ name: "Account Timeline", title: "Account Timeline", note: "Company-bound chronology reconstructed from promoted claims.", headers: Object.keys(timelineRows[0] ?? { company_id: "" }), rows: timelineRows, tableName: "AccountTimeline", tabColor: "#0F766E", widths: { A: 18, B: 32, C: 42, D: 48 } });
  writeSimpleSheet({ name: "Evidence Ledger", title: "Evidence Ledger", note: "Claim-level source lineage supporting the account thesis.", headers: Object.keys(evidenceRows[0] ?? { company_id: "" }), rows: evidenceRows, tableName: "EvidenceLedger", tabColor: "#0F766E", widths: { A: 18, B: 28, C: 48, D: 70 } });
  writeSimpleSheet({ name: "Research Gaps", title: "Research Gaps", note: "Explicit uncertainty and next action for each account.", headers: ["company_id", "research_gap_impact", "decision_relevant_gaps", "recommended_action"], rows: gapRows, tableName: "ResearchGaps", tabColor: "#0F766E", widths: { A: 18, B: 48, C: 62, D: 42 } });
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);

for (const sheetName of ["Berlin Hausverwaltungen", "Top 30 Leads", "KPI Definitions", "Source Notes", ...(input.account_intelligence_mode === "production" ? ["Account Dossiers", "Account Theses", "Account Timeline", "Evidence Ledger", "Research Gaps"] : [])]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const previewBytes = new Uint8Array(await preview.arrayBuffer());
  const safeName = sheetName.toLowerCase().replaceAll(" ", "-");
  await fs.writeFile(path.join(previewDir, `${safeName}.png`), previewBytes);
}

const inspection = await workbook.inspect({
  select: "$.sheets[*]",
  include: ["name", "regions.range", "regions.rowCount", "regions.columnCount"],
});
await fs.writeFile(
  `${outputPath}.inspect.json`,
  JSON.stringify({
    outputPath,
    companyCount: input.rows.length,
    priorityCount: input.priority_rows.length,
    sheets: inspection.records,
  }, null, 2),
);

console.log(JSON.stringify({
  outputPath,
  previewDir,
  companyCount: input.rows.length,
  priorityCount: input.priority_rows.length,
  sheets: inspection.records,
}, null, 2));
