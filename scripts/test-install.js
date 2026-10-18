#!/usr/bin/env node
// Cross-platform smoke test for the harness installer. Creates a throwaway
// home, installs every target, and asserts the documented skill roots.
import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const REPO = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const INSTALLER = join(REPO, 'scripts', 'install.js');
const home = mkdtempSync(join(tmpdir(), 'af-installer-'));
const project = join(home, 'project');
mkdirSync(project, { recursive: true });
const env = {
  ...process.env,
  HOME: home,
  USERPROFILE: home,
  APPDATA: join(home, 'AppData', 'Roaming'),
};
const expected = 35;
const failures = [];

function run(harness, cwd = home) {
  const r = spawnSync(process.execPath, [INSTALLER, `--harness=${harness}`], {
    cwd, env, encoding: 'utf8',
  });
  if (r.status !== 0) failures.push(`${harness}: exit ${r.status}\n${r.stderr}`);
  return r.stdout || '';
}

function countSkills(root) {
  if (!existsSync(root)) return 0;
  return readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() || e.isSymbolicLink()).length;
}

const roots = {
  'claude-code': join(home, '.claude', 'skills'),
  'claude-project': join(project, '.claude', 'skills'),
  'codex': join(home, '.agents', 'skills'),
  'cursor': join(home, '.cursor', 'skills'),
  'hermes': join(home, '.hermes', 'skills', 'agent-foundry'),
  'gemini-cli': join(home, '.gemini', 'skills'),
  'opencode': join(home, '.config', 'opencode', 'skills'),
  'antigravity': join(home, '.gemini', 'config', 'skills'),
  'codebuddy': join(home, '.codebuddy', 'skills'),
  'joycode': join(home, '.joycode', 'skills'),
  'qwen': join(home, '.qwen', 'skills'),
  'kimi': join(home, '.kimi-code', 'skills'),
  'openclaw': join(home, '.openclaw', 'skills', 'agent-foundry'),
  'zed': join(home, '.agents', 'skills'),
};

try {
  for (const harness of Object.keys(roots)) {
    run(harness, harness === 'claude-project' ? project : home);
  }

  for (const [harness, root] of Object.entries(roots)) {
    const n = countSkills(root);
    if (n !== expected) failures.push(`${harness}: ${n}/${expected} skills at ${root}`);
    const marker = join(root, '.agent-foundry-installed.json');
    if (!existsSync(marker)) {
      failures.push(`${harness}: missing ${marker}`);
    } else {
      const managed = JSON.parse(readFileSync(marker, 'utf8')).skills || [];
      if (managed.length !== expected) {
        failures.push(`${harness}: manifest lists ${managed.length}/${expected}`);
      }
    }
  }

  const ext = join(home, '.gemini', 'extensions', 'agent-foundry', 'skills');
  if (countSkills(ext) !== expected) {
    failures.push(`gemini extension: ${countSkills(ext)}/${expected} skills at ${ext}`);
  }

  const indexRoot = join(home, '.config', 'agent-foundry', 'skills');
  if (countSkills(indexRoot) !== expected) {
    failures.push(`CLI index: ${countSkills(indexRoot)}/${expected} skills at ${indexRoot}`);
  }

  // Re-run must be idempotent and must not duplicate links.
  run('claude-code');
  if (countSkills(roots['claude-code']) !== expected) {
    failures.push('claude-code: re-run changed the skill count');
  }
} finally {
  rmSync(home, { recursive: true, force: true });
}

if (failures.length) {
  console.error('installer test failed:\n' + failures.join('\n'));
  process.exit(1);
}
console.log(`installer ok: ${Object.keys(roots).length} targets, ${expected} skills each`);
