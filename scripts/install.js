#!/usr/bin/env node
/**
 * install.js — Cross-platform installer for Agent Foundry.
 *
 * Node.js >=18. Zero external dependencies. Mirrors the architecture used by
 * ECC and Ruflo: one Node entry point, thin shell wrappers (.sh/.bat/.ps1)
 * delegate to it.
 *
 * Usage:
 *   node scripts/install.js                          # auto-detect harness
 *   node scripts/install.js --harness=claude-code    # explicit target
 *   node scripts/install.js --harness=claude-code --dry-run
 *   node scripts/install.js --manual                 # print instructions
 *   node scripts/install.js --list                   # list all targets
 *
 * Supported targets:
 *   claude-code   - ~/.claude/skills/agent-foundry (link skills)
 *   codex         - ~/.codex/ + per-agent configs (link .codex/)
 *   cursor        - ~/.cursor/rules/ + ~/.cursor/hooks.json
 *   hermes        - ~/AppData/Local/hermes/skills/agent-foundry (link)
 *   gemini-cli    - ~/.gemini/agent-foundry-config/ (link)
 *   opencode      - ~/.config/opencode/ (copy + skills link)
 *
 * Link strategy:
 *   1. fs.symlinkSync (works on macOS/Linux, Windows with admin/dev mode)
 *   2. fs.linkSync hard link (Windows fallback when symlink fails)
 *   3. fs.cpSync recursive copy (universal fallback — ECC's default)
 */

