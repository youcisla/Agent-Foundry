"""Agent Foundry CLI (Click)."""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from pathlib import Path

import click

from .config import Config, init_config, LOG_DB_PATH
from .indexer import (
    build_index,
    get_index_cached,
    invalidate_cache,
    read_index,
    write_index,
)
from .models import (
    ExecuteRequest,
    LoopRequest,
    PlanRequest,
)


def _ensure_daemon(cfg: Config) -> bool:
    """Best-effort daemon health check (lazy start is run elsewhere)."""
    try:
        import httpx
        url = f"http://127.0.0.1:{cfg.core.daemon_port}/health"
        r = httpx.get(url, timeout=0.5)
        return r.status_code == 200
    except Exception:
        return False


def _start_daemon(cfg: Config) -> bool:
    """Spawn the daemon in background and wait for /health. Returns True if started."""
    import subprocess
    import time as _t
    log_path = Path.home() / ".config" / "agent-foundry" / "daemon.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("ab")
    pid_file = Path.home() / ".config" / "agent-foundry" / "daemon.pid"
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "agent_foundry.cli", "serve",
             "--port", str(cfg.core.daemon_port), "--detach"],
            stdout=log_file, stderr=log_file, start_new_session=True,
        )
        pid_file.write_text(str(proc.pid))
    except Exception:
        return False

    import httpx
    url = f"http://127.0.0.1:{cfg.core.daemon_port}/health"
    for _ in range(50):
        try:
            r = httpx.get(url, timeout=0.5)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        _t.sleep(0.1)
    return False


def _call_or_daemon(cfg: Config, method: str, path: str, payload: dict,
                     timeout: float = 30.0) -> dict:
    """POST/GET via daemon (lazy-start if needed)."""
    import httpx
    base = f"http://127.0.0.1:{cfg.core.daemon_port}"
    if not _ensure_daemon(cfg):
        if not _start_daemon(cfg):
            raise click.ClickException(
                f"Could not start daemon on port {cfg.core.daemon_port}"
            )

    url = f"{base}{path}"
    try:
        if method == "GET":
            r = httpx.get(url, timeout=timeout)
        else:
            r = httpx.post(url, json=payload, timeout=timeout)
    except Exception as e:
        raise click.ClickException(f"HTTP error: {e}")
    if r.status_code not in (200, 400):
        raise click.ClickException(f"Daemon returned {r.status_code}: {r.text[:200]}")
    try:
        return r.json()
    except Exception:
        return {}


@click.group()
@click.option("--config", "config_path", type=click.Path(exists=False),
              default=None, help="Path to config.toml")
@click.pass_context
def cli(ctx, config_path):
    """Agent Foundry — orchestrate skills for Claude Code."""
    ctx.ensure_object(dict)
    if config_path:
        from .config import Config as _Cfg
        cfg = _Cfg.load(Path(config_path))
    else:
        cfg = Config.load()
    ctx.obj["cfg"] = cfg


@cli.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing config")
@click.option("--skills-dir", default=None, help="Override skills directory")
@click.pass_context
def cmd_init(ctx, force, skills_dir):
    """Create config.toml and build the initial skill index."""
    cfg = ctx.obj["cfg"]
    if skills_dir:
        # Config is frozen — derive a new instance with the override
        cfg = dataclasses.replace(
            cfg, core=dataclasses.replace(cfg.core, skills_dir=skills_dir)
        )
    if force or not cfg.config_path.exists():
        cfg.save()
        click.echo(f"Wrote config: {cfg.config_path}")
    else:
        click.echo(f"Config already exists: {cfg.config_path} (use --force to overwrite)")

    skills_dir_path = Path(cfg.core.skills_dir).expanduser()
    skills_dir_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"Skills dir: {skills_dir_path}")
    idx = build_index(skills_dir_path)
    out = Path(cfg.core.index_path).expanduser()
    write_index(idx, out)
    invalidate_cache(out)
    click.echo(f"Indexed {len(idx.skills)} skills (incl. virtual fallback) -> {out}")


