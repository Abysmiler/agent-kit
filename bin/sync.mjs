#!/usr/bin/env node
// Preview-first sync of agent-kit rules and skills into host config homes.
// Zero dependencies. Default is preview; nothing is written without --apply.
import { createHash, randomBytes } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const START = '<!-- AGENT-KIT:CORE:START -->';
export const END = '<!-- AGENT-KIT:CORE:END -->';
export const HOSTS = { claude: 'CLAUDE.md', codex: 'AGENTS.md', zcode: 'AGENTS.md' };
const STATE_DIR = '.agent-kit';
const MANIFEST = `${STATE_DIR}/manifest.json`;
const WRITES = new Set(['create', 'append', 'update', 'replace', 'remove']);

export class Conflict extends Error {}

const sha = (data) => createHash('sha256').update(data).digest('hex');
const normalize = (text) => text.replace(/\r\n?/g, '\n').trim();
const same = (a, b) => (a === null || b === null ? a === b : a.equals(b));

function safeRel(rel) {
  return typeof rel === 'string' && rel.length > 0 && !/[\\<>:"|?*\x00-\x1f]/.test(rel)
    && rel.split('/').every((part) => part && part !== '.' && part !== '..' && part === part.replace(/[ .]+$/, ''));
}

function lstat(target) {
  try {
    return fs.lstatSync(target);
  } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return null;
    throw error;
  }
}

// Read home/rel, refusing symlinks, junctions and unexpected file types on the way.
function readManaged(home, rel) {
  let current = home;
  const root = lstat(home);
  if (root && (root.isSymbolicLink() || !root.isDirectory())) throw new Conflict(`not a plain directory: ${home}`);
  const parts = rel.split('/');
  for (let index = 0; index < parts.length; index += 1) {
    current = path.join(current, parts[index]);
    const info = lstat(current);
    if (!info) return null;
    if (info.isSymbolicLink()) throw new Conflict(`symlink or junction in a managed path: ${current}`);
    const last = index === parts.length - 1;
    if (last ? !info.isFile() : !info.isDirectory()) throw new Conflict(`unexpected file type: ${current}`);
  }
  return fs.readFileSync(current);
}

function listSource(dir) {
  const files = [];
  const walk = (abs, rel) => {
    const entries = fs.readdirSync(abs, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1));
    for (const entry of entries) {
      const { name } = entry;
      if (name === '.DS_Store' || name === '__pycache__' || name.endsWith('.zh.md') || name.endsWith('.pyc')) continue;
      const childRel = rel ? `${rel}/${name}` : name;
      const childAbs = path.join(abs, name);
      if (entry.isSymbolicLink()) throw new Conflict(`symlink in source: ${childAbs}`);
      if (entry.isDirectory()) walk(childAbs, childRel);
      else if (!entry.isFile() || !safeRel(childRel)) throw new Conflict(`unsupported source path: ${childAbs}`);
      else files.push([childRel, childAbs]);
    }
  };
  if (lstat(dir)) walk(dir, '');
  return files;
}

// skills/ plus the untracked local/skills/ overlay; a skill name may live in only one of them.
function collectSkills(repo) {
  const files = new Map();
  const owners = new Map();
  for (const root of ['skills', 'local/skills']) {
    for (const [rel, abs] of listSource(path.join(repo, root))) {
      if (!rel.includes('/')) continue;
      const skill = rel.split('/')[0];
      if (owners.has(skill) && owners.get(skill) !== root) throw new Conflict(`skill "${skill}" exists in both skills/ and local/skills/`);
      owners.set(skill, root);
      files.set(rel, fs.readFileSync(abs));
    }
  }
  return files;
}

// Managed block body: core rules + host notes + optional untracked local rules.
export function renderBody(repo, host) {
  const sources = ['rules/core.md', `hosts/host-${host}.md`, 'local/rules.md'].map((rel) => path.join(repo, rel));
  const body = sources
    .filter((file, index) => index < 2 || lstat(file))
    .map((file) => normalize(fs.readFileSync(file, 'utf8')))
    .filter(Boolean)
    .join('\n\n');
  if (body.includes('AGENT-KIT:CORE')) throw new Conflict('rule sources must not contain AGENT-KIT:CORE markers');
  return body;
}