import { existsSync, lstatSync, mkdirSync, rmSync, symlinkSync, linkSync, cpSync,
         readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { homedir, platform, arch } from 'node:os';
import { fileURLToPath } from 'node:url';

// ---------- paths ----------
const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const REPO       = resolve(__dirname, '..');

// ---------- helpers (defined first) ----------
function log(...args) { console.log(...args); }
function vlog(...args) { if (opts.verbose) console.log('  ·', ...args); }
function err(...args) { console.error('  ✗', ...args); }

function home() {
  return process.env.HOME || process.env.USERPROFILE || homedir();
}

function osKind() {
  const p = platform();
  if (p === 'win32') return 'windows';
  if (p === 'darwin') return 'macos';
  return 'linux';
}

function detectHarness() {
  const h = home();
  const candidates = [
    { name: 'claude-code',  path: join(h, '.claude') },
    { name: 'codex',        path: join(h, '.codex') },
    { name: 'cursor',       path: join(h, '.cursor') },
    { name: 'hermes',       path: join(h, 'AppData', 'Local', 'hermes') },
    { name: 'opencode',     path: join(h, '.config', 'opencode') },
    { name: 'antigravity',  path: join(h, '.agent') },
    { name: 'codebuddy',    path: join(h, '.codebuddy') },
    { name: 'joycode',      path: join(h, '.joycode') },
    { name: 'qwen',         path: join(h, '.qwen') },
    { name: 'kimi',         path: join(h, '.kimi') },
    { name: 'openclaw',     path: join(h, '.openclaw') },
    { name: 'zed',          path: join(h, '.zed') },
    { name: 'gemini-cli',   path: join(h, '.gemini') },
  ];
  for (const c of candidates) {
    if (existsSync(c.path)) return c.name;
  }
  return null;
}

/**
 * linkOrCopy — try symlink, then hard link, then copy.
 * Mirrors the bash version's 3-tier fallback.
 */
function linkOrCopy(src, dst, { force = true } = {}) {
  if (!existsSync(src)) {
    err(`source missing: ${src}`);
    return false;
  }
  // Remove existing target if requested
  const dstExists = existsSync(dst) || (() => { try { lstatSync(dst); return true; } catch { return false; } })();
  if (dstExists) {
    if (!force) {
      vlog(`skip (exists): ${dst}`);
      return false;
    }
    try { rmSync(dst, { recursive: true, force: true }); } catch {}
  }

  // Try 1: symlink (works on macOS/Linux, Windows w/ dev mode or admin)
  try {
    const type = statSync(src).isDirectory() ? 'dir' : 'file';
    symlinkSync(resolve(src), dst, type);
    log(`  ✓ linked ${dst}`);
    return true;
  } catch (e) { vlog(`symlink failed: ${e.code}`); }

  // Try 2: hard link (Windows fallback for files; works for dirs only on NTFS)
  try {
    linkSync(resolve(src), dst);
    log(`  ✓ hard-linked ${dst}`);
    return true;
  } catch (e) { vlog(`hard link failed: ${e.code}`); }

  // Try 3: recursive copy (universal fallback — what ECC uses by default)
  try {
    cpSync(resolve(src), dst, { recursive: true, dereference: false });
    log(`  ✓ copied ${dst}`);
    return true;
  } catch (e) {
    err(`copy failed for ${dst}: ${e.message}`);
    return false;
  }
}

function ensureDir(p) {
  mkdirSync(p, { recursive: true });
}

function rmIfExists(p) {
  try { rmSync(p, { recursive: true, force: true }); } catch {}
}

// ---------- harness installers ----------
// Status values:
//   'tested'      — installed and verified on this machine
//   'beta'        — adapter structure defined, install runs but end-to-end not yet tested
//   'coming-soon' — adapter not yet implemented (refuses to install, prints note)
const HARNESSES = {
  'claude-code': {
    label: 'Claude Code',
    status: 'tested',
    install: (dry) => {
      const dst = join(home(), '.claude', 'skills', 'agent-foundry');
      if (dry) { log(`Would link: ${REPO}/skills -> ${dst}`); return true; }
      ensureDir(dirname(dst));
      return linkOrCopy(join(REPO, 'skills'), dst);
    },
  },
  'claude-project': {
    label: 'Claude Code (project-local)',
    status: 'coming-soon',
    install: (dry) => {
      const dst = join(process.cwd(), '.claude', 'skills', 'agent-foundry');
      if (dry) { log(`Would link (project-local): ${REPO}/skills -> ${dst}`); return true; }
      ensureDir(dirname(dst));
      return linkOrCopy(join(REPO, 'skills'), dst);
    },
  },
  'codex': {
    label: 'Codex CLI',
    status: 'tested',
    install: (dry) => {
      const skillsDst   = join(home(), '.codex', 'skills', 'agent-foundry');
      const codexCfgDir = join(home(), '.codex');
      const configDst   = join(codexCfgDir, 'agent-foundry-config');
      if (dry) {
        log(`Would link: ${REPO}/skills -> ${skillsDst}`);
        log(`Would link: ${REPO}/.codex -> ${configDst}`);
        return true;
      }
      ensureDir(dirname(skillsDst));
      linkOrCopy(join(REPO, 'skills'), skillsDst);
      ensureDir(codexCfgDir);
      if (!existsSync(configDst)) {
        linkOrCopy(join(REPO, '.codex'), configDst);
        log('');
        log('To activate in Codex, copy or merge the config:');
        log(`  cp -n "${configDst}/AGENTS.md" "${codexCfgDir}/AGENTS.md"`);
        log(`  cp -n "${configDst}/config.toml" "${codexCfgDir}/config.toml"`);
      }
      return true;
    },
  },
  'cursor': {
    label: 'Cursor',
    status: 'beta',
    install: (dry) => {
      const rulesDst = join(home(), '.cursor', 'rules');
      const hooksDst = join(home(), '.cursor', 'hooks.json');
      const localRulesDir = join(REPO, '.cursor', 'rules');
      const localHooks = join(REPO, '.cursor', 'hooks.json');
      if (dry) {
        log(`Would copy: ${localRulesDir}/*.mdc -> ${rulesDst}`);
        log(`Would copy: ${localHooks} -> ${hooksDst}`);
        return true;
      }
      ensureDir(rulesDst);
      if (existsSync(localRulesDir)) {
        for (const f of readdirSync(localRulesDir)) {
          if (f.endsWith('.mdc')) {
            linkOrCopy(join(localRulesDir, f), join(rulesDst, f));
          }
        }
      }
      if (existsSync(localHooks)) linkOrCopy(localHooks, hooksDst);
      log('Cursor: restart to pick up rules + hooks.');
      return true;
    },
  },
  'hermes': {
    label: 'Hermes',
    status: 'tested',
    install: (dry) => {
      const dst = join(home(), 'AppData', 'Local', 'hermes', 'skills', 'agent-foundry');
      if (dry) { log(`Would link: ${REPO}/skills -> ${dst}`); return true; }
      ensureDir(dirname(dst));
      return linkOrCopy(join(REPO, 'skills'), dst);
    },
  },
  'gemini-cli': {
    label: 'Gemini CLI',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.gemini');
      const dst = join(cfg, 'agent-foundry-config');
      if (dry) { log(`Would link: ${REPO}/.gemini -> ${dst}`); return true; }
      ensureDir(cfg);
      if (!existsSync(dst)) {
        linkOrCopy(join(REPO, '.gemini'), dst);
      }
      log('Gemini CLI has no plugin system. Reference: ' + dst + '/AGENTS.md');
      return true;
    },
  },
  'opencode': {
    label: 'OpenCode',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.config', 'opencode');
      const configDst = join(cfg, 'agent-foundry-config');
      const skillsDst = join(cfg, 'skills', 'agent-foundry');
      if (dry) {
        log(`Would copy: ${REPO}/.opencode -> ${configDst}`);
        log(`Would link: ${REPO}/skills -> ${skillsDst}`);
        return true;
      }
      ensureDir(cfg);
      linkOrCopy(join(REPO, '.opencode'), configDst);
      ensureDir(dirname(skillsDst));
      linkOrCopy(join(REPO, 'skills'), skillsDst);
      log('Merge config if needed: jq -s \".[0] * .[1]\" ' + join(cfg, 'opencode.json') + ' ' + join(configDst, 'opencode.json') + ' > merge.json');
      return true;
    },
  },
  'antigravity': {
    label: 'Antigravity',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.agent');
      const rulesDst = join(cfg, 'rules');
      const skillsDst = join(cfg, 'skills', 'agent-foundry');
      if (dry) {
        log(`Would copy: ${REPO}/.antigravity/rules/*.md -> ${rulesDst}`);
        log(`Would copy: ${REPO}/.antigravity/skills/agent-foundry/ -> ${skillsDst}`);
        log(`Would copy: ${REPO}/.antigravity/workflows/*.md -> ${cfg}/workflows/`);
        return true;
      }
      ensureDir(rulesDst);
      cpSync(join(REPO, '.antigravity', 'rules'), rulesDst, { recursive: true });
      cpSync(join(REPO, '.antigravity', 'skills'), cfg, { recursive: true });
      ensureDir(join(cfg, 'workflows'));
      cpSync(join(REPO, '.antigravity', 'workflows'), join(cfg, 'workflows'), { recursive: true });
      return true;
    },
  },
  'codebuddy': {
    label: 'Codebuddy',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.codebuddy');
      if (dry) {
        log(`Would copy: ${REPO}/.codebuddy/skills/agent-foundry/ -> ${cfg}/skills/`);
        log(`Would copy: ${REPO}/.codebuddy/commands/af.md -> ${cfg}/commands/`);
        return true;
      }
      ensureDir(join(cfg, 'skills'));
      ensureDir(join(cfg, 'commands'));
      cpSync(join(REPO, '.codebuddy', 'skills'), join(cfg, 'skills'), { recursive: true });
      cpSync(join(REPO, '.codebuddy', 'commands'), join(cfg, 'commands'), { recursive: true });
      return true;
    },
  },
  'joycode': {
    label: 'JoyCode',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.joycode');
      if (dry) {
        log(`Would copy: ${REPO}/.joycode/skills/agent-foundry/ -> ${cfg}/skills/`);
        log(`Would copy: ${REPO}/.joycode/commands/af.md -> ${cfg}/commands/`);
        return true;
      }
      ensureDir(join(cfg, 'skills'));
      ensureDir(join(cfg, 'commands'));
      cpSync(join(REPO, '.joycode', 'skills'), join(cfg, 'skills'), { recursive: true });
      cpSync(join(REPO, '.joycode', 'commands'), join(cfg, 'commands'), { recursive: true });
      return true;
    },
  },
  'qwen': {
    label: 'Qwen CLI',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.qwen');
      const skillsDst = join(cfg, 'skills', 'agent-foundry');
      if (dry) {
        log(`Would copy: ${REPO}/.qwen/skills/agent-foundry/ -> ${cfg}/skills/`);
        return true;
      }
      ensureDir(join(cfg, 'skills'));
      cpSync(join(REPO, '.qwen', 'skills'), join(cfg, 'skills'), { recursive: true });
      return true;
    },
  },
  'kimi': {
    label: 'Kimi',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.kimi');
      const skillsDst = join(cfg, 'skills', 'agent-foundry');
      if (dry) {
        log(`Would copy: ${REPO}/.kimi/skills/agent-foundry/ -> ${cfg}/skills/`);
        return true;
      }
      ensureDir(join(cfg, 'skills'));
      cpSync(join(REPO, '.kimi', 'skills'), join(cfg, 'skills'), { recursive: true });
      return true;
    },
  },
  'openclaw': {
    label: 'OpenClaw',
    status: 'beta',
    install: (dry) => {
      const cfg = join(home(), '.openclaw');
      const skillsDst = join(cfg, 'skills', 'agent-foundry');
      if (dry) {
        log(`Would copy: ${REPO}/.openclaw/skills/agent-foundry/ -> ${cfg}/skills/`);
        return true;
      }
      ensureDir(join(cfg, 'skills'));
      cpSync(join(REPO, '.openclaw', 'skills'), join(cfg, 'skills'), { recursive: true });
      return true;
    },
  },
  'zed': {
    label: 'Zed (zquire)',
    status: 'coming-soon',
    install: (dry) => {
      log('');
      log(`  ⚠ zed is marked 'coming-soon'.`);
      log(`    Zed's agent client (zquire) is in beta and lacks a stable plugin API.`);
      log(`    We document the expected layout in .zed/README.md but won't ship a tested`);
      log(`    adapter until upstream stabilizes.`);
      return false;
    },
  },
};