@cli.command("index")
@click.pass_context
def cmd_index(ctx):
    """Rebuild the skill index from disk."""
    cfg = ctx.obj["cfg"]
    skills_dir = Path(cfg.core.skills_dir).expanduser()
    if not skills_dir.exists():
        raise click.ClickException(f"skills_dir does not exist: {skills_dir}")
    idx = build_index(skills_dir)
    out = Path(cfg.core.index_path).expanduser()
    write_index(idx, out)
    invalidate_cache(out)
    click.echo(f"Indexed {len(idx.skills)} skills -> {out}")


@cli.command("cost-report")
@click.option("--cheapest", type=int, default=None, help="Top N cheapest")
@click.option("--core", "only_core", is_flag=True)
@click.option("--optional", "only_optional", is_flag=True)
@click.pass_context
def cmd_cost_report(ctx, cheapest, only_core, only_optional):
    """Print a table of every skill with cost estimates."""
    cfg = ctx.obj["cfg"]
    idx = get_index_cached(
        Path(cfg.core.index_path).expanduser(),
        ttl_seconds=cfg.core.index_cache_ttl_seconds,
    )
    if idx is None:
        idx = read_index(Path(cfg.core.index_path).expanduser())
    if idx is None:
        raise click.ClickException("No index. Run `agent-foundry init` first.")

    skills = idx.skills
    if only_core:
        skills = [s for s in skills if s.category == "core"]
    if only_optional:
        skills = [s for s in skills if s.category == "optional"]

    def cost(s):
        c = s.estimated_token_cost or {}
        return int(c.get("input", 0)) + int(c.get("output", 0))

    if cheapest:
        skills = sorted(skills, key=cost)[:cheapest]

    click.echo(f"{'Skill':<32} {'In':>6} {'Out':>6} {'Total':>7} {'Sec':>5}  Cat")
    click.echo(f"{'-'*32} {'-'*6} {'-'*6} {'-'*7} {'-'*5}  {'-'*4}")
    ti = to = tt = 0
    for s in skills:
        c = s.estimated_token_cost or {}
        ii = int(c.get("input", 0))
        oo = int(c.get("output", 0))
        ti += ii; to += oo; tt += ii + oo
        click.echo(f"{s.id:<32} {ii:>6} {oo:>6} {ii+oo:>7} {s.estimated_time_seconds:>5}  {s.category[:1]}")
    click.echo(f"{'-'*32} {'-'*6} {'-'*6} {'-'*7} {'-'*5}")
    click.echo(f"{'TOTAL (' + str(len(skills)) + ')':<32} {ti:>6} {to:>6} {tt:>7}")


@cli.command("plan")
@click.argument("prompt")
@click.option("--max", "max_results", type=int, default=None, help="Top N")
@click.pass_context
def cmd_plan(ctx, prompt, max_results):
    """Rank skills for a prompt."""
    cfg = ctx.obj["cfg"]
    if max_results:
        cfg.planner.max_results = max_results
    payload = {"prompt": prompt, "max_results": cfg.planner.max_results}
    data = _call_or_daemon(cfg, "POST", "/plan", payload)
    results = data.get("results", [])
    if not results:
        click.echo(f"No skills matched. (Total available: {data.get('total_available', 0)})")
        return
    for i, r in enumerate(results, 1):
        c = r.get("estimated_cost", {})
        click.echo(
            f"{i}. {r['skill_id']}  score={r['score']:.3f}  "
            f"cost={c.get('total', 0)} tok  ({c.get('input', 0)}in/{c.get('output', 0)}out)"
        )
        if r.get("matched_patterns"):
            click.echo(f"   matched: {r['matched_patterns']}")