function loadManifest(bytes, host) {
  if (bytes === null) return { entry: null, skills: {} };
  const bad = (why) => new Conflict(`${MANIFEST} is damaged (${why}); fix or remove it manually`);
  let data;
  try {
    data = JSON.parse(bytes.toString('utf8'));
  } catch {
    throw bad('not JSON');
  }
  if (!data || data.version !== 1 || data.target !== host) throw bad('version or target mismatch');
  const isHash = (value) => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
  const skills = data.skills;
  if (!skills || typeof skills !== 'object' || Array.isArray(skills)) throw bad('skills');
  for (const [rel, hash] of Object.entries(skills)) {
    if (!safeRel(rel) || !rel.includes('/') || !isHash(hash)) throw bad(`unsafe skill entry ${JSON.stringify(rel)}`);
  }
  const entry = data.entry?.core_sha256;
  if (entry !== undefined && !isHash(entry)) throw bad('entry');
  return { entry: entry ?? null, skills };
}

function planEntry(host, home, body, previous, replace) {
  const rel = HOSTS[host];
  const dest = path.join(home, rel);
  const before = readManaged(home, rel);
  const block = `${START}\n${body}\n${END}`;
  const want = sha(body);
  const action = (kind, text, note) => ({ rel, kind, dest, before, content: text === null ? null : Buffer.from(text, 'utf8'), note });
  if (before === null) return action('create', `${block}\n`, 'new entry file');
  let text;
  try {
    text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(before);
  } catch {
    throw new Conflict(`${dest} is not UTF-8; convert it before syncing`);
  }
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  const local = block.replaceAll('\n', eol);
  const starts = text.split(START).length - 1;
  const ends = text.split(END).length - 1;
  const malformed = new Conflict(`${dest} has malformed or duplicate AGENT-KIT markers; repair it manually`);
  if (starts === 0 && ends === 0) {
    if (text.includes('AGENT-KIT:CORE')) throw malformed;
    const head = text.trimEnd();
    return action('append', `${head ? head + eol + eol : ''}${local}${eol}`, 'existing content kept; managed block appended');
  }
  const from = text.indexOf(START);
  const to = text.indexOf(END);
  if (starts !== 1 || ends !== 1 || from > to) throw malformed;
  const have = sha(normalize(text.slice(from + START.length, to)));
  if (have === want) return action(previous === want ? 'skip' : 'adopt', null, 'managed block already current');
  const forced = have !== previous;
  if (forced && !replace.has(rel)) {
    throw new Conflict(`${dest}: managed block was edited locally or has no baseline; review it, then pass --replace ${host}:${rel}`);
  }
  return action(forced ? 'replace' : 'update', text.slice(0, from) + local + text.slice(to + END.length), 'managed block only; text outside it is kept');
}

function planHost(repo, host, home, replace) {
  const plan = { host, home, actions: [], conflicts: [], manifestBefore: null, manifestContent: null, backupRoot: null };
  const attempt = (work) => {
    try {
      return work();
    } catch (error) {
      if (!(error instanceof Conflict) && !error.code) throw error;
      plan.conflicts.push(error.message);
      return undefined;
    }
  };
  const inside = (parent, child) => {
    const rel = path.relative(parent, child);
    return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
  };
  if (inside(repo, home) || inside(home, repo)) plan.conflicts.push(`host home overlaps the agent-kit repository: ${home}`);

  const loaded = attempt(() => {
    plan.manifestBefore = readManaged(home, MANIFEST);
    return { state: loadManifest(plan.manifestBefore, host), body: renderBody(repo, host), sources: collectSkills(repo) };
  });
  if (!loaded) return plan;
  const { state, body, sources } = loaded;
  const known = new Set([HOSTS[host]]);
  const nextSkills = {};

  const entry = attempt(() => planEntry(host, home, body, state.entry, replace));
  if (entry) plan.actions.push(entry);

  for (const [rel, source] of sources) {
    const full = `skills/${rel}`;
    const dest = path.join(home, full);
    const previous = state.skills[rel] ?? null;
    known.add(full);
    if (previous) nextSkills[rel] = previous;
    attempt(() => {
      const before = readManaged(home, full);
      const wanted = sha(source);
      const current = before === null ? null : sha(before);
      let kind;
      let note = '';
      let baseline = wanted;
      if (current === wanted) kind = previous === wanted ? 'skip' : 'adopt';
      else if (replace.has(full)) [kind, note] = [current === null ? 'create' : 'replace', 'authorized by --replace'];
      else if (current === null && previous === null) kind = 'create';
      else if (previous === null) throw new Conflict(`${dest}: unmanaged file differs from source; review it, then pass --replace ${host}:${full}`);
      else if (current !== previous) {
        if (wanted !== previous) throw new Conflict(`${dest}: changed or deleted locally and also changed in source; review it, then pass --replace ${host}:${full}`);
        [kind, note, baseline] = ['preserve', 'local change kept; source unchanged', previous];
      } else kind = 'update';
      plan.actions.push({ rel: full, kind, dest, before, content: WRITES.has(kind) ? source : null, note });
      nextSkills[rel] = baseline;
    });
  }

  // Files this tool installed earlier that no longer exist in the source.
  for (const [rel, previous] of Object.entries(state.skills)) {
    if (sources.has(rel)) continue;
    const full = `skills/${rel}`;
    const dest = path.join(home, full);
    known.add(full);
    attempt(() => {
      const before = readManaged(home, full);
      if (before === null) return;
      if (sha(before) === previous || replace.has(full)) {
        plan.actions.push({ rel: full, kind: 'remove', dest, before, content: null, note: 'removed from source; backed up first' });
      } else {
        plan.actions.push({ rel: full, kind: 'keep', dest, before, content: null, note: `removed from source but edited locally; delete it or pass --replace ${host}:${full}` });
        nextSkills[rel] = previous;
      }
    });
  }

  for (const rel of replace) {
    if (!known.has(rel)) plan.conflicts.push(`--replace names a path that is neither the entry nor a managed skill file: ${host}:${rel}`);
  }
  const sorted = Object.fromEntries(Object.keys(nextSkills).sort().map((key) => [key, nextSkills[key]]));
  const manifest = { entry: { core_sha256: sha(body), path: HOSTS[host] }, skills: sorted, target: host, version: 1 };
  const bytes = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
  if (!same(bytes, plan.manifestBefore)) plan.manifestContent = bytes;
  return plan;
}

