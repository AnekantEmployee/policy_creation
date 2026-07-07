// ─────────────────────────────────────────────
// GRC AI - Agent Features Sheet Generator
// Matches SOC Agents Excel template structure
// Run: generateGRCAISheet()
// ─────────────────────────────────────────────

function generateGRCAISheet() {
  var ss = SpreadsheetApp.create("GRC AI - Agent Features");
  buildFeatureDetails(ss);
  buildAgentSummary(ss);
  buildComparisonSheet(ss);
  // Remove default blank Sheet1
  var def = ss.getSheetByName("Sheet1");
  if (def) ss.deleteSheet(def);
  Logger.log("Done: " + ss.getUrl());
}

// ─── COLOUR PALETTE (mirrors SOC template) ───
var C_HEADER_BG   = "#203864"; // dark navy  - column header row
var C_HEADER_FG   = "#FFFFFF";
var C_LIB_BG      = "#D6E4F0"; // light blue - library group row
var C_LIB_FG      = "#000000";
var C_AGENT_BG    = "#EBF5FB"; // lighter blue - agent first-feature row
var C_FEAT_BG     = "#FFFFFF"; // white - continuation feature rows
var C_LEGEND_BG   = "#F2F2F2"; // light grey - legend section
var C_LIVE_BG     = "#C6EFCE"; var C_LIVE_FG = "#276221"; // green
var C_DEV_BG      = "#FFEB9C"; var C_DEV_FG  = "#9C6500"; // amber
var C_DEMO_BG     = "#DDEBF7"; var C_DEMO_FG = "#1F4E79"; // blue

