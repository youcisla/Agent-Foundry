// Auto-generated — DO NOT EDIT (run scripts/build-site-data.sh to refresh)

const SKILLS = [
  {
    "id": "anti-slop",
    "name": "anti-slop",
    "description": "Kill generic AI patterns before they ship \u2014 filler prose, over-commenting, defensive over-engineering, unnecessary abstr",
    "category": "core",
    "lines": 54
  },
  {
    "id": "api-design",
    "name": "api-design",
    "description": "Design REST or GraphQL APIs: resource modeling, URL conventions, error contracts, versioning, pagination, idempotency ke",
    "category": "core",
    "lines": 72
  },
  {
    "id": "automation-pick",
    "name": "automation-pick",
    "description": "Before automating a task, decide whether to automate. Decision tree based on volume, frequency, error cost, and reversib",
    "category": "core",
    "lines": 65
  },
  {
    "id": "bottleneck-gating",
    "name": "bottleneck-gating",
    "description": "Phase plans by measured bottleneck, not by requested order. Each phase has a gate condition (metric must move before pro",
    "category": "core",
    "lines": 84
  },
  {
    "id": "constraint-then-solve",
    "name": "constraint-then-solve",
    "description": "Before solving, restate the problem, list unknowns, and catalog every constraint. Verify the solution against every cons",
    "category": "core",
    "lines": 85
  },
  {
    "id": "context-optimization",
    "name": "context-optimization",
    "description": "Keep tool outputs small, sandbox large files, reference not repeat. Use on any task with >2K-token outputs, big files, o",
    "category": "core",
    "lines": 57
  },
  {
    "id": "cron-troubleshoot",
    "name": "cron-troubleshoot",
    "description": "Debug a cron job that failed or didn't run: timezone, drift, overlap, missing logs, dependency failure. Use when a sched",
    "category": "core",
    "lines": 83
  },
  {
    "id": "e2e-test-strategy",
    "name": "e2e-test-strategy",
    "description": "Plan an end-to-end test pyramid: which flows to E2E, which to integration, which to unit. Seeding strategy, auth state h",
    "category": "core",
    "lines": 84
  },
  {
    "id": "feedback-loop",
    "name": "feedback-loop",
    "description": "After shipping, set up the loop: instrument \u2192 measure \u2192 review weekly \u2192 adjust. Use when shipping a feature, launching a",
    "category": "core",
    "lines": 76
  },
  {
    "id": "knowledge-extract",
    "name": "knowledge-extract",
    "description": "Read a session, conversation, or document and identify reusable patterns. Draft a new skill (or update an existing one).",
    "category": "core",
    "lines": 83
  },
  {
    "id": "landscape-first",
    "name": "landscape-first",
    "description": "Before building anything in a competitive space, research 5-10 competitors: pricing, UX patterns, positioning, weaknesse",
    "category": "core",
    "lines": 79
  },
  {
    "id": "measure-first",
    "name": "measure-first",
    "description": "Before planning any change, query live data (DB, API, analytics, logs) to find the actual bottleneck. Static analysis re",
    "category": "core",
    "lines": 88
  },
  {
    "id": "plan-before-code",
    "name": "plan-before-code",
    "description": "No implementation without an approved spec for non-trivial work. Brainstorm \u2192 write spec \u2192 get approval \u2192 then code. Use",
    "category": "core",
    "lines": 78
  },
  {
    "id": "plan-then-act",
    "name": "plan-then-act",
    "description": "Plan first, then act. State the plan in one sentence BEFORE any tool call. Every Bash call must include a description fi",
    "category": "core",
    "lines": 90
  },
  {
    "id": "prompt-discipline",
    "name": "prompt-discipline",
    "description": "Enforce the four coding rules \u2014 think before acting, minimum viable change, surgical edits, stay on the stated goal. Use",
    "category": "core",
    "lines": 66
  },
  {
    "id": "pushback-when-wrong",
    "name": "pushback-when-wrong",
    "description": "When the brief contradicts verified reality, push back with evidence. Identify what the user is wrong about AND what the",
    "category": "core",
    "lines": 92
  },
  {
    "id": "quality-protocol",
    "name": "quality-protocol",
    "description": "The unified maximum-quality protocol \u2014 restate \u2192 catalog constraints \u2192 plan \u2192 single-file subsystems \u2192 write-verify \u2192 se",
    "category": "core",
    "lines": 80
  },
  {
    "id": "re-verify-findings",
    "name": "re-verify-findings",
    "description": "Before executing any audit finding, claimed bug, or reported issue, re-verify it against LIVE sources (repo, DB, API, br",
    "category": "core",
    "lines": 79
  },
  {
    "id": "read-before-build",
    "name": "read-before-build",
    "description": "A plan or design document is an aspiration, not a specification. Before writing any code, examine the actual source file",
    "category": "core",
    "lines": 83
  },
  {
    "id": "session-closeout",
    "name": "session-closeout",
    "description": "Before ending a session: reconcile changed files, update docs and changelog, list loose ends, write a handoff note. Appl",
    "category": "core",
    "lines": 70
  },
  {
    "id": "session-distill",
    "name": "session-distill",
    "description": "At session end, auto-summarize what was learned into a structured artifact. Captures decisions made, files changed, open",
    "category": "core",
    "lines": 82
  },
  {
    "id": "show-your-work",
    "name": "show-your-work",
    "description": "After any complex task (audit, plan, redesign, multi-agent execution), output a separate THINKING TRACE section. Documen",
    "category": "core",
    "lines": 77
  },
  {
    "id": "verify-first",
    "name": "verify-first",
    "description": "Every assertion about the codebase, product, or market is a hypothesis. Verify it against live sources before committing",
    "category": "core",
    "lines": 76
  },
  {
    "id": "workflow-decompose",
    "name": "workflow-decompose",
    "description": "Decompose any workflow into a DAG: trigger \u2192 conditions \u2192 actions \u2192 retries \u2192 observability. Mental model for n8n, Tempo",
    "category": "core",
    "lines": 77
  },
  {
    "id": "chrome-devtools-mcp-bridge",
    "name": "chrome-devtools-mcp-bridge",
    "description": "Google's official Chrome DevTools MCP \u2014 26+ tools for browser automation, network inspection, console capture, screensho",
    "category": "optional",
    "lines": 68
  },
  {
    "id": "design-language",
    "name": "design-language",
    "description": "Apply Apple-grade UI polish principles \u2014 restraint, coherence, intention, hierarchy through scale, negative space, motio",
    "category": "optional",
    "lines": 78
  },
  {
    "id": "funnel-pr-guard",
    "name": "funnel-pr-guard",
    "description": "Every PR that touches the front door must state which funnel step it changes and by how much. PR review discipline for l",
    "category": "optional",
    "lines": 85
  },
  {
    "id": "persistent-memory",
    "name": "persistent-memory",
    "description": "Persistent context across sessions for any agent \u2014 captures tool calls, file edits, and decisions; compresses the transc",
    "category": "optional",
    "lines": 63
  },
  {
    "id": "sql-migration-trio",
    "name": "sql-migration-trio",
    "description": "Every SQL migration = three files: up (forward DDL), down (reverse DDL), and schema.sql sync. Apply, drift-check, and ro",
    "category": "optional",
    "lines": 81
  },
  {
    "id": "token-compression",
    "name": "token-compression",
    "description": "Token-compression proxy + MCP server + library that compresses tool outputs, logs, files, and RAG chunks before they con",
    "category": "optional",
    "lines": 53
  }
];

const AGENTS = [
  {
    "id": "af-critic",
    "name": "af-critic",
    "description": "Score a completed task output on correctness, slop, and scope. The judge. Use after /af or any loop result completes.",
    "model": "opus"
  },
  {
    "id": "af-planner",
    "name": "af-planner",
    "description": "Decompose a request into a skill/agent plan. Use when a request is multi-step, ambiguous, or has multiple reasonable app",
    "model": "opus"
  }
];

const SKILL_COUNT = 30;
const AGENT_COUNT = 2;