@cli.command("execute")
@click.argument("skill_id")
@click.argument("prompt")
@click.option("--model", default=None)
@click.option("--seed", type=int, default=None, help="Sampling seed forwarded to the provider")
@click.option("--temperature", type=float, default=None)
@click.option("--force", is_flag=True, help="Skip budget confirmation")
@click.pass_context
def cmd_execute(ctx, skill_id, prompt, model, seed, temperature, force):
    """Run a specific skill on a prompt."""
    cfg = ctx.obj["cfg"]
    payload = {"skill_id": skill_id, "prompt": prompt, "force": force,
               "model": model, "seed": seed, "temperature": temperature}
    data = _call_or_daemon(cfg, "POST", "/execute", payload)

    if data.get("requires_confirmation"):
        c = data.get("estimated_cost", {})
        click.echo(
            f"Estimated cost: {c.get('total', 0)} tokens "
            f"(input {c.get('input')}, output {c.get('output')})."
        )
        if force or not sys.stdin.isatty():
            click.echo("Non-TTY or --force set; declining to avoid hanging.")
            return
        if not click.confirm("Proceed? [y/N]", default=False):
            click.echo("Aborted — no tokens spent.")
            return
        payload["force"] = True
        data = _call_or_daemon(cfg, "POST", "/execute", payload)

    click.echo(data.get("output", ""))
    if data.get("error"):
        click.echo(f"\n[error] {data['error']}", err=True)
        sys.exit(1)
    click.echo(
        f"\n[tokens={data.get('tokens_used', 0)}  "
        f"time={data.get('duration_seconds', 0):.2f}s]",
        err=True,
    )


@cli.command("run")
@click.argument("prompt")
@click.option("--model", default=None)
@click.option("--budget", type=int, default=None)
@click.option("--seed", type=int, default=None)
@click.option("--temperature", type=float, default=None)
@click.option("--force", is_flag=True, help="Skip budget confirmation prompt")
@click.option("--judge", is_flag=True, help="Score output via af-critic after execution")
@click.pass_context
def cmd_run(ctx, prompt, model, budget, seed, temperature, force, judge):
    """Plan + execute the top-ranked skill."""
    cfg = ctx.obj["cfg"]
    payload = {"prompt": prompt, "force": force, "model": model,
               "budget": budget, "judge": judge, "seed": seed,
               "temperature": temperature}

    def call(req):
        return _call_or_daemon(cfg, "POST", "/loop", req)

    data = call(payload)
    if data.get("requires_confirmation"):
        c = data.get("estimated_cost", {})
        click.echo(
            f"Estimated cost: {c.get('total', 0)} tokens "
            f"(input {c.get('input')}, output {c.get('output')}, budget "
            f"{budget or cfg.core.token_budget})."
        )
        click.echo(
            f"Selected skill: {data.get('skill_id')} "
            f"(plan: {[p['skill_id'] for p in data.get('plan', [])]})"
        )
        if not force and sys.stdin.isatty() and click.confirm("Proceed? [y/N]", default=False):
            payload["force"] = True
            data = call(payload)
        else:
            if not force and not sys.stdin.isatty():
                click.echo("Non-TTY input; declining without --force.")
            else:
                click.echo("Aborted — no tokens spent.")
            return

    fb = " [FALLBACK]" if data.get("was_fallback") else ""
    plan_skills = [p["skill_id"] for p in data.get("plan", [])]
    click.echo(f"--> Skill: {data.get('skill_id')}{fb}   Plan: {plan_skills}")
    if data.get("session_id"):
        click.echo(f"    session {data['session_id']} — continue with: "
                   f"agent-foundry resume {data['session_id']} \"...\"", err=True)
    click.echo("---")
    click.echo(data.get("output", ""))
    if data.get("error"):
        click.echo(f"\n[error] {data['error']}", err=True)
        sys.exit(1)
    click.echo(
        f"\n[tokens={data.get('tokens_used', 0)}  "
        f"time={data.get('duration_seconds', 0):.2f}s]",
        err=True,
    )
    if data.get("judged") and data.get("judge_score"):
        click.echo(f"\nJudge (af-critic): {json.dumps(data['judge_score'], indent=2)}",
                   err=True)


