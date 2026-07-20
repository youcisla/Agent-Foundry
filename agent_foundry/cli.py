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
@click.option("--force", is_flag=True, help="Skip budget confirmation")
@click.pass_context
def cmd_execute(ctx, skill_id, prompt, model, force):
    """Run a specific skill on a prompt."""
    cfg = ctx.obj["cfg"]
    payload = {"skill_id": skill_id, "prompt": prompt, "force": force, "model": model}
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
@click.option("--force", is_flag=True, help="Skip budget confirmation prompt")
@click.option("--judge", is_flag=True, help="Score output via af-critic after execution")
@click.pass_context
def cmd_run(ctx, prompt, model, budget, force, judge):
    """Plan + execute the top-ranked skill."""
    cfg = ctx.obj["cfg"]
    payload = {"prompt": prompt, "force": force, "model": model,
               "budget": budget, "judge": judge}

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
    else:
        click.echo(f"[WARN] Index not found: {idx_path} (run init)")
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
    from .logging_db import get_stats
    cfg = ctx.obj.get("cfg") if ctx.obj else None
    if cfg is None:
        import agent_foundry.config as _cfg
        cfg = _cfg.Config.load()
    db_path = cfg.log_path
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
@click.pass_context
def cmd_learn(ctx):
    """Analyze execution log and generate trigger-pattern instincts."""
    from .logging_db import learn, LOG_DB_PATH
    result = learn(LOG_DB_PATH)
    click.echo(f"New instincts: {result['new_instincts']}")
    click.echo(f"Updated: {result['updated_instincts']}")
    for p in result["patterns_found"]:
        click.echo(f"  {p['skill']} → \"{p['pattern']}\"")


@cli.command("instincts")
@click.option("--approved", is_flag=True, help="Show approved only")
@click.pass_context
def cmd_instincts(ctx, approved):
    """List learned trigger-pattern instincts."""
    from .logging_db import list_instincts, LOG_DB_PATH
    for inst in list_instincts(LOG_DB_PATH, approved_only=approved):
        flag = "✓" if inst["approved"] else "○"
        click.echo(f"  {flag} #{inst['id']} [{inst['skill']}] \"{inst['pattern']}\" conf={inst['confidence']:.2f} ({inst['samples']} samples)")


@cli.command("instinct-approve")
@click.argument("instinct_id", type=int)
@click.pass_context
def cmd_instinct_approve(ctx, instinct_id):
    """Approve a suggested instinct."""
    from .logging_db import approve_instinct, LOG_DB_PATH
    ok = approve_instinct(LOG_DB_PATH, instinct_id)
    click.echo("✓ Approved" if ok else "✗ Not found")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
