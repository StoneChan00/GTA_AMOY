/** One-command release to the Alibaba Cloud ECS static host (http://<host>/<REPO>/).
 * npm run deploy:ecs  (or: node scripts/deploy-ecs.mjs)
 *
 * The ECS serves multiple projects from one Nginx server: /var/www is the
 * multi-project root, each project lives in /var/www/<repo>/ and is reached
 * at http://<host>/<repo>/ (mirrors the GitHub Pages project-site convention).
 *
 * Pipeline: clean dist -> npm run build -- --base=/<repo>/ -> rewrite
 * root-absolute runtime asset paths (shared with deploy-pages) -> tar -> scp
 * to /tmp on the host -> remote extract into /var/www/<repo>/.
 *
 * Env overrides: DEPLOY_ECS_HOST (default root@39.96.117.179 — plain
 * user@host, bracketed ssh-config aliases break PowerShell->scp argument
 * passing) and DEPLOY_PAGES_BASE for the sub-path.
 * Prerequisites: ssh key auth to the host, tar in PATH on both sides.
 */
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {rewriteDistPaths, verifyNoLeftovers} from './rewrite-dist-paths.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dist = path.join(root, 'dist');
const host = process.env.DEPLOY_ECS_HOST || 'root@39.96.117.179';

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
console.log(`部署目标：${host} -> /var/www/${repo}，访问路径 http://<host>${base}`);

// 2. Clean dist, including any leftover deploy-time .git so Vite may empty it.
fs.rmSync(dist, {recursive: true, force: true});

// 3. Production build with base (keeps prebuild character checks and tsc).
run('npm', ['run', 'build', '--', `--base=${base}`], {stdio: 'inherit', ...(process.platform === 'win32' ? {shell: true} : {})});

// 4-5. Rewrite root-absolute runtime asset paths, then fail loudly on leftovers.
const {files, subs} = rewriteDistPaths(dist, prefix);
console.log(`路径重写：${subs} 处（${files} 个文件）`);
verifyNoLeftovers(dist);

// 6. Pack, upload and extract on the host.
const tarball = path.join(os.tmpdir(), `${repo}-ecs.tar.gz`);
run('tar', ['-czf', tarball, '-C', dist, '.']);
const size = (fs.statSync(tarball).size / 1048576).toFixed(0);
console.log(`打包完成（${size} MB），上传 ${host} …`);
run('scp', ['-o', 'BatchMode=yes', tarball, `${host}:/tmp/${repo}-ecs.tar.gz`], {stdio: 'inherit'});
console.log('远端解压部署 …');
run('ssh', ['-o', 'BatchMode=yes', host, `mkdir -p /var/www/${repo} && tar -xzf /tmp/${repo}-ecs.tar.gz -C /var/www/${repo} && rm -f /tmp/${repo}-ecs.tar.gz && ls /var/www/${repo} | head -4`], {stdio: 'inherit'});
fs.rmSync(tarball, {force: true});
console.log(`完成。站点：http://${host.split('@')[1]}${base}`);
