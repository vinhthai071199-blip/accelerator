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
function ensureDir(d) { try { fs.mkdirSync(d, { recursive: true }); return true; } catch (e) { return false; } }
/* Kho video chinh: o E (khong co tu tao). Chuyen khac o dia -> copy+xoa. */
const LIB_DIR = 'E:\\videoserver';
function moveFile(a, b) {
  try { fs.renameSync(a, b); return; } catch (e) {
    if (!e || e.code !== 'EXDEV') throw e;
  }
  fs.copyFileSync(a, b);
  fs.unlinkSync(a);
}

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
function runLive(cmd, args, onPct) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { windowsHide: true,
      env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }) });
    let out = '', err = '', buf = '';
    function feed(d) {
      buf += d;
      let k;
      while ((k = buf.search(/[\r\n]/)) !== -1) {
        const line = buf.slice(0, k);
        buf = buf.slice(k + 1);
        const m = line.match(/(\d+(?:\.\d+)?)%/);
        if (m && /download/i.test(line)) onPct(Math.min(99, parseFloat(m[1])));
      }
    }
    p.stdout.on('data', d => { out += d; feed(d.toString()); });
    p.stderr.on('data', d => { err += d; feed(d.toString()); });
    p.on('error', reject);
    p.on('close', code => code === 0 ? resolve({ out, err }) : reject(new Error(err.slice(-2000) || ('exit ' + code))));
  });
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
let prog = { stage: 'idle', pct: 0, detail: '' };
const hits = [];
function overLimit(){
  const now = Date.now();
  while (hits.length && now - hits[0] > 24 * 3600 * 1000) hits.shift();
  if (hits.length >= 30) return true;
  let h = 0;
  for (let i = hits.length - 1; i >= 0; i--) { if (now - hits[i] <= 3600 * 1000) h++; else break; }
  return h >= 20;
}
const server = http.createServer((req, res) => {
  if (req.method === 'OPTIONS') { cors(res); res.writeHead(204); res.end(); return; }
  const u = new URL(req.url, 'http://x');
  if (req.method === 'GET' && u.pathname === '/ping') return send(res, 200, { ok: true, busy });
  if (req.method === 'GET' && u.pathname === '/progress') return send(res, 200, { ok: true, busy, stage: prog.stage, pct: prog.pct, detail: prog.detail });
  if (req.method === 'GET' && u.pathname.indexOf('/files/') === 0) {
    /* Kho o cung: phuc vu file + ho tro Range (seek video) */
    cors(res);
    let rel = '';
    try { rel = decodeURIComponent(u.pathname.slice(7)); } catch (e) { res.writeHead(400); res.end(); return; }
    const ffp = path.normalize(path.join(LIB_DIR, rel));
    if (ffp !== LIB_DIR && ffp.indexOf(LIB_DIR + path.sep) !== 0) { res.writeHead(403); res.end(); return; }
    fs.stat(ffp, function (err, fst) {
      if (err || !fst.isFile()) { res.writeHead(404); res.end(); return; }
      const ext = path.extname(ffp).toLowerCase();
      const mime = ext === '.mp4' ? 'video/mp4' : (ext === '.jpg' || ext === '.jpeg') ? 'image/jpeg' : ext === '.webm' ? 'video/webm' : ext === '.m4a' ? 'audio/mp4' : 'application/octet-stream';
      const total = fst.size;
      res.setHeader('Accept-Ranges', 'bytes');
      res.setHeader('Content-Type', mime);
      res.setHeader('Cache-Control', 'public, max-age=86400');
      if (u.searchParams.get('download') === '1') {
        const dn = path.basename(ffp).replace(/"/g, '');
        res.setHeader('Content-Disposition', 'attachment; filename="' + dn + '"; filename*=UTF-8\'\'' + encodeURIComponent(dn));
      }
      const rg = String(req.headers.range || '');
      const m = rg.match(/bytes=(\d*)-(\d*)/);
      if (m) {
        let start = m[1] === '' ? 0 : parseInt(m[1], 10);
        let end = m[2] === '' ? total - 1 : parseInt(m[2], 10);
        if (isNaN(start) || isNaN(end) || start >= total || end < start) { res.writeHead(416); res.end(); return; }
        end = Math.min(end, total - 1);
        res.writeHead(206, { 'Content-Range': 'bytes ' + start + '-' + end + '/' + total, 'Content-Length': end - start + 1 });
        fs.createReadStream(ffp, { start: start, end: end }).pipe(res);
      } else {
        res.writeHead(200, { 'Content-Length': total });
        fs.createReadStream(ffp).pipe(res);
      }
    });
    return;
  }
  if (req.method === 'POST' && u.pathname === '/dl') {
    let body = '';
    req.on('data', c => { body += c; if (body.length > 1e6) req.destroy(); });
    req.on('end', async () => {
      try {
        const j = JSON.parse(body || '{}');
        /* Khong dung token (chu nhan chon tien dung thay bao mat).
           Giu: 1 video/lan + toi da 20 video/gio + 30 video/ngay. */
        if (busy) return send(res, 409, { error: 'may dang tai video khac, doi chut roi bam lai' });
        if (overLimit()) return send(res, 429, { error: 'may nha qua tai (toi da 20 video/gio, 30 video/ngay), doi chut roi bam lai' });
        const url = String(j.url || '');
        if (!/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//.test(url)) return send(res, 400, { error: 'khong phai link youtube' });
        busy = true; hits.push(Date.now());
        prog = { stage: 'dl', pct: 0, detail: '' };
        try {
          const dest0 = j.dest === 'cloud' ? 'cloud' : 'home';
          /* Lay ban dep nhat (1080p-4K 60fps). Kho cloud tu chia theo dung
             luong; kho o cung giu nguyen ban goc. */
          const fmtDefault = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b';
          const fmt = (/^[A-Za-z0-9_*+\/()[\].\-=,:? ]{1,120}$/.test(String(j.format || '')) && j.format) || fmtDefault;
          const tpl = path.join(DL_DIR, Date.now() + '.%(title).60s [%(id)s].%(ext)s');
          const baseArgs = ['-f', fmt, '--merge-output-format', 'mp4',
            '--ffmpeg-location', cfg.ffmpeg, '-o', tpl, '--no-playlist', '--retries', '3', '--newline',
            '--print', 'after_move:filepath', url];
          const onPct = function(p){ prog.pct = p; };
          let r1;
          try { r1 = await runLive(cfg.ytdlp, baseArgs, onPct); }
          catch (e1) {
            /* Luot 2: doi sang android client (vuot kiem tra bot / SABR) */
            prog.pct = 0;
            r1 = await runLive(cfg.ytdlp, ['--extractor-args', 'youtube:player_client=android'].concat(baseArgs), onPct);
          }
          const fp0 = r1.out.trim().split(/\r?\n/).filter(function(l){ return l && l.indexOf('%') === -1; }).pop() || '';
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
          const dest = dest0;
          if (dest === 'home') {
            /* Kho o cung E:/videoserver: giu file, tao anh bia, khong gioi han dung luong */
            if (!ensureDir(LIB_DIR)) throw new Error('khong thay o E:/videoserver (kiem tra o E roi bam lai)');
            const destFp = path.join(LIB_DIR, path.basename(fp));
            try { moveFile(fp, destFp); } catch (e) { throw new Error('khong giu duoc file o cung'); }
            const pub = '/files/' + encodeURIComponent(path.basename(destFp));
            let posterPath = '';
            try {
              prog = { stage: 'up', pct: -1, detail: 'Dang tao anh bia...' };
              const jpg = destFp.replace(/\.[^.]+$/, '.jpg');
              await run(cfg.ffmpeg, ['-hide_banner', '-loglevel', 'error', '-y', '-ss', '1', '-i', destFp, '-vframes', '1', '-vf', 'scale=640:-1', jpg]);
              posterPath = '/files/' + encodeURIComponent(path.basename(jpg));
            } catch (e) { posterPath = ''; }
            busy = false;
            prog = { stage: 'done', pct: 100, detail: '' };
            return send(res, 200, { ok: true, url: pub, host: 'home', path: pub, poster: posterPath, bytes: st.size });
          }
          if (st.size > 200 * 1024 * 1024) {
            busy = false;
            return send(res, 413, { error: 'file ' + Math.round(st.size / 1048576) + 'MB vuot 200MB! File nam o yt-server/dl, up tay len Drive (toi 2GB) nhe' });
          }
          if (st.size > 100 * 1024 * 1024) {
            /* 100-200MB: Cloudinary free khong nhan -> up Catbox (toi da 200MB) */
            prog = { stage: 'up', pct: -1, detail: 'Dang up len Catbox (file 100-200MB, cho vai phut)...' };
            const r2 = await run('curl.exe', ['-sS', '-F', 'reqtype=fileupload',
              '-F', 'fileToUpload=@' + fp, 'https://catbox.moe/user/api.php']);
            const curl = (r2.out || '').trim();
            if (!/^https:\/\/files\.catbox\.moe\//.test(curl)) throw new Error('catbox tu choi: ' + curl.slice(0, 120));
            try { if (ensureDir(LIB_DIR)) moveFile(fp, path.join(LIB_DIR, path.basename(fp))); else fs.unlinkSync(fp); } catch (e) { try { if (fs.existsSync(fp)) fs.unlinkSync(fp); } catch (e2) {} }
            busy = false;
            prog = { stage: 'done', pct: 100, detail: '' };
            return send(res, 200, { ok: true, url: curl, host: 'catbox', bytes: st.size });
          }
          prog = { stage: 'up', pct: -1, detail: 'Dang up len Cloudinary (cho vai phut)...' };
          const r2 = await run('curl.exe', ['-sS', '-X', 'POST',
            'https://api.cloudinary.com/v1_1/' + cfg.cloud + '/video/upload',
            '-F', 'file=@' + fp, '-F', 'upload_preset=' + cfg.preset]);
          let up = {};
          try { up = JSON.parse(r2.out); } catch (e) { throw new Error('cloudinary tra ve la: ' + r2.out.slice(0, 200)); }
          if (!up.secure_url) throw new Error((up.error && up.error.message) || 'cloudinary tu choi');
          try { if (ensureDir(LIB_DIR)) moveFile(fp, path.join(LIB_DIR, path.basename(fp))); else fs.unlinkSync(fp); } catch (e) { try { if (fs.existsSync(fp)) fs.unlinkSync(fp); } catch (e2) {} }
          busy = false;
          prog = { stage: 'done', pct: 100, detail: '' };
          return send(res, 200, { ok: true, url: up.secure_url, host: 'cloudinary', public_id: up.public_id || '', del: up.delete_token || '', bytes: up.bytes || st.size });
        } catch (e) { busy = false; return send(res, 500, { error: String((e && e.message) || e).slice(0, 300) }); }
      } catch (e) { return send(res, 400, { error: 'sai du lieu' }); }
    });
    return;
  }
  send(res, 404, { error: 'not found' });
});

/* ============ WORKER HANG DOI (Firebase) ============
   Dien thoai gui viec vao 'settings/queue', may nha tu ra lay (poll 15s)
   roi tai + up kho + ghi videos + xoa viec. Khong can mo cong,
   tunnel, Tailscale, token hay sua rules. May tat thi viec nam cho. */
const FB_KEY = 'AIzaSyCvCjTJ30HSsHv-oM1H4nngEHhzMyqjLtw';
const FB_DB = 'cinevault-ec9d1-default-rtdb.asia-southeast1.firebasedatabase.app';
let fbT = null;
function httpsReq(method, host, path, body, ctype) {
  const https = require('https');
  return new Promise(function (resolve, reject) {
    const data = (body === undefined || body === null) ? null : (typeof body === 'string' ? body : JSON.stringify(body));
    const rq = https.request({ host: host, path: path, method: method,
      headers: Object.assign({ 'Content-Length': data ? Buffer.byteLength(data) : 0 },
        data ? { 'Content-Type': ctype || 'application/json' } : {}) }, function (rs) {
      let d = '';
      rs.on('data', function (c) { d += c; });
      rs.on('end', function () {
        let j = null;
        try { j = d ? JSON.parse(d) : null; } catch (e) { return reject(new Error('firebase tra ve la')); }
        if (rs.statusCode >= 400) { const em = (j && j.error) || ('http-' + rs.statusCode); return reject(new Error(em)); }
        resolve(j);
      });
    });
    rq.on('error', reject);
    if (data) rq.write(data);
    rq.end();
  });
}
async function fbToken() {
  const now = Date.now();
  if (fbT && fbT.exp > now + 60000) return fbT.id;
  if (fbT && fbT.refresh) {
    try {
      const r = await httpsReq('POST', 'securetoken.googleapis.com', '/v1/token?key=' + FB_KEY,
        'grant_type=refresh_token&refresh_token=' + encodeURIComponent(fbT.refresh), 'application/x-www-form-urlencoded');
      fbT = { id: r.id_token, refresh: r.refresh_token || fbT.refresh, exp: now + (+r.expires_in || 3600) * 1000 };
      return fbT.id;
    } catch (e) { fbT = null; }
  }
  if (!cfg.admin_email || !cfg.admin_pass) throw new Error('server chua co email/pass admin (mo yt-server/config.json dien vao)');
  const r = await httpsReq('POST', 'identitytoolkit.googleapis.com', '/v1/accounts:signInWithPassword?key=' + FB_KEY,
    { email: cfg.admin_email, password: cfg.admin_pass, returnSecureToken: true });
  if (!r.idToken) throw new Error('sai email/pass admin');
  fbT = { id: r.idToken, refresh: r.refreshToken, exp: now + (+r.expiresIn || 3600) * 1000 };
  return fbT.id;
}
async function fbGet(p) {
  const t = await fbToken();
  return httpsReq('GET', FB_DB, '/' + p + '.json?auth=' + t);
}
async function fbPatch(p, o) {
  const t = await fbToken();
  return httpsReq('PATCH', FB_DB, '/' + p + '.json?auth=' + t, o);
}
async function fbPost(p, o) {
  const t = await fbToken();
  return httpsReq('POST', FB_DB, '/' + p + '.json?auth=' + t, o);
}
async function fbDel(p) {
  const t = await fbToken();
  return httpsReq('DELETE', FB_DB, '/' + p + '.json?auth=' + t);
}
function postLocalDl(url, dest, format) {
  return new Promise(function (resolve, reject) {
    const data = JSON.stringify({ url: url, dest: dest || 'cloud', format: format || '' });
    const rq = http.request({ host: '127.0.0.1', port: PORT, path: '/dl', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } }, function (rs) {
      let d = '';
      rs.on('data', function (c) { d += c; });
      rs.on('end', function () {
        let j = {};
        try { j = JSON.parse(d); } catch (e) { return reject(new Error('server loi')); }
        if (j.error) return reject(new Error(j.error));
        resolve(j);
      });
    });
    rq.on('error', reject);
    rq.write(data);
    rq.end();
  });
}
let working = false;
async function queueTick() {
  if (busy || working) return;
  let q = null;
  try { q = await fbGet('settings/queue'); } catch (e) { return; }
  if (!q) return;
  const keys = Object.keys(q).filter(function (k) {
    const it = q[k] || {};
    if (!it.url) return false;
    if (it.stage === 'new' || !it.stage) return true;
    if ((it.stage === 'downloading' || it.stage === 'uploading') && it.claimedAt && Date.now() - it.claimedAt > 30 * 60 * 1000) return true;
    return false;
  });
  if (!keys.length) return;
  keys.sort(function (a, b) { return (q[a].time || 0) - (q[b].time || 0); });
  const key = keys[0], job = q[key];
  if (!/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//.test(String(job.url || ''))) {
    try { await fbDel('settings/queue' + key); } catch (e) {}
    return;
  }
  working = true;
  try {
    await fbPatch('settings/queue' + key, { stage: 'downloading', pct: 0, detail: 'May nha da nhan viec', claimedAt: Date.now() });
    let lastPct = -1, lastStage = '';
    const iv = setInterval(function () {
      fetch('http://127.0.0.1:' + PORT + '/progress').then(function (r) { return r.json(); }).then(function (p) {
        const st = p.stage === 'up' ? 'uploading' : 'downloading';
        const pc = Math.max(0, Math.min(99, Math.round(p.pct || 0)));
        if (st !== lastStage || Math.abs(pc - lastPct) >= 5) {
          lastStage = st; lastPct = pc;
          fbPatch('settings/queue' + key, { stage: st, pct: pc, detail: p.detail || '' }).catch(function () {});
        }
      }).catch(function () {});
    }, 3000);
    let r;
    try { r = await postLocalDl(job.url, job.dest, job.format); }
    finally { clearInterval(iv); }
    const entry = { title: job.title || 'YouTube video', time: Date.now(), cat: job.cat || '' };
    if (r.host === 'home') {
      entry.host = 'home'; entry.path = r.path || ''; entry.poster = r.poster || ''; entry.url = ''; entry.size = r.bytes || 0;
    } else {
      entry.host = r.host || 'cloudinary'; entry.url = r.url; entry.public_id = r.public_id || ''; entry.del = r.del || ''; entry.size = r.bytes || 0;
    }
    await fbPost('videos', entry);
    await fbDel('settings/queue' + key);
  } catch (e) {
    try { await fbPatch('settings/queue' + key, { stage: 'error', detail: String((e && e.message) || e).slice(0, 200) }); } catch (e2) {}
  }
  working = false;
}
setInterval(queueTick, 15000);
setTimeout(queueTick, 8000);
server.listen(PORT, () => {
  console.log('YT server chay o http://127.0.0.1:' + PORT + ' (tat cua so nay = tat server)');
  console.log('Kho video o cung: ' + LIB_DIR + (ensureDir(LIB_DIR) ? ' (san sang)' : ' (CHUA TAO DUOC - kiem tra o E)'));
  console.log('Worker hang doi Firebase: ' + ((cfg.admin_email && cfg.admin_pass) ? 'BAT (poll 15s)' : 'TAT (thieu email/pass trong config.json)'));
  console.log('Gioi han 20 video/gio + 30 video/ngay.');
});