// ---------- CLI parsing ----------
const args = process.argv.slice(2);
const opts = {
  harness: null,
  dryRun: false,
  manual: false,
  list: false,
  verbose: false,
  force: false,
};
for (const a of args) {
  if (a === '--dry-run')           opts.dryRun = true;
  else if (a === '--manual')        opts.manual = true;
  else if (a === '--list')          opts.list = true;
  else if (a === '--verbose' || a === '-v') opts.verbose = true;
  else if (a === '--force' || a === '-f') opts.force = true;
  else if (a.startsWith('--harness=')) opts.harness = a.slice('--harness='.length);
  else if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
  else { console.error(`Unknown arg: ${a}`); printHelp(); process.exit(2); }
}

// ---------- main ----------
function printHelp() {
  const STATUS_BADGE = { 'tested': '✓', 'beta': '◐', 'coming-soon': '○' };
  const list = Object.entries(HARNESSES)
    .map(([k, v]) => `  ${k.padEnd(16)} ${STATUS_BADGE[v.status] || ' '} ${v.label}`)
    .join('\n');
  console.log(`Agent Foundry installer

Usage:
  node scripts/install.js                          auto-detect harness
  node scripts/install.js --harness=<name>          explicit target
  node scripts/install.js --harness=<name> --dry-run
  node scripts/install.js --manual                  show manual instructions
  node scripts/install.js --list                    list supported targets

Options:
  --harness=<name>    Target harness (see list)
  --dry-run           Show what would happen
  --manual            Print manual install instructions
  --list              List supported targets
  --force, -f         Overwrite existing installs
  --verbose, -v       Verbose output
  --help, -h          Show this help

Targets (✓ tested · ◐ beta · ○ coming-soon):
${list}
`);
}

