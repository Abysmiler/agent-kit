import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { END, START, main } from './sync.mjs';

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}
const read = (file) => fs.readFileSync(file, 'utf8');
const exists = (file) => fs.existsSync(file);

// A throwaway repo plus three host homes; claude and codex exist, zcode does not.
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'agent-kit-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const repo = path.join(root, 'repo');
  write(path.join(repo, 'rules/core.md'), '# Core\n\n- rule one\n');
  for (const host of ['claude', 'codex', 'zcode']) write(path.join(repo, `hosts/host-${host}.md`), `## Host ${host}\n`);
  write(path.join(repo, 'skills/alpha/SKILL.md'), 'alpha v1\n');
  write(path.join(repo, 'skills/alpha/SKILL.zh.md'), '译本\n');
  write(path.join(repo, 'skills/alpha/references/notes.md'), 'notes v1\n');
  const homes = Object.fromEntries(['claude', 'codex', 'zcode'].map((host) => [host, path.join(root, `home-${host}`)]));
  fs.mkdirSync(homes.claude);
  fs.mkdirSync(homes.codex);
  const run = (...args) => {
    const lines = [];
    const code = main(['--repo', repo, '--claude-home', homes.claude, '--codex-home', homes.codex, '--zcode-home', homes.zcode, ...args], (line) => lines.push(line));
    return { code, out: lines.join('\n') };
  };
  return { repo, homes, run };
}

test('preview writes nothing', (t) => {
  const { homes, run } = fixture(t);
  const { code, out } = run();
  assert.equal(code, 0);
  assert.match(out, /Preview only/);
  assert.deepEqual(fs.readdirSync(homes.claude), []);
  assert.deepEqual(fs.readdirSync(homes.codex), []);
});