@cli.command("resume")
@click.argument("session_id", type=int)
@click.argument("prompt")
@click.option("--model", default=None)
@click.option("--seed", type=int, default=None)
@click.option("--temperature", type=float, default=None)
@click.pass_context
def cmd_resume(ctx, session_id, prompt, model, seed, temperature):
    """Continue a loop session with a follow-up prompt."""
    cfg = ctx.obj["cfg"]
    data = _call_or_daemon(
        cfg, "POST", "/loop/resume",
        {"session_id": session_id, "prompt": prompt, "model": model,
         "seed": seed, "temperature": temperature},
        timeout=max(60.0, float(cfg.core.executor_timeout_seconds) + 15.0),
    )
    click.echo(f"--> Session: {data.get('session_id')}  Skill: {data.get('skill_id')}")
    click.echo("---")
    click.echo(data.get("output", ""))
    if data.get("error"):
        click.echo(f"\n[error] {data['error']}", err=True)
        sys.exit(1)
    click.echo(
        f"\n[tokens={data.get('tokens_used', 0)}  "
        f"time={data.get('duration_seconds', 0):.2f}s  "
        f"cost=${data.get('cost_usd', 0.0):.6f}]",
        err=True,
    )


@cli.command("session")
@click.argument("session_id", type=int)
@click.pass_context
def cmd_session(ctx, session_id):
    """Show a stored loop session."""
    cfg = ctx.obj["cfg"]
    data = _call_or_daemon(cfg, "GET", f"/loop/{session_id}", {})
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@cli.command("doctor")
@click.pass_context
def cmd_doctor(ctx):
    """Health-check: config, index, daemon, API key."""
    cfg = ctx.obj.get("cfg") if ctx.obj else None
    if cfg is None:
        import agent_foundry.config as _cfg
        cfg = _cfg.Config.load()
    ok = True
    click.echo("=== Agent Foundry Doctor ===")
    if cfg.config_path.exists():
        click.echo(f"[PASS] Config: {cfg.config_path}")
    else:
        click.echo(f"[FAIL] Config not found: {cfg.config_path}")
        ok = False
    idx_path = cfg.core.index_path
    if os.path.exists(str(idx_path)):
        click.echo(f"[PASS] Index: {idx_path}")
        from .indexer import read_index
        idx = read_index(Path(idx_path).expanduser())
        if idx:
            real = [s for s in idx.skills if not s.is_fallback]
            click.echo(f"[PASS] Skills indexed: {len(real)}")
        else:
            click.echo("[FAIL] Index unreadable")
            ok = False
    else:
        click.echo(f"[WARN] Index not found: {idx_path} (run init)")
    from .logging_db import get_skill_weights
    weights = get_skill_weights(LOG_DB_PATH)
    if weights:
        click.echo(f"[PASS] Learned skill weights: {len(weights)}")
    graph = Path(__file__).resolve().parent.parent / "web" / "graph-stats.js"
    if graph.exists():
        click.echo(f"[PASS] Knowledge graph stats: {graph.name}")
    else:
        click.echo("[WARN] Knowledge graph stats missing (run graphify)")
    import httpx
    try:
        r = httpx.get(f"http://127.0.0.1:{cfg.core.daemon_port}/health", timeout=2)
        click.echo(f"[PASS] Daemon reachable at port {cfg.core.daemon_port}")
    except Exception:
        click.echo(f"[WARN] Daemon not reachable (lazy-start on next command)")
    import os as _os
    ak = _os.environ.get("ANTHROPIC_API_KEY", _os.environ.get("OPENAI_API_KEY", ""))
    if ak:
        click.echo(f"[PASS] API key set ({ak[:8]}...)")
    else:
        click.echo(f"[FAIL] No API key set (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
        ok = False
    if ok:
        click.echo("\nResult: All checks passed.")
    else:
        click.echo("\nResult: Some checks failed — see above.")

@cli.command("status")
@click.option("--markdown", is_flag=True, help="Output in portable markdown")
@click.pass_context
def cmd_status(ctx, markdown):
    """Show orchestrator status: routing accuracy, fallback rate."""
    from .logging_db import LOG_DB_PATH, get_stats
    cfg = ctx.obj.get("cfg") if ctx.obj else None
    if cfg is None:
        import agent_foundry.config as _cfg
        cfg = _cfg.Config.load()
    db_path = LOG_DB_PATH
    stats = get_stats(db_path)
    if markdown:
        click.echo("## Agent Foundry Status\n")
        click.echo(f"| Metric | Value |\n|--------|-------|")
        for k, v in stats.items():
            click.echo(f"| {k} | {v} |")
    else:
        click.echo("=== Agent Foundry Status ===")
        for k, v in stats.items():
            click.echo(f"  {k}: {v}")

@cli.command("consult")
@click.argument("need")
@click.pass_context
def cmd_consult(ctx, need):
    """Recommend components to install or enable for a need."""
    from agent_foundry.planner import plan
    from agent_foundry.config import Config
    from agent_foundry.indexer import read_index
    from agent_foundry.models import PlanRequest
    from pathlib import Path

    cfg = ctx.obj.get("cfg") if ctx.obj else None
    if cfg is None:
        cfg = Config.load()
    idx = read_index(Path(cfg.core.index_path).expanduser())
    if not idx:
        click.echo("No index found. Run 'init' first.", err=True)
        return
    req = PlanRequest(prompt=need)
    resp = plan(req, idx, cfg.planner)
    click.echo(f"Components recommended for: {need}\n")
    for r in resp.results[:5]:
        click.echo(f"  {r.skill_id}  (score {r.score})")
        click.echo(f"    {r.description[:100]}")
    click.echo(f"\nTo install: agent-foundry install {r.skill_id} (TODO)")


@cli.command("serve")

@click.option("--port", type=int, default=None, help="Override daemon port")
@click.option("--host", default="127.0.0.1", help="Bind host")
@click.option("--detach", is_flag=True, help="Detach mode (used by lazy-start)")
@click.pass_context
def cmd_serve(ctx, port, host, detach):
    """Run the daemon (foreground by default)."""
    import uvicorn

    cfg = ctx.obj.get("cfg") if ctx.obj else None
    if cfg is None:
        cfg = Config.load()
    if port:
        # Config is frozen — derive a new instance with the override
        cfg = dataclasses.replace(
            cfg, core=dataclasses.replace(cfg.core, daemon_port=port)
        )

    from .daemon import create_app
    app = create_app(cfg)

    if detach:
        config = uvicorn.Config(
            app, host=host, port=cfg.core.daemon_port, log_level="warning"
        )
        server = uvicorn.Server(config)
        server.run()
    else:
        click.echo(
            f"Agent Foundry daemon listening on http://{host}:{cfg.core.daemon_port}"
        )
        uvicorn.run(app, host=host, port=cfg.core.daemon_port)


@cli.command("rejudge")
@click.argument("execution_id", type=int)
@click.option("--model", default=None, help="Judge model override")
@click.pass_context
def cmd_rejudge(ctx, execution_id, model):
    """Re-score a stored execution without re-running the completion."""
    cfg = ctx.obj["cfg"]
    from .logging_db import get_execution, update_execution_judge
    from .judge import judge_output
    from .spill import read_output

    row = get_execution(LOG_DB_PATH, execution_id)
    if row is None:
        raise click.ClickException(f"execution not found: {execution_id}")
    text = read_output(row.get("output_ref")) or row.get("output") or ""
    if not text:
        raise click.ClickException("execution has no stored output to judge")
    idx = read_index(Path(cfg.core.index_path).expanduser())
    skill_paths = idx.skill_paths if idx else {}
    result = judge_output(
        task=row.get("prompt") or "",
        output=text,
        model=model or cfg.core.default_llm,
        skill_paths=skill_paths,
        fallback_prompt=cfg.fallback_system_prompt,
        timeout_seconds=cfg.core.judge_timeout_seconds,
        retries=cfg.core.judge_retries,
    )
    update_execution_judge(
        LOG_DB_PATH, execution_id, scores=result.scores,
        status=result.status, model=result.model,
    )
    click.echo(json.dumps({
        "execution_id": execution_id,
        "judge_status": result.status,
        "scores": result.scores,
        "error": result.error,
    }, indent=2, ensure_ascii=False))
    if not result.ok:
        ctx.exit(1)


@cli.command("prune")
@click.option("--older-than-days", type=int, required=True,
              help="Delete rows older than this many days")
@click.option("--executions-days", type=int, default=None)
@click.option("--observations-days", type=int, default=None)
@click.option("--policy-days", type=int, default=None)
@click.option("--perf-days", type=int, default=None)
@click.option("--dry-run", is_flag=True, help="Report counts without deleting")
@click.option("--yes", is_flag=True, help="Skip the confirmation prompt")
@click.pass_context
def cmd_prune(ctx, older_than_days, executions_days, observations_days,
              policy_days, perf_days, dry_run, yes):
    """Delete old executions, observations, policy decisions, and perf stats."""
    from .logging_db import prune_db
    if older_than_days <= 0:
        raise click.ClickException("--older-than-days must be > 0")
    class_days = {
        key: value for key, value in {
            "executions": executions_days,
            "observations": observations_days,
            "policy_decisions": policy_days,
            "perf_stats": perf_days,
        }.items() if value is not None
    }
    if not dry_run and not yes:
        if not sys.stdin.isatty():
            raise click.ClickException("non-interactive prune requires --yes")
        if not click.confirm(
            f"Delete rows older than {older_than_days} days from {LOG_DB_PATH}?",
            default=False,
        ):
            click.echo("Aborted — nothing deleted.")
            return
    counts = prune_db(LOG_DB_PATH, older_than_days=older_than_days,
                      dry_run=dry_run, class_days=class_days)
    click.echo(json.dumps({"dry_run": dry_run, "counts": counts}, indent=2))


@cli.command("calibrate")
@click.option("--bins", type=int, default=5, show_default=True)
@click.pass_context
def cmd_calibrate(ctx, bins):
    """Compare stored judge scores with human feedback."""
    from .calibration import calibration_report
    report = calibration_report(LOG_DB_PATH, bins=max(1, bins))
    click.echo(json.dumps(report, indent=2))


@cli.command("feedback")
@click.argument("execution_id", type=int)
@click.argument("score", type=int)
@click.pass_context
def cmd_feedback(ctx, execution_id, score):
    """Rate an execution: 1 = thumbs_up, -1 = thumbs_down."""
    if score not in (1, -1):
        click.echo("Score must be 1 (up) or -1 (down)", err=True)
        ctx.exit(1)
    from .logging_db import set_feedback, LOG_DB_PATH
    ok = set_feedback(LOG_DB_PATH, execution_id, score)
    click.echo("✓ Feedback recorded" if ok else "✗ Execution not found")


@cli.command("learn")
@click.option("--scope", type=click.Choice(["project", "global"]), default=None,
              help="Use the observation ledger with this scope")
@click.option("--project-id", default=None, help="Override the project key")
@click.pass_context
def cmd_learn(ctx, scope, project_id):
    """Analyze execution log and generate trigger-pattern instincts."""
    from .logging_db import learn, learn_scoped, LOG_DB_PATH
    if scope:
        result = learn_scoped(LOG_DB_PATH, scope=scope, project_id=project_id)
        click.echo(f"Scope: {result['scope']} ({result.get('project_id') or 'all projects'})")
    else:
        result = learn(LOG_DB_PATH)
    click.echo(f"New instincts: {result['new_instincts']}")
    click.echo(f"Updated: {result['updated_instincts']}")
    click.echo(f"Skill weights updated: {result.get('weights_updated', 0)}")
    for p in result["patterns_found"]:
        click.echo(f"  {p['skill']} → \"{p['pattern']}\"")


@cli.command("instincts")
@click.option("--approved", is_flag=True, help="Show approved only")
@click.option("--explain", "explain_id", type=int, default=None,
              help="Show supporting observations for one instinct")
@click.option("--proposals", is_flag=True, help="Cluster instincts into reviewable proposals")
@click.pass_context
def cmd_instincts(ctx, approved, explain_id, proposals):
    """List learned trigger-pattern instincts."""
    from .logging_db import (
        LOG_DB_PATH,
        cluster_instincts,
        explain_instinct,
        list_instincts,
        write_proposals,
    )
    if explain_id is not None:
        detail = explain_instinct(LOG_DB_PATH, explain_id)
        if detail is None:
            raise click.ClickException(f"instinct not found: {explain_id}")
        click.echo(json.dumps(detail, indent=2, ensure_ascii=False))
        return
    if proposals:
        groups = cluster_instincts(LOG_DB_PATH)
        out_dir = Path.home() / ".config" / "agent-foundry" / "proposals"
        paths = write_proposals(groups, out_dir)
        click.echo(f"Proposals: {len(paths)}")
        for path in paths:
            click.echo(f"  {path}")
        return
    for inst in list_instincts(LOG_DB_PATH, approved_only=approved):
        flag = "✓" if inst["approved"] else "○"
        scope = inst.get("scope") or "global"
        click.echo(f"  {flag} #{inst['id']} [{inst['skill']}] \"{inst['pattern']}\" "
                   f"conf={inst['confidence']:.2f} ({inst['samples']} samples, "
                   f"{inst.get('successes', 0)}+/{inst.get('failures', 0)}-, {scope})")


@cli.command("instinct-approve")
@click.argument("instinct_id", type=int)
@click.pass_context
def cmd_instinct_approve(ctx, instinct_id):
    """Approve a suggested instinct."""
    from .logging_db import approve_instinct, LOG_DB_PATH
    ok = approve_instinct(LOG_DB_PATH, instinct_id)
    click.echo("✓ Approved" if ok else "✗ Not found")


@cli.command("attest")
@click.option("--root", type=click.Path(), default=None,
              help="Installed skills root (default: cfg.core.skills_dir)")
@click.pass_context
def cmd_attest(ctx, root):
    """Sign the installed skill manifest with a local key."""
    from .attest import MANIFEST_NAME, attest_root
    cfg = ctx.obj["cfg"]
    root_path = Path(root).expanduser() if root else Path(cfg.core.skills_dir).expanduser()
    manifest = root_path / MANIFEST_NAME
    result = attest_root(root_path, manifest,
                         Path(cfg.core.attest_key_path).expanduser())
    click.echo(f"attested {len(result['entries'])} skills -> {manifest}")


@cli.command("verify")
@click.option("--root", type=click.Path(), default=None,
              help="Installed skills root (default: cfg.core.skills_dir)")
@click.option("--strict", is_flag=True,
              help="Fail on missing or unsigned skills as well as tampering")
@click.option("--json", "as_json", is_flag=True, help="Machine-readable output")
@click.pass_context
def cmd_verify(ctx, root, strict, as_json):
    """Verify the installed manifest, signature, and skill hashes."""
    from .attest import MANIFEST_NAME, verify_manifest
    cfg = ctx.obj["cfg"]
    root_path = Path(root).expanduser() if root else Path(cfg.core.skills_dir).expanduser()
    result = verify_manifest(
        root_path / MANIFEST_NAME,
        Path(cfg.core.attest_key_path).expanduser(),
        root=root_path,
    )
    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo(f"checked: {result.checked}")
        for label, values in (("missing", result.missing),
                              ("mismatched", result.mismatched),
                              ("unsigned", result.unsigned),
                              ("errors", result.errors)):
            if values:
                click.echo(f"{label}: {', '.join(map(str, values))}")
        click.echo("ok" if result.ok else "not ok")

    hard_fail = bool(result.errors or result.mismatched)
    if strict:
        hard_fail = hard_fail or bool(result.missing or result.unsigned)
    if hard_fail:
        sys.exit(1)


@cli.command("gate")
@click.option("--kind", type=click.Choice(["shell", "file_write", "text", "network"]),
              default="shell")
@click.option("--value", default=None, help="Action value (command, path, or URL)")
@click.option("--text", default=None, help="Text to scan instead of --value")
@click.option("--direction", type=click.Choice(["inbound", "outbound"]), default="inbound")
@click.option("--workspace", default=".", help="Workspace root for file_write checks")
@click.option("--json", "as_json", is_flag=True, help="Machine-readable output")
def cmd_gate(kind, value, text, direction, workspace, as_json):
    """Classify one action against the local policy rules."""
    from .policy import PolicyAction, evaluate
    if text is not None:
        action = PolicyAction("text", text, {"direction": direction})
    elif value is not None:
        action = PolicyAction(kind, value, {"workspace": workspace})
    else:
        raise click.ClickException("--value or --text is required")
    decision = evaluate(action)
    if as_json:
        click.echo(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
    else:
        click.echo(f"{decision.decision}: {decision.rule_id or 'no-rule'} "
                   f"({decision.reason})")
    sys.exit({"allow": 0, "confirm": 2, "deny": 1}[decision.decision])


@cli.command("mcp")
@click.pass_context
def cmd_mcp(ctx):
    """Run the MCP stdio server (ten tools; see `agent_foundry.mcp_server`)."""
    from .mcp_server import run_stdio
    run_stdio(ctx.obj.get("cfg"))


@cli.command("browse")
@click.option("--search", default="", help="Filter by id, name, description, or tag")
@click.option("--read", "read_id", default=None, help="Print one skill's SKILL.md")
@click.pass_context
def cmd_browse(ctx, search, read_id):
    """Browse the skill catalog without leaving the terminal."""
    cfg = ctx.obj.get("cfg")
    idx = read_index(Path(cfg.core.index_path).expanduser())
    if idx is None:
        raise click.ClickException("No index. Run `agent-foundry index` first.")

    if read_id:
        path = idx.skill_paths.get(read_id)
        if not path or path.startswith("__virtual__:"):
            raise click.ClickException(f"Unknown skill: {read_id}")
        click.echo(Path(path).read_text(encoding="utf-8"))
        return

    q = search.lower().strip()
    shown = 0
    for s in idx.skills:
        if s.is_fallback:
            continue
        haystack = " ".join([s.id, s.name, s.description, " ".join(s.tags)]).lower()
        if q and q not in haystack:
            continue
        click.echo(f"{s.id:<28} [{s.category:<8}] {s.description[:90]}")
        shown += 1
    click.echo(f"\n{shown} skill(s). Use --read <id> to print one.")


@cli.command("eval")
@click.option("--tasks", "tasks_path", required=True, type=click.Path(exists=True),
              help="JSON task file: [{id,prompt,skill,verify}]")
@click.option("--model", default=None)
@click.option("--json", "as_json", is_flag=True, help="Print raw JSON result")
@click.option("--allow-shell", is_flag=True,
              help="Run verifier commands with shell syntax; only for trusted task files")
@click.pass_context
def cmd_eval(ctx, tasks_path, model, as_json, allow_shell):
    """Run a paired skill eval (with vs without skill) and report lift."""
    from .eval import run_eval
    cfg = ctx.obj.get("cfg")
    result = run_eval(Path(tasks_path), cfg=cfg, model=model, db_path=LOG_DB_PATH,
                      allow_shell=allow_shell)
    if as_json:
        click.echo(json.dumps(result, indent=2))
        return
    for t in result["tasks"]:
        click.echo(
            f"{t['id']:<30} with={t['with_skill_pass']} without={t['no_skill_pass']}"
        )
    click.echo(
        f"\nscored={result['scored']}  with={result['with_skill_pass_rate']}  "
        f"without={result['no_skill_pass_rate']}  lift={result['skill_lift']}  "
        f"cost=${result['total_cost_usd']}"
    )


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
