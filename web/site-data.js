// Auto-generated from skills/ SKILL.md and agents/ AGENT.md frontmatter.
// DO NOT EDIT. Regenerate via scripts/build-site-data.sh.

const SKILLS = [
  {
    "id": "anti-slop",
    "name": "anti-slop",
    "description": "Kill generic AI patterns before they ship \u2014 filler prose, over-commenting,",
    "category": "core",
    "lines": 52,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "api-design",
    "name": "api-design",
    "description": "Design REST or GraphQL APIs: resource modeling, URL conventions, error",
    "category": "core",
    "lines": 70,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "automation-pick",
    "name": "automation-pick",
    "description": "Before automating a task, decide whether to automate. Decision tree based",
    "category": "core",
    "lines": 63,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "bottleneck-gating",
    "name": "bottleneck-gating",
    "description": "Phase plans by measured bottleneck, not by requested order. Each phase",
    "category": "core",
    "lines": 82,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "constraint-then-solve",
    "name": "constraint-then-solve",
    "description": "Before solving, restate the problem, list unknowns, and catalog every",
    "category": "core",
    "lines": 83,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "context-optimization",
    "name": "context-optimization",
    "description": "Keep tool outputs small, sandbox large files, reference not repeat. Use",
    "category": "core",
    "lines": 55,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "cron-troubleshoot",
    "name": "cron-troubleshoot",
    "description": "Debug a cron job that failed or didn''t run: timezone, drift, overlap,",
    "category": "core",
    "lines": 81,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "e2e-test-strategy",
    "name": "e2e-test-strategy",
    "description": "Plan an end-to-end test pyramid: which flows to E2E, which to integration,",
    "category": "core",
    "lines": 82,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "feedback-loop",
    "name": "feedback-loop",
    "description": "After shipping, set up the loop: instrument \u2192 measure \u2192 review weekly",
    "category": "core",
    "lines": 74,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "knowledge-extract",
    "name": "knowledge-extract",
    "description": "Read a session, conversation, or document and identify reusable patterns.",
    "category": "core",
    "lines": 79,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "landscape-first",
    "name": "landscape-first",
    "description": "Before building anything in a competitive space, research 5-10 competitors:",
    "category": "core",
    "lines": 79,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "measure-first",
    "name": "measure-first",
    "description": "Before planning any change, query live data (DB, API, analytics, logs)",
    "category": "core",
    "lines": 86,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "plan-before-code",
    "name": "plan-before-code",
    "description": "No implementation without an approved spec for non-trivial work. Brainstorm",
    "category": "core",
    "lines": 78,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "plan-then-act",
    "name": "plan-then-act",
    "description": "Plan first, then act. State the plan in one sentence BEFORE any tool",
    "category": "core",
    "lines": 88,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "prompt-discipline",
    "name": "prompt-discipline",
    "description": "Enforce the four coding rules \u2014 think before acting, minimum viable change,",
    "category": "core",
    "lines": 66,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "pushback-when-wrong",
    "name": "pushback-when-wrong",
    "description": "When the brief contradicts verified reality, push back with evidence.",
    "category": "core",
    "lines": 90,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "quality-protocol",
    "name": "quality-protocol",
    "description": "The unified maximum-quality protocol \u2014 restate \u2192 catalog constraints",
    "category": "core",
    "lines": 78,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "re-verify-findings",
    "name": "re-verify-findings",
    "description": "Before executing any audit finding, claimed bug, or reported issue, re-verify",
    "category": "core",
    "lines": 77,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "read-before-build",
    "name": "read-before-build",
    "description": "A plan or design document is an aspiration, not a specification. Before",
    "category": "core",
    "lines": 81,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "session-closeout",
    "name": "session-closeout",
    "description": "Before ending a session: reconcile changed files, update docs and changelog,",
    "category": "core",
    "lines": 68,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "session-distill",
    "name": "session-distill",
    "description": "At session end, auto-summarize what was learned into a structured artifact.",
    "category": "core",
    "lines": 80,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "show-your-work",
    "name": "show-your-work",
    "description": "After any complex task (audit, plan, redesign, multi-agent execution),",
    "category": "core",
    "lines": 75,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "verify-first",
    "name": "verify-first",
    "description": "Every assertion about the codebase, product, or market is a hypothesis.",
    "category": "core",
    "lines": 76,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "workflow-decompose",
    "name": "workflow-decompose",
    "description": "Decompose any workflow into a DAG: trigger \u2192 conditions \u2192 actions \u2192",
    "category": "core",
    "lines": 75,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "chrome-devtools-mcp-bridge",
    "name": "chrome-devtools-mcp-bridge",
    "description": "Google's official Chrome DevTools MCP \u2014 26+ tools for browser automation,",
    "category": "optional",
    "lines": 68,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "design-language",
    "name": "design-language",
    "description": "Apply Apple-grade UI polish principles \u2014 restraint, coherence, intention,",
    "category": "optional",
    "lines": 76,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "funnel-pr-guard",
    "name": "funnel-pr-guard",
    "description": "Every PR that touches the front door must state which funnel step it",
    "category": "optional",
    "lines": 83,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "persistent-memory",
    "name": "persistent-memory",
    "description": "Persistent context across sessions for any agent \u2014 captures tool calls,",
    "category": "optional",
    "lines": 63,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "sql-migration-trio",
    "name": "sql-migration-trio",
    "description": "Every SQL migration = three files: up (forward DDL), down (reverse DDL),",
    "category": "optional",
    "lines": 79,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
  },
  {
    "id": "token-compression",
    "name": "token-compression",
    "description": "Token-compression proxy + MCP server + library that compresses tool outputs,",
    "category": "optional",
    "lines": 53,
    "version": "0.1.0",
    "author": "Agent Foundry Contributors"
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
    "description": "Decompose a request into a skill/agent plan. Use when a request is multi-step, ambiguous, or has multiple reasonable approaches.",
    "model": "opus"
  }
];

const SKILL_COUNT = 30;
const AGENT_COUNT = 2;