// ─── SHEET 1: Feature Details ────────────────
function buildFeatureDetails(ss) {
  var sh = ss.insertSheet("Feature Details", 0);

  // --- define agents ---
  var agents = [
    {
      library:   "Agent Library",
      name:      "Organization Profiler",
      status:    "Live",
      category:  "Framework Analysis",
      access:    "All Users",
      features: [
        "Organization description analysis",
        "Website intelligence gathering (Tavily web research)",
        "Industry detection (healthcare, finance, tech, government, etc.)",
        "Geographic region mapping",
        "Data type identification (personal, health, financial, payment)",
        "Framework relevance scoring (0.0 - 1.0)",
        "Mandatory vs. recommended classification",
        "Rule-based fallback system"
      ]
    },
    {
      library:   "Agent Library",
      name:      "Policy Generator",
      status:    "Live",
      category:  "Policy Creation",
      access:    "All Users",
      features: [
        "8 policy types generation",
        "AI-generated policies (1,500+ chars, organization-specific)",
        "9-section comprehensive policy structure",
        "10+ specific actionable requirements per policy",
        "5+ roles defined with clear responsibilities",
        "Framework-specific citations (e.g. GDPR Article 32, HIPAA §164.308)",
        "Organization-specific tailoring (not templates)",
        "3-attempt retry with fresh LLM on each attempt",
        "JSON sanitization and automatic error recovery"
      ]
    },
    {
      library:   "Agent Library",
      name:      "Procedure Generator",
      status:    "Live",
      category:  "Operational Procedures",
      access:    "All Users",
      features: [
        "10 procedure types generation",
        "Exactly 10 detailed steps per procedure",
        "Responsible role assigned per step",
        "Timeline specification per step",
        "Tools and systems required per step",
        "Documentation artifact per step",
        "Full escalation path with decision chain",
        "Framework alignment and control mapping",
        "3-attempt retry with exponential backoff",
        "Substantive fallback procedure (not stubs)"
      ]
    },
    {
      library:   "Agent Library",
      name:      "Policy Consolidator",
      status:    "Live",
      category:  "Multi-Framework Consolidation",
      access:    "All Users",
      features: [
        "Multi-framework policy consolidation (2+ frameworks → 1 master policy)",
        "Intelligent conflict resolution (applies stricter requirement)",
        "Requirement deduplication across frameworks",
        "Domain-based organization (8 compliance domains)",
        "Cross-framework compliance matrix generation",
        "Framework cross-references per requirement",
        "Implementation priority matrix",
        "Fallback consolidation system"
      ]
    }
  ];

  // --- write column headers ---
  var headers = ["Library", "Agent Name", "Status", "Category / Focus", "Access Level", "Feature"];
  sh.getRange(1, 1, 1, 6).setValues([headers]);
  applyHeaderStyle(sh.getRange(1, 1, 1, 6));
  sh.setFrozenRows(1);

  // --- write rows ---
  var row = 2;
  for (var a = 0; a < agents.length; a++) {
    var ag = agents[a];
    var startRow = row;
    var featureCount = ag.features.length;

    for (var f = 0; f < featureCount; f++) {
      if (f === 0) {
        sh.getRange(row, 1).setValue(ag.library);
        sh.getRange(row, 2).setValue(ag.name);
        sh.getRange(row, 3).setValue(ag.status);
        sh.getRange(row, 4).setValue(ag.category);
        sh.getRange(row, 5).setValue(ag.access);
      } else {
        sh.getRange(row, 1).setValue("");
        sh.getRange(row, 2).setValue("");
        sh.getRange(row, 3).setValue("");
        sh.getRange(row, 4).setValue("");
        sh.getRange(row, 5).setValue("");
      }
      sh.getRange(row, 6).setValue(ag.features[f]);
      row++;
    }

    // Merge cols 1-5 vertically for this agent block
    if (featureCount > 1) {
      sh.getRange(startRow, 1, featureCount, 1).mergeVertically();
      sh.getRange(startRow, 2, featureCount, 1).mergeVertically();
      sh.getRange(startRow, 3, featureCount, 1).mergeVertically();
      sh.getRange(startRow, 4, featureCount, 1).mergeVertically();
      sh.getRange(startRow, 5, featureCount, 1).mergeVertically();
    }

    // Style the merged block
    var blockRange = sh.getRange(startRow, 1, featureCount, 6);
    blockRange.setBackground(a % 2 === 0 ? "#EBF5FB" : "#FDFEFE");
    blockRange.setFontSize(10);
    blockRange.setFontFamily("Arial");
    blockRange.setVerticalAlignment("middle");
    blockRange.setHorizontalAlignment("left");
    blockRange.setWrap(true);
    blockRange.setBorder(true, true, true, true, false, true,
      "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);

    // Bold the agent name cell
    sh.getRange(startRow, 2, featureCount, 1).setFontWeight("bold");

    // Status badge colour
    var statusCell = sh.getRange(startRow, 3);
    colorStatus(statusCell, ag.status);
    statusCell.setHorizontalAlignment("center");
    statusCell.setFontWeight("bold");

    // Bold outer border for this block
    sh.getRange(startRow, 1, featureCount, 6)
      .setBorder(true, true, true, true, false, false,
        "#203864", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  }

  // Column widths
  sh.setColumnWidth(1, 120);
  sh.setColumnWidth(2, 190);
  sh.setColumnWidth(3, 80);
  sh.setColumnWidth(4, 195);
  sh.setColumnWidth(5, 110);
  sh.setColumnWidth(6, 340);
}

// ─── SHEET 2: Agent Summary ───────────────────
function buildAgentSummary(ss) {
  var sh = ss.insertSheet("Agent Summary", 1);

  var headers = ["Library", "Agent Name", "Status", "Category / Focus", "Access Level", "# Features"];
  sh.getRange(1, 1, 1, 6).setValues([headers]);
  applyHeaderStyle(sh.getRange(1, 1, 1, 6));
  sh.setFrozenRows(1);

  var rows = [
    ["Agent Library", "Organization Profiler",           "Live", "Framework Analysis",           "All Users", 8],
    ["Agent Library", "Policy Generator",                "Live", "Policy Creation",               "All Users", 9],
    ["Agent Library", "Procedure Generator",             "Live", "Operational Procedures",        "All Users", 10],
    ["Agent Library", "Policy Consolidator",             "Live", "Multi-Framework Consolidation", "All Users", 8]
  ];

  sh.getRange(2, 1, rows.length, 6).setValues(rows);

  // Style data rows
  for (var i = 0; i < rows.length; i++) {
    var r = 2 + i;
    var rowRange = sh.getRange(r, 1, 1, 6);
    rowRange.setBackground(i % 2 === 0 ? "#EBF5FB" : "#FDFEFE");
    rowRange.setFontSize(10);
    rowRange.setFontFamily("Arial");
    rowRange.setVerticalAlignment("middle");
    rowRange.setHorizontalAlignment("left");
    rowRange.setBorder(true, true, true, true, true, true,
      "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);

    var statusCell = sh.getRange(r, 3);
    colorStatus(statusCell, rows[i][2]);
    statusCell.setHorizontalAlignment("center");
    statusCell.setFontWeight("bold");

    // Right-align feature count
    sh.getRange(r, 6).setHorizontalAlignment("center").setFontWeight("bold");
  }

  // Total row
  var totalRow = 2 + rows.length;
  sh.getRange(totalRow, 1, 1, 6).setValues([["", "TOTAL", "", "", "", 35]]);
  sh.getRange(totalRow, 1, 1, 6)
    .setBackground("#203864")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("left");
  sh.getRange(totalRow, 6)
    .setHorizontalAlignment("center");

  // ── Status Legend ──
  var legendRow = totalRow + 2;
  sh.getRange(legendRow, 1, 1, 2).setValues([["Status Legend", ""]]);
  sh.getRange(legendRow, 1, 1, 2)
    .setBackground(C_HEADER_BG).setFontColor(C_HEADER_FG)
    .setFontWeight("bold").setFontSize(10)
    .setBorder(true, true, true, true, true, true, "#203864", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  var legend = [
    ["Live",  "Fully built and operational"],
    ["Dev",   "Currently in development"],
    ["Demo",  "Available as demo / POC"]
  ];
  sh.getRange(legendRow + 1, 1, legend.length, 2).setValues(legend);
  for (var j = 0; j < legend.length; j++) {
    var lr = legendRow + 1 + j;
    colorStatus(sh.getRange(lr, 1), legend[j][0]);
    sh.getRange(lr, 1).setHorizontalAlignment("center").setFontWeight("bold");
    sh.getRange(lr, 2).setBackground("#FFFFFF").setFontSize(10);
    sh.getRange(lr, 1, 1, 2).setBorder(true, true, true, true, true, true,
      "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
  }

  // Column widths
  sh.setColumnWidth(1, 120);
  sh.setColumnWidth(2, 220);
  sh.setColumnWidth(3, 80);
  sh.setColumnWidth(4, 200);
  sh.setColumnWidth(5, 110);
  sh.setColumnWidth(6, 100);
}

// ─── SHEET 3: Market Comparison ──────────────
function buildComparisonSheet(ss) {
  var sh = ss.insertSheet("Market Comparison", 2);

  // ── Section 1: Feature vs Competitor matrix ──
  var secARow = 1;
  sh.getRange(secARow, 1).setValue("FEATURE COMPARISON vs. COMPETITORS");
  sh.getRange(secARow, 1, 1, 7)
    .mergeAcross()
    .setBackground(C_HEADER_BG)
    .setFontColor(C_HEADER_FG)
    .setFontWeight("bold")
    .setFontSize(11)
    .setFontFamily("Arial")
    .setVerticalAlignment("middle")
    .setHorizontalAlignment("left")
    .setBorder(true, true, true, true, true, true, "#FFFFFF", SpreadsheetApp.BorderStyle.SOLID);
  sh.setRowHeight(secARow, 30);

  var colHeaders = ["Feature / Capability", "Our System", "Ciphrix", "Hyperproof", "Drata", "Secureframe", "Vanta"];
  sh.getRange(secARow + 1, 1, 1, 7).setValues([colHeaders]);
  applyHeaderStyle(sh.getRange(secARow + 1, 1, 1, 7));
  sh.setFrozenRows(secARow + 1);

  // Y = has it  N = doesn't  P = partial
  var Y = "Yes";
  var N = "No";
  var P = "Partial";

  var features = [
    // [Feature, Ours, Ciphrix, Hyperproof, Drata, Secureframe, Vanta]
    ["AI-Generated Policies",                    Y, Y, P, N, N, N],
    ["Organization-Specific Tailoring",          Y, Y, P, N, N, N],
    ["8+ Policy Types",                          Y, P, P, P, P, P],
    ["Framework-Specific Citations",             Y, Y, P, P, P, P],
    ["Multi-Framework Support (10+)",            Y, N, Y, Y, Y, Y],
    ["Procedure Generation (10 types)",          Y, N, N, N, N, N],
    ["Step-by-Step Operational Runbooks",        Y, N, N, N, N, N],
    ["Policy Consolidation (Master Policy)",     Y, N, N, N, N, N],
    ["Cross-Framework Conflict Resolution",      Y, N, N, N, N, N],
    ["Org Profiler + Framework Recommendations", Y, N, N, N, N, N],
    ["Web Intelligence (Tavily Research)",       Y, N, N, N, N, N],
    ["Retry / Fallback Robustness",              Y, P, P, P, P, P],
    ["Evidence Collection",                      N, Y, Y, Y, Y, Y],
    ["System Integrations",                      N, N, Y, Y, Y, Y],
    ["Auditor Network / Handoff",                N, N, Y, Y, Y, Y],
    ["Vendor Questionnaire Auto-Completion",     N, Y, N, N, N, N],
    ["Compliance Dashboard",                     N, N, Y, Y, Y, Y],
    ["Custom Framework Support",                 N, N, Y, P, P, N],
    ["Risk Assessment Module",                   N, N, Y, Y, Y, P],
    ["Compliance Training Module",               N, N, P, Y, Y, Y]
  ];

  sh.getRange(secARow + 2, 1, features.length, 7).setValues(features);

  // Style feature rows
  for (var i = 0; i < features.length; i++) {
    var r = secARow + 2 + i;
    var rowBg = i % 2 === 0 ? "#EBF5FB" : "#FDFEFE";
    sh.getRange(r, 1, 1, 7)
      .setBackground(rowBg)
      .setFontSize(10)
      .setFontFamily("Arial")
      .setVerticalAlignment("middle")
      .setHorizontalAlignment("left")
      .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
    sh.setRowHeight(r, 24);

    // Colour each cell in cols 2-7 by Yes/No/Partial
    for (var c = 2; c <= 7; c++) {
      var cell = sh.getRange(r, c);
      var val = features[i][c - 1];
      if (val === Y) {
        cell.setBackground("#C6EFCE").setFontColor("#276221").setFontWeight("bold").setHorizontalAlignment("center");
      } else if (val === N) {
        cell.setBackground("#FFCCCC").setFontColor("#9C0006").setFontWeight("bold").setHorizontalAlignment("center");
      } else if (val === P) {
        cell.setBackground("#FFEB9C").setFontColor("#9C6500").setFontWeight("bold").setHorizontalAlignment("center");
      }
    }
  }

  // ── Section 2: Unique Advantages ──
  var secBRow = secARow + 2 + features.length + 2;
  sh.getRange(secBRow, 1).setValue("OUR UNIQUE ADVANTAGES (Not available in any competitor)");
  sh.getRange(secBRow, 1, 1, 7)
    .mergeAcross()
    .setBackground(C_LIVE_BG)
    .setFontColor(C_LIVE_FG)
    .setFontWeight("bold")
    .setFontSize(11)
    .setFontFamily("Arial")
    .setVerticalAlignment("middle")
    .setHorizontalAlignment("left")
    .setBorder(true, true, true, true, true, true, "#276221", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  sh.setRowHeight(secBRow, 30);

  var advHeaders = ["Capability", "Description", "", "", "", "", ""];
  sh.getRange(secBRow + 1, 1, 1, 7).setValues([advHeaders]);
  applyHeaderStyle(sh.getRange(secBRow + 1, 1, 1, 7));

  var advantages = [
    ["Policy Consolidation",            "Consolidates policies from 2+ frameworks into one unified master policy with conflict resolution and deduplication", "", "", "", "", ""],
    ["Procedure Generation",            "Generates 10 detailed operational procedures, each with exactly 10 steps, roles, timelines, tools and escalation paths", "", "", "", "", ""],
    ["Organization Profiler",           "Automatically recommends applicable compliance frameworks from org description + website (Tavily research)", "", "", "", "", ""],
    ["Cross-Framework Conflict Solver", "When frameworks conflict, applies the stricter requirement and documents the reasoning", "", "", "", "", ""],
    ["Web Intelligence Integration",    "Uses Tavily to research the organization's website for more accurate framework scoring", "", "", "", "", ""]
  ];

  sh.getRange(secBRow + 2, 1, advantages.length, 7).setValues(advantages);

  for (var k = 0; k < advantages.length; k++) {
    var ar = secBRow + 2 + k;
    sh.getRange(ar, 1, 1, 7)
      .setBackground(k % 2 === 0 ? "#EBF5FB" : "#FDFEFE")
      .setFontSize(10)
      .setFontFamily("Arial")
      .setVerticalAlignment("middle")
      .setWrap(true)
      .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
    sh.getRange(ar, 1).setFontWeight("bold");
    sh.getRange(ar, 2, 1, 6).mergeAcross();
    sh.setRowHeight(ar, 36);
  }

  // ── Section 3: Gaps to Close ──
  var secCRow = secBRow + 2 + advantages.length + 2;
  sh.getRange(secCRow, 1).setValue("GAPS TO CLOSE (What competitors have that we don't)");
  sh.getRange(secCRow, 1, 1, 7)
    .mergeAcross()
    .setBackground("#FCE4D6")
    .setFontColor("#833C00")
    .setFontWeight("bold")
    .setFontSize(11)
    .setFontFamily("Arial")
    .setVerticalAlignment("middle")
    .setHorizontalAlignment("left")
    .setBorder(true, true, true, true, true, true, "#833C00", SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  sh.setRowHeight(secCRow, 30);

  var gapHeaders = ["Gap", "Competitor(s)", "Impact", "Recommended Fix", "", "", ""];
  sh.getRange(secCRow + 1, 1, 1, 7).setValues([gapHeaders]);
  applyHeaderStyle(sh.getRange(secCRow + 1, 1, 1, 7));

  var gaps = [
    ["No evidence collection",            "Ciphrix, Hyperproof, Drata, Vanta",  "Cannot validate policy implementation",   "Build an evidence collection agent with key integrations", "", "", ""],
    ["No system integrations",            "Vanta (300+), Drata (100+)",         "Cannot pull live compliance data",        "Add integrations: Okta, GitHub, AWS, Datadog, Slack",      "", "", ""],
    ["No auditor network",                "Secureframe, Drata, Thoropass",       "Cannot directly hand off to auditors",    "Create auditor-facing export formats and dashboards",      "", "", ""],
    ["Limited framework breadth",         "Hyperproof (140), Drata (15)",        "Cannot serve orgs with niche frameworks", "Expand to 20+ frameworks, add custom framework support",   "", "", ""],
    ["No vendor questionnaire agent",     "Ciphrix",                            "Cannot auto-answer security questionnaires","Build questionnaire auto-completion agent",               "", "", ""],
    ["No risk assessment module",         "Hyperproof, Drata, Secureframe",      "Cannot quantify compliance risk",         "Add a lightweight risk scoring and assessment module",     "", "", ""]
  ];

  sh.getRange(secCRow + 2, 1, gaps.length, 7).setValues(gaps);

  for (var g = 0; g < gaps.length; g++) {
    var gr = secCRow + 2 + g;
    sh.getRange(gr, 1, 1, 7)
      .setBackground(g % 2 === 0 ? "#FFF2CC" : "#FDFEFE")
      .setFontSize(10)
      .setFontFamily("Arial")
      .setVerticalAlignment("middle")
      .setWrap(true)
      .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
    sh.getRange(gr, 1).setFontWeight("bold");
    sh.getRange(gr, 4, 1, 4).mergeAcross();
    sh.setRowHeight(gr, 36);
  }

  // ── Legend ──
  var legRow = secCRow + 2 + gaps.length + 2;
  sh.getRange(legRow, 1, 1, 3).setValues([["LEGEND", "", ""]]);
  sh.getRange(legRow, 1, 1, 3)
    .mergeAcross()
    .setBackground(C_HEADER_BG).setFontColor(C_HEADER_FG)
    .setFontWeight("bold").setFontSize(10).setFontFamily("Arial")
    .setHorizontalAlignment("left").setVerticalAlignment("middle");

  var legData = [
    ["Yes",     "Feature available",            "#C6EFCE", "#276221"],
    ["No",      "Feature not available",        "#FFCCCC", "#9C0006"],
    ["Partial", "Partially available / limited","#FFEB9C", "#9C6500"]
  ];
  for (var l = 0; l < legData.length; l++) {
    var lr = legRow + 1 + l;
    sh.getRange(lr, 1).setValue(legData[l][0])
      .setBackground(legData[l][2]).setFontColor(legData[l][3])
      .setFontWeight("bold").setFontSize(10).setHorizontalAlignment("center")
      .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
    sh.getRange(lr, 2).setValue(legData[l][1])
      .setBackground("#FFFFFF").setFontSize(10).setFontFamily("Arial")
      .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
  }

  // Column widths
  sh.setColumnWidth(1, 240);
  sh.setColumnWidth(2, 200);
  sh.setColumnWidth(3, 200);
  sh.setColumnWidth(4, 240);
  sh.setColumnWidth(5, 60);
  sh.setColumnWidth(6, 60);
  sh.setColumnWidth(7, 60);
}

// ─── HELPERS ─────────────────────────────────

function applyHeaderStyle(range) {
  range.setBackground(C_HEADER_BG);
  range.setFontColor(C_HEADER_FG);
  range.setFontWeight("bold");
  range.setFontSize(11);
  range.setFontFamily("Arial");
  range.setHorizontalAlignment("left");
  range.setVerticalAlignment("middle");
  range.setWrap(true);
  range.setBorder(true, true, true, true, true, true,
    "#FFFFFF", SpreadsheetApp.BorderStyle.SOLID);
}

function colorStatus(cell, status) {
  if (status === "Live") {
    cell.setBackground(C_LIVE_BG).setFontColor(C_LIVE_FG);
  } else if (status === "Dev") {
    cell.setBackground(C_DEV_BG).setFontColor(C_DEV_FG);
  } else if (status === "Demo") {
    cell.setBackground(C_DEMO_BG).setFontColor(C_DEMO_FG);
  }
}