if (opts.list) { printHelp(); process.exit(0); }

if (opts.manual) {
  console.log('Manual install instructions:');
  console.log('');
  console.log('  1. Pick a target from the list (run with --list)');
  console.log('  2. Link or copy this repo into the harness\'s expected location');
  console.log('  3. Restart the harness');
  console.log('');
  console.log('  Example for Claude Code:');
  console.log(`    ln -s "${REPO}/skills" "${home()}/.claude/skills/agent-foundry"`);
  process.exit(0);
}

if (!opts.harness) opts.harness = detectHarness();
if (!opts.harness) {
  err('No harness detected. Pass --harness=<name> or use --list');
  process.exit(1);
}

const installer = HARNESSES[opts.harness];
if (!installer) {
  err(`Unknown harness: ${opts.harness}`);
  console.log('Use --list to see supported targets');
  process.exit(1);
}

log(`Agent Foundry installer — ${osKind()} ${arch()}`);
log(`Target: ${opts.harness} (${installer.label})`);
log(`Repo:   ${REPO}`);
log(`Mode:   ${opts.dryRun ? 'dry-run' : 'install'}`);
log('');

const ok = installer.install(opts.dryRun);

if (ok && !opts.dryRun) {
  log('');
  log('Done. Restart your harness so it picks up the new skills.');
}