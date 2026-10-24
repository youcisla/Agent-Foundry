#!/usr/bin/env node
/**
 * install.js â€” Cross-platform installer for Agent Foundry.
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
 *   node scripts/install.js --harness=zed --copy     # portable copy
 *
 * Every target gets each skill as a direct child of its documented skills
 * root. Run --list for the current targets; docs/harness-compatibility.md
 * has the path matrix and dos/don'ts.
 *
 * Link strategy:
 *   1. directory symlink (junction on Windows, no admin rights needed)
 *   2. hard link for files on Windows
 *   3. recursive copy
 */

import { existsSync, lstatSync, mkdirSync, rmSync, symlinkSync, linkSync, cpSync,
         readdirSync, statSync, copyFileSync, readFileSync, writeFileSync,
         realpathSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { basename, dirname, join, resolve, sep } from 'node:path';
import { homedir, platform, arch } from 'node:os';
import { fileURLToPath } from 'node:url';

// ---------- paths ----------
const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const REPO       = resolve(__dirname, '..');

// ---------- helpers (defined first) ----------
function log(...args) { console.log(...args); }
function vlog(...args) { if (opts.verbose) console.log('  Â·', ...args); }
function err(...args) { console.error('  âœ—', ...args); }

function home() {
  return process.env.HOME || process.env.USERPROFILE || homedir();
}

function osKind() {
  const p = platform();
  if (p === 'win32') return 'windows';
  if (p === 'darwin') return 'macos';
  return 'linux';
}

function firstExisting(...paths) {
  return paths.find((p) => existsSync(p)) || paths[0];
}

function hermesRoot() {
  return firstExisting(
    join(home(), '.hermes'),
    join(home(), 'AppData', 'Local', 'hermes'),
  );
}

function kimiRoot() {
  return firstExisting(join(home(), '.kimi-code'), join(home(), '.kimi'));
}

function zedConfigRoot() {
  if (platform() === 'win32') {
    return join(process.env.APPDATA || join(home(), 'AppData', 'Roaming'), 'Zed');
  }
  return join(home(), '.config', 'zed');
}

function detectHarness() {
  const h = home();
  const candidates = [
    { name: 'claude-code',  path: join(h, '.claude') },
    { name: 'codex',        path: join(h, '.codex') },
    { name: 'cursor',       path: join(h, '.cursor') },
    { name: 'hermes',       path: join(h, '.hermes') },
    { name: 'hermes',       path: join(h, 'AppData', 'Local', 'hermes') },
    { name: 'opencode',     path: join(h, '.config', 'opencode') },
    { name: 'antigravity',  path: join(h, '.gemini', 'config') },
    { name: 'codebuddy',    path: join(h, '.codebuddy') },
    { name: 'joycode',      path: join(h, '.joycode') },
    { name: 'qwen',         path: join(h, '.qwen') },
    { name: 'kimi',         path: join(h, '.kimi-code') },
    { name: 'kimi',         path: join(h, '.kimi') },
    { name: 'openclaw',     path: join(h, '.openclaw') },
    { name: 'zed',          path: zedConfigRoot() },
    { name: 'gemini-cli',   path: join(h, '.gemini') },
  ];
  for (const c of candidates) {
    if (existsSync(c.path)) return c.name;
  }
  return null;
}

/**
 * linkOrCopy â€” try symlink, then hard link, then copy.
 * Mirrors the bash version's 3-tier fallback.
 */
function linkOrCopy(src, dst, { force = true, copy = false } = {}) {
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

  if (copy) {
    try {
      cpSync(resolve(src), dst, { recursive: true, dereference: false });
      log(`  âœ“ copied ${dst}`);
      return true;
    } catch (e) {
      err(`copy failed for ${dst}: ${e.message}`);
      return false;
    }
  }

  // Try 1: symlink. Windows directory junctions need no admin rights;
  // file symlinks do, so files fall through to hard links below.
  try {
    const isDir = statSync(src).isDirectory();
    const type = isDir ? (platform() === 'win32' ? 'junction' : 'dir') : 'file';
    symlinkSync(resolve(src), dst, type);
    log(`  âœ“ linked ${dst}`);
    return true;
  } catch (e) { vlog(`symlink failed: ${e.code}`); }

  // Try 2: hard link (works for files on NTFS; not directories)
  try {
    linkSync(resolve(src), dst);
    log(`  âœ“ hard-linked ${dst}`);
    return true;
  } catch (e) { vlog(`hard link failed: ${e.code}`); }

  // Try 3: recursive copy
  try {
    cpSync(resolve(src), dst, { recursive: true, dereference: false });
    log(`  âœ“ copied ${dst}`);
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

// ---------- skill discovery ----------
// Harnesses scan skills as direct children of a skills root. The repo keeps
// them grouped under core/ and optional/, so every adapter installs one link
// per skill instead of linking the grouped tree.
const SKILL_ROOTS = [join(REPO, 'skills', 'core'), join(REPO, 'skills', 'optional')];
const MANAGED_MARKER = '.agent-foundry-installed.json';

function sha256File(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function frontmatterSha256(path) {
  const text = readFileSync(path, 'utf8')
    .replace(/^ï»¿/, '')
    .replace(/\r\n?/g, '\n');
  if (!text.startsWith('---\n')) {
    return createHash('sha256').update('').digest('hex');
  }
  const end = text.indexOf('\n---', 4);
  const body = end === -1 ? '' : text.slice(4, end);
  return createHash('sha256').update(body).digest('hex');
}

function skillSources() {
  const sources = [];
  for (const root of SKILL_ROOTS) {
    if (!existsSync(root)) continue;
    for (const entry of readdirSync(root, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = join(root, entry.name);
      if (existsSync(join(dir, 'SKILL.md'))) sources.push(dir);
    }
  }
  return sources.sort((a, b) => basename(a).localeCompare(basename(b)));
}

function insideRepo(p) {
  try {
    return realpathSync(p).startsWith(realpathSync(REPO) + sep);
  } catch {
    return false;
  }
}

function readManaged(target) {
  try {
    const data = JSON.parse(readFileSync(join(target, MANAGED_MARKER), 'utf8'));
    return Array.isArray(data.skills) ? data.skills : [];
  } catch {
    return [];
  }
}

function writeManaged(target, skills, entries = []) {
  writeFileSync(join(target, MANAGED_MARKER), JSON.stringify({
    package: '@youcisla/agent-foundry',
    repo: REPO,
    mode: opts.copy ? 'copy' : 'link',
    manifest_version: 2,
    generated_at: new Date().toISOString(),
    skills,
    entries,
  }, null, 2) + '\n');
}

/**
 * Install every skill as a direct child of `root`.
 * A manifest records what this installer created: re-runs replace only those
 * entries, so user-authored skills with the same name are never deleted.
 */
function installSkills(root, dry, { group = '', label = '' } = {}) {
  const target = group ? join(root, group) : root;
  const sources = skillSources();
  const names = sources.map((s) => basename(s));
  const previous = readManaged(target);

  if (dry) {
    log(`Would ${opts.copy ? 'copy' : 'link'} ${sources.length} skills -> ${target}`);
    return true;
  }

  ensureDir(target);

  // Drop entries this installer owned that no longer exist upstream.
  for (const stale of previous) {
    if (!names.includes(stale)) {
      const p = join(target, stale);
      if (existsSync(p) || (() => { try { lstatSync(p); return true; } catch { return false; } })()) {
        rmIfExists(p);
        vlog(`removed stale skill: ${stale}`);
      }
    }
  }

  let installed = 0;
  const managed = [];
  const entries = [];
  for (const src of sources) {
    const name = basename(src);
    const dst = join(target, name);
    const exists = existsSync(dst) || (() => { try { lstatSync(dst); return true; } catch { return false; } })();

    if (exists) {
      const owned = previous.includes(name) || insideRepo(dst);
      if (!owned) {
        log(`  ! skipped ${name}: unmanaged skill already exists at ${dst}`);
        continue;
      }
      rmIfExists(dst);
    }

    if (linkOrCopy(src, dst, { force: false, copy: opts.copy })) {
      installed++;
      managed.push(name);
      const skillMd = join(src, 'SKILL.md');
      entries.push({
        name,
        sha256: sha256File(skillMd),
        frontmatter_sha256: frontmatterSha256(skillMd),
        installed_at: new Date().toISOString(),
      });
    }
  }

  writeManaged(target, managed, entries);
  log(`  ${installed}/${sources.length} skills ${opts.copy ? 'copied' : 'linked'}${label ? ` for ${label}` : ''}`);
  return installed === sources.length;
}

function copyTree(src, dst, dry, label = '') {
  if (!existsSync(src)) {
    vlog(`(no ${label || src} â€” skipping)`);
    return true;
  }
  if (dry) {
    log(`Would copy: ${src} -> ${dst}`);
    return true;
  }
  ensureDir(dst);
  try {
    cpSync(src, dst, { recursive: true, force: true });
    log(`  âœ“ copied ${label || dst}`);
    return true;
  } catch (e) {
    err(`copy failed for ${dst}: ${e.message}`);
    return false;
  }
}

function copyFileIfMissing(src, dst, dry) {
  if (!existsSync(src) || existsSync(dst)) return true;
  if (dry) {
    log(`Would copy: ${src} -> ${dst} (only if missing)`);
    return true;
  }
  ensureDir(dirname(dst));
  copyFileSync(src, dst);
  log(`  âœ“ copied ${dst}`);
  return true;
}

const SHARED_SKILLS = () => join(home(), '.agents', 'skills');
// Dedicated root for the CLI indexer, so `agent-foundry plan` ranks only
// Agent Foundry skills instead of every third-party skill in a harness root.
const INDEX_SKILLS = () => join(home(), '.config', 'agent-foundry', 'skills');

function pkgVersion() {
  try {
    return JSON.parse(readFileSync(join(REPO, 'package.json'), 'utf8')).version;
  } catch {
    return '0.0.0';
  }
}

function copyFiles(srcDir, dstDir, dry, { ext = null, label = '' } = {}) {
  if (!existsSync(srcDir)) return true;
  const files = readdirSync(srcDir).filter((f) => !ext || f.endsWith(ext));
  if (dry) {
    log(`Would copy: ${srcDir}/${ext ? '*' + ext : '*'} -> ${dstDir}`);
    return true;
  }
  ensureDir(dstDir);
  for (const f of files) {
    copyFileSync(join(srcDir, f), join(dstDir, f));
  }
  if (files.length) log(`  âœ“ copied ${files.length} ${label || 'file(s)'} -> ${dstDir}`);
  return true;
}

// ---------- harness installers ----------
// Status values:
//   'tested'      â€” installer + indexer smoke test passes; 41 skills land at the documented root
//   'coming-soon' â€” adapter not yet implemented (refuses to install, prints note)
const HARNESSES = {
  'claude-code': {
    label: 'Claude Code',
    status: 'tested',
    install: (dry) => {
      // Claude Code scans only direct children of ~/.claude/skills.
      const root = join(home(), '.claude', 'skills');
      return installSkills(root, dry, { label: 'Claude Code' });
    },
  },
  'claude-project': {
    label: 'Claude Code (project-local)',
    status: 'tested',
    install: (dry) => {
      const root = join(process.cwd(), '.claude', 'skills');
      return installSkills(root, dry, { label: 'this project' });
    },
  },
  'codex': {
    label: 'Codex CLI',
    status: 'tested',
    install: (dry) => {
      // Current Codex scans .agents/skills at every repo level plus
      // $HOME/.agents/skills. ~/.codex/skills is legacy.
      const ok = installSkills(SHARED_SKILLS(), dry, { label: 'Codex' });
      copyFileIfMissing(join(REPO, '.codex', 'AGENTS.md'),
                        join(home(), '.codex', 'AGENTS.md'), dry);
      return ok;
    },
  },
  'cursor': {
    label: 'Cursor',
    status: 'tested',
    install: (dry) => {
      const root = join(home(), '.cursor', 'skills');
      const ok = installSkills(root, dry, { label: 'Cursor' });
      copyFiles(join(REPO, '.cursor', 'rules'), join(home(), '.cursor', 'rules'),
                dry, { ext: '.mdc', label: 'Cursor rule(s)' });
      copyFileIfMissing(join(REPO, '.cursor', 'hooks.json'),
                        join(home(), '.cursor', 'hooks.json'), dry);
      if (!dry) log('Cursor: restart to pick up skills, rules, and hooks.');
      return ok;
    },
  },
  'hermes': {
    label: 'Hermes',
    status: 'tested',
    install: (dry) => {
      // Hermes scans category folders under ~/.hermes/skills.
      const root = join(hermesRoot(), 'skills');
      return installSkills(root, dry, { group: 'agent-foundry', label: 'Hermes' });
    },
  },
  'gemini-cli': {
    label: 'Gemini CLI / Antigravity CLI',
    status: 'tested',
    install: (dry) => {
      const gemini = join(home(), '.gemini');
      let ok = installSkills(join(gemini, 'skills'), dry, { label: 'Gemini CLI' });

      // Also ship a real extension so commands/context/MCP travel together.
      const ext = join(gemini, 'extensions', 'agent-foundry');
      if (dry) {
        log(`Would create Gemini extension: ${ext}`);
      } else {
        ensureDir(ext);
        // Migrate an early layout that put skills at the extension root.
        for (const stale of readManaged(ext)) rmIfExists(join(ext, stale));
        rmIfExists(join(ext, MANAGED_MARKER));
        writeFileSync(join(ext, 'gemini-extension.json'), JSON.stringify({
          name: 'agent-foundry',
          version: pkgVersion(),
          description: 'Curated, harness-agnostic agent skills from Agent Foundry.',
          contextFileName: 'GEMINI.md',
        }, null, 2) + '\n');
        copyFileSync(join(REPO, '.gemini', 'AGENTS.md'), join(ext, 'GEMINI.md'));
        log(`  âœ“ wrote ${join(ext, 'gemini-extension.json')}`);
      }
      // The extension contract is extensions/<name>/skills/<skill>/SKILL.md.
      ok = installSkills(join(ext, 'skills'), dry, { label: 'Gemini extension' }) && ok;
      return ok;
    },
  },
  'opencode': {
    label: 'OpenCode',
    status: 'tested',
    install: (dry) => {
      const cfg = join(home(), '.config', 'opencode');
      const ok = installSkills(join(cfg, 'skills'), dry, { label: 'OpenCode' });
      copyTree(join(REPO, '.opencode', 'instructions'),
               join(cfg, 'agent-foundry', 'instructions'), dry, 'OpenCode instructions');
      if (!dry) {
        log('');
        log('Optional: merge agents/commands into your opencode.json:');
        log(`  ${join(REPO, '.opencode', 'opencode.json')}`);
        log(`  ${join(cfg, 'opencode.json')}`);
      }
      return ok;
    },
  },
  'antigravity': {
    label: 'Antigravity (App / IDE / CLI)',
    status: 'tested',
    install: (dry) => {
      // Three products, three global roots. Workspace .agents/skills is
      // intentionally not touched; the shared root covers it.
      const roots = [
        join(home(), '.gemini', 'config', 'skills'),
        join(home(), '.gemini', 'antigravity-cli', 'skills'),
        SHARED_SKILLS(),
      ];
      let ok = true;
      for (const root of roots) {
        ok = installSkills(root, dry, { label: 'Antigravity' }) && ok;
      }
      copyFiles(join(REPO, '.antigravity', 'rules'),
                join(home(), '.gemini', 'config', 'rules'), dry,
                { ext: '.md', label: 'Antigravity rule(s)' });
      copyFiles(join(REPO, '.antigravity', 'rules'),
                join(home(), '.gemini', 'antigravity-cli', 'rules'), dry,
                { ext: '.md', label: 'Antigravity CLI rule(s)' });
      return ok;
    },
  },
  'codebuddy': {
    label: 'CodeBuddy',
    status: 'tested',
    install: (dry) => {
      const cfg = join(home(), '.codebuddy');
      const ok = installSkills(join(cfg, 'skills'), dry, { label: 'CodeBuddy' });
      copyFiles(join(REPO, '.codebuddy', 'commands'), join(cfg, 'commands'), dry,
                { ext: '.md', label: 'CodeBuddy command(s)' });
      return ok;
    },
  },
  'joycode': {
    label: 'JoyCode',
    status: 'tested',
    install: (dry) => {
      const cfg = join(home(), '.joycode');
      const ok = installSkills(join(cfg, 'skills'), dry, { label: 'JoyCode' });
      copyFiles(join(REPO, '.joycode', 'commands'), join(cfg, 'commands'), dry,
                { ext: '.md', label: 'JoyCode command(s)' });
      return ok;
    },
  },
  'qwen': {
    label: 'Qwen Code',
    status: 'tested',
    install: (dry) => installSkills(join(home(), '.qwen', 'skills'), dry,
                                     { label: 'Qwen Code' }),
  },
  'kimi': {
    label: 'Kimi CLI',
    status: 'tested',
    install: (dry) => {
      const ok = installSkills(join(kimiRoot(), 'skills'), dry, { label: 'Kimi' });
      installSkills(SHARED_SKILLS(), dry, { label: 'cross-tool agents' });
      return ok;
    },
  },
  'openclaw': {
    label: 'OpenClaw',
    status: 'tested',
    install: (dry) => {
      const ok = installSkills(join(home(), '.openclaw', 'skills'), dry,
                               { group: 'agent-foundry', label: 'OpenClaw' });
      installSkills(SHARED_SKILLS(), dry, { label: 'cross-tool agents' });
      return ok;
    },
  },
  'zed': {
    label: 'Zed',
    status: 'tested',
    install: (dry) => {
      // Zed loads skills only from ~/.agents/skills (global) and
      // .agents/skills (project). Nesting is explicitly unsupported.
      const ok = installSkills(SHARED_SKILLS(), dry, { label: 'Zed' });
      if (!dry) {
        log('');
        log(`Zed personal instructions: ${join(zedConfigRoot(), 'AGENTS.md')}`);
        log('Project instructions: AGENTS.md or .rules');
      }
      return ok;
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
  copy: false,
};
for (const a of args) {
  if (a === '--dry-run')           opts.dryRun = true;
  else if (a === '--manual')        opts.manual = true;
  else if (a === '--list')          opts.list = true;
  else if (a === '--copy')          opts.copy = true;
  else if (a === '--verbose' || a === '-v') opts.verbose = true;
  else if (a === '--force' || a === '-f') opts.force = true;
  else if (a.startsWith('--harness=')) opts.harness = a.slice('--harness='.length);
  else if (a === '--help' || a === '-h') { printHelp(); process.exit(0); }
  else { console.error(`Unknown arg: ${a}`); printHelp(); process.exit(2); }
}

// ---------- main ----------
function printHelp() {
  const STATUS_BADGE = { 'tested': 'âœ“', 'coming-soon': 'â—‹' };
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
  --copy              Copy skills instead of linking (portable, no live updates)
  --force, -f         Legacy; managed entries are always refreshed
  --verbose, -v       Verbose output
  --help, -h          Show this help

Targets (âœ“ tested):
${list}
`);
}

if (opts.list) { printHelp(); process.exit(0); }

if (opts.manual) {
  console.log('Manual install instructions:');
  console.log('');
  console.log('  1. Pick a target from the list (run with --list)');
  console.log('  2. Put each skill directory in the harness\'s skills root:');
  console.log(`       ${REPO}/skills/core/<skill> -> <root>/<skill>`);
  console.log(`       ${REPO}/skills/optional/<skill> -> <root>/<skill>`);
  console.log('     Do not nest a parent folder: most harnesses scan direct children only.');
  console.log('  3. Restart the harness');
  console.log('');
  console.log('  Example for Claude Code:');
  console.log(`    for d in "${REPO}"/skills/*/*; do ln -s "$d" "${home()}/.claude/skills/$(basename "$d")"; done`);
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

log(`Agent Foundry installer â€” ${osKind()} ${arch()}`);
log(`Target: ${opts.harness} (${installer.label})`);
log(`Repo:   ${REPO}`);
log(`Mode:   ${opts.dryRun ? 'dry-run' : 'install'}`);
log('');

const ok = installer.install(opts.dryRun);

if (ok && opts.dryRun) {
  log(`Would ${opts.copy ? 'copy' : 'link'} ${skillSources().length} skills -> ${INDEX_SKILLS()} (CLI index)`);
}

if (ok && !opts.dryRun) {
  installSkills(INDEX_SKILLS(), false, { label: 'Agent Foundry CLI index' });
  log('');
  log('Done. Restart your harness so it picks up the new skills.');
}