export function buildPlans({ repo, target = 'auto', homes = {}, replace = [] }) {
  const root = path.resolve(repo);
  const resolved = Object.fromEntries(Object.keys(HOSTS).map((host) => [host, path.resolve(homes[host] ?? path.join(os.homedir(), `.${host}`))]));
  let selected;
  if (target === 'all') selected = Object.keys(HOSTS);
  else if (target === 'auto') selected = Object.keys(HOSTS).filter((host) => lstat(resolved[host]));
  else if (target in HOSTS) selected = [target];
  else throw new Conflict(`unknown target: ${target} (use auto, all, ${Object.keys(HOSTS).join(', ')})`);
  const replacements = Object.fromEntries(selected.map((host) => [host, new Set()]));
  for (const value of replace) {
    const split = value.indexOf(':');
    const host = value.slice(0, split);
    const rel = value.slice(split + 1);
    if (split < 1 || !(host in HOSTS) || !safeRel(rel)) throw new Conflict(`invalid --replace, expected HOST:RELATIVE_PATH: ${value}`);
    if (!replacements[host]) throw new Conflict(`--replace host is not selected: ${host}`);
    replacements[host].add(rel);
  }
  return selected.map((host) => planHost(root, host, resolved[host], replacements[host]));
}

function atomicWrite(dest, content) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  const temp = `${dest}.tmp-${randomBytes(4).toString('hex')}`;
  try {
    fs.writeFileSync(temp, content, { flag: 'wx' });
    const existing = lstat(dest);
    if (existing) fs.chmodSync(temp, existing.mode & 0o777);
    fs.renameSync(temp, dest);
  } finally {
    if (lstat(temp)) fs.unlinkSync(temp);
  }
}

function verifyUnchanged(plan, rel, before) {
  if (!same(readManaged(plan.home, rel), before)) throw new Conflict(`${path.join(plan.home, rel)} changed after planning; rerun the sync`);
}

