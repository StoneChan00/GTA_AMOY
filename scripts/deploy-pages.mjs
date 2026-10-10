/** One-command GitHub Pages release for this project site (https://<user>.github.io/<repo>/).
 * npm run deploy:pages  (or: node scripts/deploy-pages.mjs)
 *
 * Pipeline: clean dist -> npm run build -- --base=/<repo>/ -> rewrite root-absolute
 * runtime asset paths inside built JS/CSS/HTML/JSON (Vite never rewrites string
 * literals; skipping this step ships a blank page) -> fail on any leftover ->
 * push dist as the gh-pages branch with plain blobs (Pages must serve real
 * files, not Git LFS pointers) -> drop the temporary dist/.git so the next
 * `vite build` can empty dist normally.
 *
 * The sub-path is derived from the origin remote name; set DEPLOY_PAGES_BASE
 * to override (e.g. "/" for a user site or a custom domain).
 * Prerequisites: origin remote configured, push credentials available, and
 * `git lfs pull` run (prebuild validates the characters anyway).
 */
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');

const run = (cmd, args, opts = {}) => {
  const r = spawnSync(cmd, args, {cwd: root, encoding: 'utf8', ...opts});
  if (r.status !== 0) throw Error(`命令失败：${cmd} ${args.join(' ')}\n${(r.stderr || r.stdout || '').toString().slice(0, 2000)}`);
  return (typeof r.stdout === 'string' ? r.stdout : '').trim();
};

// 1. Sub-path from the origin remote (https://github.com/<owner>/<repo>.git -> /<repo>/).
const origin = run('git', ['remote', 'get-url', 'origin']);
if (!origin) throw Error('无法读取 origin 远端地址：请先 git remote add origin <url>');
const repo = origin.replace(/\.git$/, '').split(/[/:]/).pop();
const base = process.env.DEPLOY_PAGES_BASE || `/${repo}/`;
const prefix = base.replace(/\/+$/, '');
console.log(`部署目标：${origin} -> gh-pages，子路径 ${base}`);

// 2. Clean dist, including any leftover deploy-time .git so Vite may empty it.
fs.rmSync(dist, {recursive: true, force: true});

// 3. Production build with base (keeps prebuild character checks and tsc).
run('npm', ['run', 'build', '--', `--base=${base}`], {stdio: 'inherit', ...(process.platform === 'win32' ? {shell: true} : {})});

// 4. Rewrite root-absolute runtime asset paths in built JS/CSS/HTML/JSON.
//    Quote + /(city|characters|assets|licenses) followed by a quote or slash:
//    covers '/city/x', `'/city/'`, '/characters'; never touches '/GTA_AMOY/...'
//    (there the quote is followed by /G, not by /c).
const re = /(["'`])\/(city|characters|assets|licenses)(?=["'`\/])/g;
let files = 0, subs = 0;
const rewrite = dir => {
  for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { rewrite(p); continue; }
    if (!/\.(js|css|html|json)$/.test(e.name)) continue;
    const src = fs.readFileSync(p, 'utf8');
    let n = 0;
    const out = src.replace(re, (m, q, seg) => { n++; return q + prefix + '/' + seg; });
    if (n) { fs.writeFileSync(p, out); files++; subs += n; }
  }
};
rewrite(dist);
console.log(`路径重写：${subs} 处（${files} 个文件）`);

// 5. A newly hard-coded path pattern must fail loudly instead of shipping 404s.
const leftovers = [];
const verify = dir => {
  for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { verify(p); continue; }
    if (!/\.(js|css|html|json)$/.test(e.name)) continue;
    if (fs.readFileSync(p, 'utf8').match(re)) leftovers.push(path.relative(dist, p));
  }
};
verify(dist);
if (leftovers.length) throw Error('产物中仍有未重写的根绝对路径（新增硬编码路径需先加入重写清单）：' + leftovers.join(', '));

// 6. Ship dist as the gh-pages branch: plain blobs, no .gitattributes, no LFS.
fs.writeFileSync(path.join(dist, '.nojekyll'), '');
const git = (args, opts = {}) => run('git', ['-C', dist, ...args], opts);
git(['init']);
git(['checkout', '-b', 'gh-pages']);
const userName = run('git', ['config', 'user.name']) || 'pages-deploy';
const userEmail = run('git', ['config', 'user.email']) || 'pages-deploy@users.noreply.github.com';
git(['add', '-A']);
git(['-c', `user.name=${userName}`, '-c', `user.email=${userEmail}`, 'commit', '-m', `deploy: GitHub Pages build (base=${base}) ${new Date().toISOString()}`]);
git(['remote', 'add', 'origin', origin]);
console.log('推送 gh-pages（产物约 160 MB，请稍候）…');
git(['push', '--force', '-u', 'origin', 'gh-pages'], {stdio: 'inherit'});

// 7. Drop the temporary repo so future builds start from an empty dist.
fs.rmSync(path.join(dist, '.git'), {recursive: true, force: true});
const owner = origin.replace(/\.git$/, '').match(/github\.com[\/:]([^\/]+)\//)?.[1];
console.log(`完成。站点：${owner ? `https://${owner}.github.io/${repo}/` : 'gh-pages 分支'}`);
