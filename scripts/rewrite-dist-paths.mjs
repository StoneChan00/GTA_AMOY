/** Shared dist post-processing for sub-path hosting (GitHub Pages project sites,
 * ECS multi-project roots, ...): rewrite root-absolute runtime asset paths
 * inside built JS/CSS/HTML/JSON.
 *
 * Vite's `--base` only rewrites URLs that go through the bundler and HTML.
 * Runtime string literals such as fetch('/city/city.json') and paths stored
 * inside JSON manifests are never touched — without this rewrite a sub-path
 * deploy ships a blank page / 404s.
 *
 * Quote + /(city|characters|assets|licenses) followed by a quote or slash:
 * covers '/city/x', `'/city/'`, '/characters'; never touches '/GTA_AMOY/...'
 * (there the quote is followed by /G, not by /c).
 */
import fs from 'node:fs';
import path from 'node:path';

const RE = /(["'`])\/(city|characters|assets|licenses)(?=["'`\/])/g;

export function rewriteDistPaths(dist, prefix) {
  let files = 0, subs = 0;
  const walk = dir => {
    for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { walk(p); continue; }
      if (!/\.(js|css|html|json)$/.test(e.name)) continue;
      const src = fs.readFileSync(p, 'utf8');
      let n = 0;
      const out = src.replace(RE, (m, q, seg) => { n++; return q + prefix + '/' + seg; });
      if (n) { fs.writeFileSync(p, out); files++; subs += n; }
    }
  };
  walk(dist);
  return {files, subs};
}

/** A newly hard-coded path pattern must fail loudly instead of shipping 404s. */
export function verifyNoLeftovers(dist) {
  const leftovers = [];
  const scan = dir => {
    for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { scan(p); continue; }
      if (!/\.(js|css|html|json)$/.test(e.name)) continue;
      if (fs.readFileSync(p, 'utf8').match(RE)) leftovers.push(path.relative(dist, p));
    }
  };
  scan(dist);
  if (leftovers.length) throw Error('产物中仍有未重写的根绝对路径（新增硬编码路径需先加入重写清单）：' + leftovers.join(', '));
  return leftovers;
}