export function applyPlans(plans) {
  if (plans.some((plan) => plan.conflicts.length)) throw new Conflict('conflicts found; nothing was written');
  // Recheck every target before the first write, so a late change still means zero writes.
  for (const plan of plans) {
    for (const action of plan.actions) verifyUnchanged(plan, action.rel, action.before);
    verifyUnchanged(plan, MANIFEST, plan.manifestBefore);
  }
  const stamp = `${new Date().toISOString().replace(/\D/g, '').slice(0, 14)}-${randomBytes(3).toString('hex')}`;
  for (const plan of plans) {
    const backupRoot = path.join(plan.home, STATE_DIR, 'backups', stamp);
    const skillsRoot = path.join(plan.home, 'skills');
    try {
      for (const action of plan.actions.filter((item) => WRITES.has(item.kind))) {
        verifyUnchanged(plan, action.rel, action.before);
        if (action.before !== null) {
          const backup = path.join(backupRoot, action.rel);
          fs.mkdirSync(path.dirname(backup), { recursive: true });
          fs.writeFileSync(backup, action.before, { flag: 'wx' });
          plan.backupRoot = backupRoot;
        }
        if (action.kind !== 'remove') {
          atomicWrite(action.dest, action.content);
          continue;
        }
        fs.unlinkSync(action.dest);
        for (let dir = path.dirname(action.dest); dir !== skillsRoot && dir.startsWith(skillsRoot); dir = path.dirname(dir)) {
          if (fs.readdirSync(dir).length) break;
          fs.rmdirSync(dir);
        }
      }
      if (plan.manifestContent) atomicWrite(path.join(plan.home, MANIFEST), plan.manifestContent);
    } catch (error) {
      const backups = plan.backupRoot ? ` Replaced files are backed up in ${plan.backupRoot}.` : '';
      throw new Conflict(`[${plan.host}] sync stopped midway: ${error.message}. Files already written equal the source and are adopted on the next run.${backups}`);
    }
  }
}

function report(plans, apply, log) {
  if (!plans.length) {
    log('No host home found (~/.claude, ~/.codex, ~/.zcode). Pass --target <host> or --target all to create one.');
    return;
  }
  for (const plan of plans) {
    log(`[${plan.host}] ${plan.home}`);
    const counts = {};
    for (const action of plan.actions) counts[action.kind] = (counts[action.kind] ?? 0) + 1;
    log(`  ${Object.keys(counts).sort().map((kind) => `${kind}=${counts[kind]}`).join(', ') || 'nothing to do'}`);
    for (const action of plan.actions) {
      if (action.kind !== 'skip') log(`  - ${action.kind}: ${action.rel}${action.note ? ` (${action.note})` : ''}`);
    }
    for (const message of plan.conflicts) log(`  - CONFLICT: ${message}`);
  }
  const conflicts = plans.reduce((total, plan) => total + plan.conflicts.length, 0);
  if (conflicts) log(`Stopped: ${conflicts} conflict(s); no target was modified.`);
  else if (!apply) log('Preview only; nothing was written. Re-run with --apply to write.');
}

const USAGE = `Usage: node bin/sync.mjs [--apply] [--target auto|all|claude|codex|zcode]
                         [--replace HOST:RELATIVE_PATH]... [--repo DIR]
                         [--claude-home DIR] [--codex-home DIR] [--zcode-home DIR]

Default is a preview. --apply writes after every selected host passes the conflict check.
--target auto (default) uses host homes that already exist; a named host or "all" may create them.
--replace authorizes overwriting one conflicting file, e.g. --replace codex:AGENTS.md`;

export function main(argv, log = console.log) {
  try {
    const options = { apply: false, target: 'auto', replace: [], homes: {}, repo: path.dirname(path.dirname(fileURLToPath(import.meta.url))) };
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      const value = () => {
        index += 1;
        if (index >= argv.length) throw new Conflict(`${arg} needs a value`);
        return argv[index];
      };
      const home = /^--(claude|codex|zcode)-home$/.exec(arg);
      if (arg === '-h' || arg === '--help') return log(USAGE), 0;
      if (arg === '--apply') options.apply = true;
      else if (arg === '--target') options.target = value();
      else if (arg === '--replace') options.replace.push(value());
      else if (arg === '--repo') options.repo = value();
      else if (home) options.homes[home[1]] = value();
      else throw new Conflict(`unknown argument: ${arg}\n${USAGE}`);
    }
    const plans = buildPlans(options);
    report(plans, options.apply, log);
    if (plans.some((plan) => plan.conflicts.length)) return 2;
    if (options.apply && plans.length) {
      applyPlans(plans);
      const changed = plans.some((plan) => plan.manifestContent || plan.actions.some((action) => WRITES.has(action.kind)));
      log(changed ? 'Sync applied.' : 'Already up to date; nothing was written.');
      for (const plan of plans) if (plan.backupRoot) log(`[${plan.host}] backups: ${plan.backupRoot}`);
    }
    return 0;
  } catch (error) {
    if (!(error instanceof Conflict) && !error.code) throw error;
    log(`error: ${error.message}`);
    return 2;
  }
}

const invoked = process.argv[1] ? fs.realpathSync(process.argv[1]) : '';
if (invoked && invoked.toLowerCase() === fs.realpathSync(fileURLToPath(import.meta.url)).toLowerCase()) {
  process.exitCode = main(process.argv.slice(2));
}
