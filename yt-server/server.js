/* YT local server — chay tren may nha, admin.html goi sang.
   GET  /ping          -> {ok:true} (admin dung de biet may co bat khong)
   POST /dl {url, token} -> tai YouTube bang yt-dlp, up Cloudinary,
                            tra ve {url, public_id, del, bytes}
   Chi nghe 127.0.0.1 (may nha), co token chong nguoi la bam nut. */
const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = __dirname;
const CFG_PATH = path.join(ROOT, 'config.json');
const DL_DIR = path.join(ROOT, 'dl');
if (!fs.existsSync(DL_DIR)) fs.mkdirSync(DL_DIR, { recursive: true });

let cfg = {};
try { cfg = JSON.parse(fs.readFileSync(CFG_PATH, 'utf8')); } catch (e) { cfg = {}; }
if (!cfg.token) cfg.token = crypto.randomBytes(24).toString('hex');
cfg.port = cfg.port || 8799;
cfg.ytdlp = cfg.ytdlp || path.join(ROOT, '..', 'tools', 'yt-dlp.exe');
cfg.ffmpeg = cfg.ffmpeg || path.join(ROOT, '..', 'tools', 'ffmpeg.exe');
cfg.cloud = cfg.cloud || 'ck9gvbcq';
cfg.preset = cfg.preset || 'web_upload';
cfg.site = cfg.site || 'https://acceleratorares.vercel.app';
const PORT = process.env.YT_PORT || cfg.port || 8799;
fs.writeFileSync(CFG_PATH, JSON.stringify(cfg, null, 2));

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Private-Network', 'true');
}
function send(res, code, obj) {
  cors(res);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(obj));
}
function run(cmd, args) {
  return new Promise((resolve, reject) => {
    /* PYTHONIOENCODING=utf-8: ep yt-dlp in duong dan Unicode ra pipe,
       khong thi ten co dau/la (vd em dash) se lech -> stat ENOENT */
    const p = spawn(cmd, args, { windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }) });
    let out = '', err = '';
    p.stdout.on('data', d => { out += d; });
    p.stderr.on('data', d => { err += d; });
    p.on('error', reject);
    p.on('close', code => code === 0 ? resolve({ out, err }) : reject(new Error(err.slice(-2000) || ('exit ' + code))));
  });
}

let busy = false;
const hits = [];
function overLimit(){
  const now = Date.now();
  while (hits.length && now - hits[0] > 3600 * 1000) hits.shift();
  return hits.length >= 20;
}
const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') { cors(res); res.writeHead(204); res.end(); return; }
  const u = new URL(req.url, 'http://x');
  if (req.method === 'GET' && u.pathname === '/ping') return send(res, 200, { ok: true, busy });
  if (req.method === 'POST' && u.pathname === '/dl') {
    let body = '';
    req.on('data', c => { body += c; if (body.length > 1e6) req.destroy(); });
    req.on('end', async () => {
      try {
        const j = JSON.parse(body || '{}');
        const viaTunnel = !!(req.headers['cf-connecting-ip'] || req.headers['x-forwarded-for']);
        const origin = String(req.headers.origin || '');
        const siteOk = origin === '' || origin === cfg.site;
        /* Tu internet (qua tunnel) bat buoc token. May nha goi thang:
           token dung, hoac trinh duyet tu trang chinh (Origin), hoac curl tay. */
        if (viaTunnel) {
          if (j.token !== cfg.token) return send(res, 403, { error: 'sai token (xin token tu chu may qua chat)' });
        } else if (j.token !== cfg.token && !siteOk) {
          return send(res, 403, { error: 'sai token' });
        }
        if (busy) return send(res, 409, { error: 'may dang tai video khac, doi chut roi bam lai' });
        if (overLimit()) return send(res, 429, { error: 'may nha qua tai (toi da 20 video/gio), doi chut roi bam lai' });
        const url = String(j.url || '');
        if (!/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//.test(url)) return send(res, 400, { error: 'khong phai link youtube' });
        busy = true; hits.push(Date.now());
        try {
          const fmt = (/^[A-Za-z0-9_*+\/()[\].\-=,:? ]{1,120}$/.test(String(j.format || '')) && j.format) || 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b';
          const tpl = path.join(DL_DIR, Date.now() + '.%(title).60s [%(id)s].%(ext)s');
          const baseArgs = ['-f', fmt, '--merge-output-format', 'mp4',
            '--ffmpeg-location', cfg.ffmpeg, '-o', tpl, '--no-playlist', '--retries', '3',
            '--print', 'after_move:filepath', url];
          let r1;
          try { r1 = await run(cfg.ytdlp, baseArgs); }
          catch (e1) {
            /* Luot 2: doi sang android client (vuot kiem tra bot / SABR) */
            r1 = await run(cfg.ytdlp, ['--extractor-args', 'youtube:player_client=android'].concat(baseArgs));
          }
          const fp0 = r1.out.trim().split(/\r?\n/).pop();
          let fp = fp0, st = null;
          try { st = fs.statSync(fp); } catch (e) { st = null; }
          if (!st) {
            /* Du phong: ten in ra lech encoding thi lay file mp4 moi nhat trong dl/ */
            const cands = fs.readdirSync(DL_DIR).map(function (n) {
              const p = path.join(DL_DIR, n);
              try { return { p, m: fs.statSync(p).mtimeMs }; } catch (e) { return null; }
            }).filter(Boolean).sort((a, b) => b.m - a.m);
            if (!cands.length || Date.now() - cands[0].m > 15 * 60 * 1000) throw new Error('tai xong nhung khong thay file (bam lai lan nua)');
            fp = cands[0].p;
            st = fs.statSync(fp);
          }
          if (st.size > 100 * 1024 * 1024) {
            busy = false;
            return send(res, 413, { error: 'file ' + Math.round(st.size / 1048576) + 'MB vuot 100MB Cloudinary! File nam o yt-server/dl, up tay Drive/Catbox nhe' });
          }
          const r2 = await run('curl.exe', ['-sS', '-X', 'POST',
            'https://api.cloudinary.com/v1_1/' + cfg.cloud + '/video/upload',
            '-F', 'file=@' + fp, '-F', 'upload_preset=' + cfg.preset]);
          let up = {};
          try { up = JSON.parse(r2.out); } catch (e) { throw new Error('cloudinary tra ve la: ' + r2.out.slice(0, 200)); }
          if (!up.secure_url) throw new Error((up.error && up.error.message) || 'cloudinary tu choi');
          try { fs.unlinkSync(fp); } catch (e) {}
          busy = false;
          return send(res, 200, { ok: true, url: up.secure_url, public_id: up.public_id || '', del: up.delete_token || '', bytes: up.bytes || st.size });
        } catch (e) { busy = false; return send(res, 500, { error: String((e && e.message) || e).slice(0, 300) }); }
      } catch (e) { return send(res, 400, { error: 'sai du lieu' }); }
    });
    return;
  }
  send(res, 404, { error: 'not found' });
});
server.listen(PORT, '127.0.0.1', () => {
  console.log('YT server chay o http://127.0.0.1:' + PORT + ' (tat cua so nay = tat server)');
  console.log('TOKEN gui cho admin O XA nhap 1 lan (may nay dung khong can nhap): ' + cfg.token);
});