test('apply installs entry, skills and manifest; skips translations and absent homes', (t) => {
  const { homes, run } = fixture(t);
  assert.equal(run('--apply').code, 0);
  const entry = read(path.join(homes.claude, 'CLAUDE.md'));
  assert.equal(entry, `${START}\n# Core\n\n- rule one\n\n## Host claude\n${END}\n`);
  assert.match(read(path.join(homes.codex, 'AGENTS.md')), /## Host codex/);
  assert.equal(read(path.join(homes.claude, 'skills/alpha/SKILL.md')), 'alpha v1\n');
  assert.equal(read(path.join(homes.claude, 'skills/alpha/references/notes.md')), 'notes v1\n');
  assert.ok(!exists(path.join(homes.claude, 'skills/alpha/SKILL.zh.md')));
  assert.ok(exists(path.join(homes.claude, '.agent-kit/manifest.json')));
  assert.ok(!exists(homes.zcode), 'auto target must not create a missing home');
  assert.ok(!exists(path.join(homes.claude, '.agent-kit/backups')), 'nothing replaced, so no backups');
});

test('second apply is a no-op', (t) => {
  const { run } = fixture(t);
  run('--apply');
  const { code, out } = run('--apply');
  assert.equal(code, 0);
  assert.match(out, /Already up to date/);
});

test('named target creates a missing home', (t) => {
  const { homes, run } = fixture(t);
  assert.equal(run('--apply', '--target', 'zcode').code, 0);
  assert.ok(exists(path.join(homes.zcode, 'AGENTS.md')));
  assert.ok(!exists(path.join(homes.claude, 'CLAUDE.md')), 'unselected hosts stay untouched');
});

test('entry without markers keeps its content, gets the block appended, and is backed up', (t) => {
  const { homes, run } = fixture(t);
  const mine = '# My preferences\r\n\r\n- use the proxy\r\n';
  write(path.join(homes.codex, 'AGENTS.md'), mine);
  assert.equal(run('--apply').code, 0);
  const entry = read(path.join(homes.codex, 'AGENTS.md'));
  assert.ok(entry.startsWith('# My preferences\r\n\r\n- use the proxy\r\n\r\n' + START + '\r\n'));
  assert.ok(!/[^\r]\n/.test(entry), 'CRLF line endings are preserved');
  const [batch] = fs.readdirSync(path.join(homes.codex, '.agent-kit/backups'));
  assert.equal(read(path.join(homes.codex, '.agent-kit/backups', batch, 'AGENTS.md')), mine);
});

test('core update rewrites only the block and keeps text outside it', (t) => {
  const { repo, homes, run } = fixture(t);
  run('--apply');
  const file = path.join(homes.claude, 'CLAUDE.md');
  write(file, `before\n\n${read(file)}\nafter\n`);
  write(path.join(repo, 'rules/core.md'), '# Core\n\n- rule two\n');
  assert.equal(run('--apply').code, 0);
  const entry = read(file);
  assert.ok(entry.startsWith('before\n\n' + START));
  assert.ok(entry.endsWith(END + '\n\nafter\n'));
  assert.match(entry, /rule two/);
  assert.doesNotMatch(entry, /rule one/);
});

test('local edit inside the block conflicts and blocks every target', (t) => {
  const { repo, homes, run } = fixture(t);
  run('--apply');
  const file = path.join(homes.claude, 'CLAUDE.md');
  const edited = read(file).replace('rule one', 'my own rule');
  write(file, edited);
  write(path.join(repo, 'rules/core.md'), '# Core\n\n- rule two\n');
  const { code, out } = run('--apply');
  assert.equal(code, 2);
  assert.match(out, /CONFLICT: .*edited locally/);
  assert.equal(read(file), edited);
  assert.match(read(path.join(homes.codex, 'AGENTS.md')), /rule one/, 'the clean target must not be written either');

  assert.equal(run('--apply', '--replace', 'claude:CLAUDE.md').code, 0);
  assert.match(read(file), /rule two/);
  assert.match(read(path.join(homes.codex, 'AGENTS.md')), /rule two/);
});

test('malformed markers always conflict', (t) => {
  const { homes, run } = fixture(t);
  write(path.join(homes.claude, 'CLAUDE.md'), `${START}\nx\n${START}\ny\n${END}\n`);
  const { code, out } = run('--apply', '--replace', 'claude:CLAUDE.md');
  assert.equal(code, 2);
  assert.match(out, /malformed or duplicate/);
});

test('skill files: local edit is preserved, double edit conflicts, --replace overrides', (t) => {
  const { repo, homes, run } = fixture(t);
  run('--apply');
  const installed = path.join(homes.claude, 'skills/alpha/SKILL.md');
  write(installed, 'my tweak\n');
  let result = run('--apply');
  assert.equal(result.code, 0);
  assert.match(result.out, /preserve: skills\/alpha\/SKILL\.md/);
  assert.equal(read(installed), 'my tweak\n');

  write(path.join(repo, 'skills/alpha/SKILL.md'), 'alpha v2\n');
  result = run('--apply');
  assert.equal(result.code, 2);
  assert.equal(read(installed), 'my tweak\n');
  assert.equal(read(path.join(homes.codex, 'skills/alpha/SKILL.md')), 'alpha v1\n');

  assert.equal(run('--apply', '--replace', 'claude:skills/alpha/SKILL.md').code, 0);
  assert.equal(read(installed), 'alpha v2\n');
  const [batch] = fs.readdirSync(path.join(homes.claude, '.agent-kit/backups'));
  assert.equal(read(path.join(homes.claude, '.agent-kit/backups', batch, 'skills/alpha/SKILL.md')), 'my tweak\n');
});

test('unmanaged file that differs from source conflicts; identical file is adopted', (t) => {
  const { homes, run } = fixture(t);
  write(path.join(homes.claude, 'skills/alpha/SKILL.md'), 'someone else\n');
  write(path.join(homes.codex, 'skills/alpha/SKILL.md'), 'alpha v1\n');
  const { code, out } = run('--target', 'claude');
  assert.equal(code, 2);
  assert.match(out, /unmanaged file differs/);
  const adopted = run('--apply', '--target', 'codex');
  assert.equal(adopted.code, 0);
  assert.match(adopted.out, /adopt: skills\/alpha\/SKILL\.md/);
});

test('files removed from source are deleted when untouched and kept when edited', (t) => {
  const { repo, homes, run } = fixture(t);
  write(path.join(repo, 'skills/beta/SKILL.md'), 'beta\n');
  // A nested directory, to check that directories emptied by a removal are pruned bottom-up.
  write(path.join(repo, 'skills/alpha/data/deep/table.txt'), 'data\n');
  run('--apply');
  write(path.join(homes.codex, 'skills/beta/SKILL.md'), 'beta, edited\n');
  write(path.join(homes.claude, 'skills/user-skill/SKILL.md'), 'mine\n');
  fs.rmSync(path.join(repo, 'skills/beta'), { recursive: true });
  fs.rmSync(path.join(repo, 'skills/alpha/data'), { recursive: true });
  const { code, out } = run('--apply');
  assert.equal(code, 0);
  assert.ok(!exists(path.join(homes.claude, 'skills/beta/SKILL.md')), 'untouched stale file is removed');
  assert.ok(!exists(path.join(homes.claude, 'skills/alpha/data')), 'directories emptied by the removal are pruned');
  assert.ok(exists(path.join(homes.claude, 'skills/alpha/SKILL.md')));
  assert.equal(read(path.join(homes.claude, 'skills/user-skill/SKILL.md')), 'mine\n', 'files the tool never installed are left alone');
  assert.equal(read(path.join(homes.codex, 'skills/beta/SKILL.md')), 'beta, edited\n');
  assert.match(out, /keep: skills\/beta\/SKILL\.md/);
  const [batch] = fs.readdirSync(path.join(homes.claude, '.agent-kit/backups'));
  assert.equal(read(path.join(homes.claude, '.agent-kit/backups', batch, 'skills/beta/SKILL.md')), 'beta\n');
});

test('local overlay adds rules and skills; a duplicate skill name conflicts', (t) => {
  const { repo, homes, run } = fixture(t);
  write(path.join(repo, 'local/rules.md'), '## Local\n\n- never touch SVN\n');
  write(path.join(repo, 'local/skills/private/SKILL.md'), 'private\n');
  assert.equal(run('--apply').code, 0);
  assert.match(read(path.join(homes.claude, 'CLAUDE.md')), /## Host claude\n\n## Local\n\n- never touch SVN\n<!--/);
  assert.equal(read(path.join(homes.codex, 'skills/private/SKILL.md')), 'private\n');

  write(path.join(repo, 'local/skills/alpha/SKILL.md'), 'shadow\n');
  const { code, out } = run('--apply');
  assert.equal(code, 2);
  assert.match(out, /exists in both/);
});

test('manifest written by the old Python tool is accepted', (t) => {
  const { repo, homes, run } = fixture(t);
  run('--apply');
  const file = path.join(homes.claude, '.agent-kit/manifest.json');
  const manifest = JSON.parse(read(file));
  assert.deepEqual(Object.keys(manifest).sort(), ['entry', 'skills', 'target', 'version']);
  assert.deepEqual(Object.keys(manifest.entry).sort(), ['core_sha256', 'path']);
  assert.deepEqual(Object.keys(manifest.skills), ['alpha/SKILL.md', 'alpha/references/notes.md']);
  write(path.join(repo, 'rules/core.md'), '# Core\n\n- rule two\n');
  assert.equal(run('--apply').code, 0);
});

test('a manifest with an unsafe path conflicts and deletes nothing', (t) => {
  const { homes, run } = fixture(t);
  run('--apply');
  const victim = path.join(homes.claude, 'victim.txt');
  write(victim, 'keep me\n');
  const file = path.join(homes.claude, '.agent-kit/manifest.json');
  const manifest = JSON.parse(read(file));
  manifest.skills['../victim.txt'] = 'a'.repeat(64);
  write(file, JSON.stringify(manifest));
  const { code, out } = run('--apply');
  assert.equal(code, 2);
  assert.match(out, /manifest\.json is damaged/);
  assert.equal(read(victim), 'keep me\n');
});

test('a symlinked skill directory is refused', (t) => {
  const { homes, run } = fixture(t);
  const outside = path.join(path.dirname(homes.claude), 'outside');
  fs.mkdirSync(outside);
  fs.mkdirSync(path.join(homes.claude, 'skills'));
  try {
    fs.symlinkSync(outside, path.join(homes.claude, 'skills/alpha'), 'junction');
  } catch {
    t.skip('cannot create links here');
    return;
  }
  const { code, out } = run('--apply');
  assert.equal(code, 2);
  assert.match(out, /symlink or junction/);
  assert.deepEqual(fs.readdirSync(outside), []);
});

test('bad arguments are reported, not thrown', (t) => {
  const { run } = fixture(t);
  assert.equal(run('--target', 'nope').code, 2);
  assert.equal(run('--replace', 'claude:../x').code, 2);
  assert.equal(run('--replace', 'zcode:AGENTS.md').code, 2, 'host not selected under auto');
  assert.equal(run('--bogus').code, 2);
});
