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
const CODE_V = 9;
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
function sleepMs(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
async function runRetry(cmd, args, tries, delayMs) {
  let err = null;
  for (let i = 0; i < tries; i++) {
    try { return await run(cmd, args); }
    catch (e) { err = e; if (i + 1 < tries) await sleepMs(delayMs); }
  }
  throw err;
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
    p.on('close', code => {
      if (code === 0) return resolve({ out, err });
      const e2 = new Error(err.slice(-2000) || ('exit ' + code));
      e2.out = out; e2.err = err;
      reject(e2);
    });
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
  if (req.method === 'GET' && u.pathname === '/ping') return send(res, 200, { ok: true, busy, v: CODE_V });
  if (req.method === 'GET' && u.pathname === '/progress') return send(res, 200, { ok: true, busy, stage: prog.stage, pct: prog.pct, detail: prog.detail });
  if (req.method === 'GET' && u.pathname.indexOf('/files/') === 0) {
    /* Kho o cung: phuc vu file + ho tro Range (seek video) */
    cors(res);
    let rel = '';
    try { rel = decodeURIComponent(u.pathname.slice(7)); } catch (e) { res.writeHead(400); res.end(); return; }
    const ffp = path.normalize(path.join(LIB_DIR, rel));
    if (ffp !== LIB_DIR && ffp.indexOf(LIB_DIR + path.sep) !== 0) { res.writeHead(403); res.end(); return; }
    fs.stat(ffp, function (err, fst) {
      try {
      if (err || !fst.isFile()) { res.writeHead(404); res.end(); return; }
      const ext = path.extname(ffp).toLowerCase();
      const mime = ext === '.mp4' ? 'video/mp4' : (ext === '.jpg' || ext === '.jpeg') ? 'image/jpeg' : ext === '.webm' ? 'video/webm' : ext === '.m4a' ? 'audio/mp4' : 'application/octet-stream';
      const total = fst.size;
      res.setHeader('Accept-Ranges', 'bytes');
      res.setHeader('Content-Type', mime);
      res.setHeader('Cache-Control', 'public, max-age=86400');
      if (u.searchParams.get('download') === '1') {
        /* Ten file co the chua tieng Nhat/Han/emoji (vuot ASCII) -> Node
           nem loi chet server. Tach: ten ASCII cho filename, ten goc cho filename*. */
        const raw = path.basename(ffp).replace(/"/g, '');
        const ascii = raw.replace(/[^\x20-\x7e]/g, '').trim() || 'video.mp4';
        let star = '';
        try { star = "; filename*=UTF-8''" + encodeURIComponent(raw); } catch (e) {}
        res.setHeader('Content-Disposition', 'attachment; filename="' + ascii + '"' + star);
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
      } catch (e) { try { if (!res.headersSent) res.writeHead(500); res.end(); } catch (e2) {} }
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
        if (busy) return send(res, 409, { error: 'Máy đang tải video khác, đợi chút rồi bấm lại' });
        if (overLimit()) return send(res, 429, { error: 'Máy nhà quá tải (tối đa 20 video/giờ, 30 video/ngày), đợi chút rồi bấm lại' });
        const url = String(j.url || '');
        if (!/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//.test(url)) return send(res, 400, { error: 'Không phải link YouTube' });
        busy = true; hits.push(Date.now());
        prog = { stage: 'dl', pct: 0, detail: '' };
        try {
          const dest0 = j.dest === 'cloud' ? 'cloud' : (j.dest === 'litter' ? 'litter' : 'home');
          /* Lay ban dep nhat (1080p-4K 60fps). Kho cloud tu chia theo dung
             luong; kho o cung giu nguyen ban goc. */
          const fmtDefault = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b';
          const fmt = (/^[A-Za-z0-9_*+\/()[\].\-=,:? ]{1,120}$/.test(String(j.format || '')) && j.format) || fmtDefault;
          const tpl = path.join(DL_DIR, Date.now() + '.%(title).60s [%(id)s].%(ext)s');
          /* Thu tu client: web truoc (giu hanh vi cu), rot xuong web_embedded
             roi android khi YouTube bat kiem tra bot / SABR */
          const baseArgs = ['-f', fmt, '--merge-output-format', 'mp4',
            '--ffmpeg-location', cfg.ffmpeg, '-o', tpl, '--no-playlist', '--retries', '3', '--newline',
            '--extractor-args', 'youtube:player_client=web,web_embedded,android',
            '--print', 'after_move:filepath', url];
          const onPct = function(p){ prog.pct = p; };
          const r1 = await runLive(cfg.ytdlp, baseArgs, onPct);
          const fp0 = r1.out.trim().split(/\r?\n/).filter(function(l){ return l && l.indexOf('%') === -1; }).pop() || '';
          let fp = fp0, st = null;
          try { st = fs.statSync(fp); } catch (e) { st = null; }
          if (!st) {
            /* Du phong: ten in ra lech encoding thi lay file mp4 moi nhat trong dl/ */
            const cands = fs.readdirSync(DL_DIR).map(function (n) {
              const p = path.join(DL_DIR, n);
              try { return { p, m: fs.statSync(p).mtimeMs }; } catch (e) { return null; }
            }).filter(Boolean).sort((a, b) => b.m - a.m);
            if (!cands.length || Date.now() - cands[0].m > 15 * 60 * 1000) throw new Error('Tải xong nhưng không thấy file (bấm lại lần nữa)');
            fp = cands[0].p;
            st = fs.statSync(fp);
          }
          /* Chong ban cuc thap (bot-check chi nha 360p): duoi 720p thi bo file, bao thu lai.
             ffmpeg -i khong file ra luon exit != 0 nen doc kich thuoc tu output cua loi. */
          try {
            await run(cfg.ffmpeg, ['-hide_banner', '-i', fp]);
          } catch (e) {
            const dump = ((e && e.err) || '') + '\n' + ((e && e.out) || '');
            const mm2 = dump.match(/Video:[^\n]*?(\d{3,5})x(\d{3,5})/);
            const hh = mm2 ? parseInt(mm2[2], 10) : 0;
            if (hh && hh < 720) {
              try { if (fs.existsSync(fp)) fs.unlinkSync(fp); } catch (e2) {}
              throw new Error('YouTube chỉ nhả bản thấp lúc này, gửi lại sau ít phút để lấy bản đẹp');
            }
          }
          const dest = dest0;
          if (dest === 'litter') {
            /* Kho tam Litterbox: toi da 1GB, tu huy sau 1h. Khong luu E:. */
            if (st.size > 1024 * 1024 * 1024) {
              busy = false;
              return send(res, 413, { error: 'File ' + Math.round(st.size / 1048576) + 'MB vượt 1GB! Up tay lên Drive (tới 2GB) nhé' });
            }
            prog = { stage: 'up', pct: -1, detail: 'Đang up lên Litterbox (tạm 1h, chờ vài phút)...' };
            const r2 = await runRetry('curl.exe', ['-sS', '-F', 'reqtype=fileupload', '-F', 'time=1h',
              '-F', 'fileToUpload=@' + fp, 'https://litterbox.catbox.moe/resources/internals/api.php'], 3, 15000);
            const curl = (r2.out || '').trim();
            if (!/^https:\/\/litter\.catbox\.moe\//.test(curl)) throw new Error('litterbox từ chối: ' + curl.slice(0, 120));
            try { if (fs.existsSync(fp)) fs.unlinkSync(fp); } catch (e) {}
            busy = false;
            prog = { stage: 'done', pct: 100, detail: '' };
            return send(res, 200, { ok: true, url: curl, host: 'litterbox', bytes: st.size });
          }
          if (dest === 'home') {
            /* Kho o cung E:/videoserver: giu file, tao anh bia, khong gioi han dung luong */
            if (!ensureDir(LIB_DIR)) throw new Error('Không thấy ổ E:/videoserver (kiểm tra ổ E rồi bấm lại)');
            const destFp = path.join(LIB_DIR, path.basename(fp));
            try { moveFile(fp, destFp); } catch (e) { throw new Error('Không giữ được file ở ổ cứng'); }
            const pub = '/files/' + encodeURIComponent(path.basename(destFp));
            let posterPath = '';
            try {
              prog = { stage: 'up', pct: -1, detail: 'Đang tạo ảnh bìa...' };
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
            return send(res, 413, { error: 'File ' + Math.round(st.size / 1048576) + 'MB vượt 200MB! File nằm ở E:/videoserver, up tay lên Drive (tới 2GB) nhé' });
          }
          if (st.size > 100 * 1024 * 1024) {
            /* 100-200MB: Cloudinary free khong nhan -> up Catbox (toi da 200MB) */
            prog = { stage: 'up', pct: -1, detail: 'Đang up lên Catbox (file 100–200MB, chờ vài phút)...' };
            const r2 = await runRetry('curl.exe', ['-sS', '-F', 'reqtype=fileupload',
              '-F', 'fileToUpload=@' + fp, 'https://catbox.moe/user/api.php'], 3, 15000);
            const curl = (r2.out || '').trim();
            if (!/^https:\/\/files\.catbox\.moe\//.test(curl)) throw new Error('catbox tu choi: ' + curl.slice(0, 120));
            try { if (ensureDir(LIB_DIR)) moveFile(fp, path.join(LIB_DIR, path.basename(fp))); else fs.unlinkSync(fp); } catch (e) { try { if (fs.existsSync(fp)) fs.unlinkSync(fp); } catch (e2) {} }
            busy = false;
            prog = { stage: 'done', pct: 100, detail: '' };
            return send(res, 200, { ok: true, url: curl, host: 'catbox', bytes: st.size });
          }
          prog = { stage: 'up', pct: -1, detail: 'Đang up lên Cloudinary (chờ vài phút)...' };
          const r2 = await runRetry('curl.exe', ['-sS', '-X', 'POST',
            'https://api.cloudinary.com/v1_1/' + cfg.cloud + '/video/upload',
            '-F', 'file=@' + fp, '-F', 'upload_preset=' + cfg.preset], 3, 15000);
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
  if (!cfg.admin_email || !cfg.admin_pass) throw new Error('Server chưa có email/pass admin (mở yt-server/config.json điền vào)');
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
/* Loi ky thuat (tieng Anh) -> cau tieng Viet hien cho admin.
   Chi tiet goc giu trong console cua so server de sua loi. */
function friendlyErr(msg) {
  msg = String(msg || '');
  if (/gửi lại sau|bản thấp|bản đẹp/i.test(msg)) return msg;
  if (/unavailable|private video|deleted|not found| 404/i.test(msg)) return 'Video gốc không còn (bị xóa, ẩn hoặc khóa vùng)';
  if (/sign in|log in|cookie|bot|captcha|SABR/i.test(msg)) return 'YouTube chặn tải tự động lúc này, gửi lại sau ít phút';
  if (/catbox/i.test(msg)) return 'Kho Catbox từ chối lúc này, gửi lại sau';
  if (/cloudinary|size limit|File size|100 ?MB/i.test(msg)) return 'File vượt giới hạn kho, thử lại hoặc đổi kho khác';
  if (/quota|credit/i.test(msg)) return 'Kho Cloud hết quota tháng này';
  if (/email\/pass|sai email/i.test(msg)) return 'Sai email/pass admin trong config, kiểm tra lại';
  if (/o E:|E:\/videoserver/i.test(msg)) return 'Không thấy ổ E, kiểm tra ổ cứng rồi gửi lại';
  return 'Máy nhà bận/không tải được lúc này, gửi lại sau ít phút';
}
async function queueTick() {
  if (busy || working) return;
  let q = null;
  try { q = await fbGet('settings/queue'); } catch (e) { return; }
  if (!q) return;
  const keys = Object.keys(q).filter(function (k) {
    const it = q[k] || {};
    if (!it.url) return false;
    if (it.stage === 'new' || !it.stage) return true;
    if (it.stage === 'waiting' && it.retryAt && Date.now() >= it.retryAt) return true;
    if ((it.stage === 'downloading' || it.stage === 'uploading') && it.claimedAt && Date.now() - it.claimedAt > 30 * 60 * 1000) return true;
    return false;
  });
  if (!keys.length) return;
  keys.sort(function (a, b) { return (q[a].time || 0) - (q[b].time || 0); });
  const key = keys[0], job = q[key];
  if (!/^https?:\/\/(www\.|m\.)?(youtube\.com|youtu\.be)\//.test(String(job.url || ''))) {
    try { await fbDel('settings/queue/' + key); } catch (e) {}
    return;
  }
  working = true;
  try {
    await fbPatch('settings/queue/' + key, { stage: 'downloading', pct: 0, detail: 'Máy nhà đã nhận việc', claimedAt: Date.now() });
    let lastPct = -1, lastStage = '';
    const iv = setInterval(function () {
      fetch('http://127.0.0.1:' + PORT + '/progress').then(function (r) { return r.json(); }).then(function (p) {
        const st = p.stage === 'up' ? 'uploading' : 'downloading';
        const pc = Math.max(0, Math.min(99, Math.round(p.pct || 0)));
        if (st !== lastStage || Math.abs(pc - lastPct) >= 5) {
          lastStage = st; lastPct = pc;
          fbPatch('settings/queue/' + key, { stage: st, pct: pc, detail: p.detail || '' }).catch(function () {});
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
    if (r.host === 'litterbox') entry.expiresAt = Date.now() + 1 * 3600 * 1000;
    await fbPost('videos', entry);
    await fbDel('settings/queue/' + key);
  } catch (e) {
    const msg = String((e && e.message) || e);
    try { console.error('[worker] loi ky thuat:', msg); } catch (e3) {}
    const attempts = (job.attempts || 0) + 1;
    const perm = /không còn|bị xóa|khóa vùng|không phải link|vượt \d+MB|vượt 1GB|sai email|không thấy ổ|o E:/i.test(msg);
    if (!perm && attempts <= 3) {
      const waitMin = [10, 30, 60][attempts - 1] || 60;
      try { await fbPatch('settings/queue/' + key, { stage: 'waiting', retryAt: Date.now() + waitMin * 60000, attempts: attempts, detail: 'Bận tạm, tự thử lại sau ' + waitMin + ' phút (lần ' + attempts + '/3)' }); } catch (e2) {}
    } else {
      try { await fbPatch('settings/queue/' + key, { stage: 'error', attempts: attempts, detail: friendlyErr(msg), tech: msg.slice(0, 300) }); } catch (e2) {}
    }
  }
  working = false;
}
setInterval(queueTick, 15000);
setTimeout(queueTick, 8000);

/* ============ TU XOA VIDEO HET HAN ============
   Video kho tam (Litterbox) qua 1h thi xoa khoi web (file goc tren
   Litterbox cung tu huy). Quet 10 phut/lan, moi lan toi da 20 muc. */
async function sweepExpired() {
  let v = null;
  try { v = await fbGet('videos'); } catch (e) { return; }
  if (!v) return;
  const now = Date.now();
  const olds = Object.keys(v).filter(function (k) {
    const r = v[k] || {};
    return r.expiresAt && now > r.expiresAt;
  }).slice(0, 20);
  for (const k of olds) {
    try { await fbDel('videos/' + k); console.log('Tu xoa video het han: ' + k); } catch (e) {}
  }
}
setInterval(sweepExpired, 10 * 60 * 1000);
setTimeout(sweepExpired, 30000);

/* ============ TU NUOI TUNNEL ============
   Bat YT_TUNNEL=1 (hoac config tunnel:true): server tu mo cloudflared,
   chet tu dung lai, doi link tu cap nhat Firebase + file tun-url.txt.
   YT_TUNNEL=file: chi ghi file (de test, khong dung Firebase). */
const TUN_MODE = process.env.YT_TUNNEL || (cfg.tunnel ? '1' : '');
const TUN_FILE = path.join(ROOT, 'tun-url.txt');
let tunProc = null, tunUrl = '', tunBad = 0;
async function pushBase(url) {
  try { fs.writeFileSync(TUN_FILE, url); } catch (e) {}
  if (TUN_MODE !== '1') return;
  try {
    const cur = await fbGet('settings/ytServerBase').catch(function () { return null; });
    if (cur === url) return;
    await fbPatch('settings', { ytServerBase: url });
    console.log('Tunnel moi, da cap nhat dia chi web: ' + url);
  } catch (e) { console.log('Chua cap nhat duoc dia chi web (se thu lai khi link doi)'); }
}
function tunnelTick() {
  if (!TUN_MODE) return;
  const cf = path.join(ROOT, '..', 'tools', 'cloudflared.exe');
  if (!fs.existsSync(cf)) { console.log('Muon tunnel: thieu tools/cloudflared.exe'); return; }
  if (tunProc && tunProc.exitCode === null) return;
  tunProc = spawn(cf, ['tunnel', '--url', 'http://127.0.0.1:' + PORT], { windowsHide: true });
  tunProc.stderr.on('data', function (d) {
    const m = String(d).match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/);
    if (m && m[0] !== tunUrl) {
      tunUrl = m[0]; tunBad = 0;
      console.log('Tunnel public: ' + tunUrl);
      pushBase(tunUrl);
    }
  });
  tunProc.on('exit', function () {
    tunProc = null;
    setTimeout(tunnelTick, 5000);
  });
}
async function tunnelLive() {
  if (!TUN_MODE || !tunUrl) return;
  try {
    const r = await fetch(tunUrl + '/ping');
    const j = await r.json().catch(function () { return {}; });
    if (r.ok && j.ok) { tunBad = 0; return; }
    throw new Error('bad');
  } catch (e) {
    tunBad++;
    if (tunBad >= 2 && tunProc && tunProc.exitCode === null) {
      console.log('Tunnel chet (mat ket noi) - dung lai...');
      try { tunProc.kill(); } catch (e2) {}
      tunProc = null;
    }
  }
}
setInterval(tunnelTick, 30000);
setInterval(tunnelLive, 60000);
setTimeout(tunnelTick, 5000);
process.on('SIGINT', function () {
  try {
    if (TUN_MODE === '1' && tunUrl) {
      fbGet('settings/ytServerBase').catch(function () { return ''; }).then(function (cur) {
        if (cur === tunUrl) fbPatch('settings', { ytServerBase: '' }).catch(function () {});
      });
    }
  } catch (e) {}
  setTimeout(function () { process.exit(0); }, 1500);
});
process.on('uncaughtException', function (e) {
  try { console.error('LOI bat ngo (server van chay):', (e && e.message) || e); } catch (e2) {}
});
server.listen(PORT, () => {
  console.log('YT server chay o http://127.0.0.1:' + PORT + ' (tat cua so nay = tat server)');
  console.log('Kho video o cung: ' + LIB_DIR + (ensureDir(LIB_DIR) ? ' (san sang)' : ' (CHUA TAO DUOC - kiem tra o E)'));
  console.log('Worker hang doi Firebase: ' + ((cfg.admin_email && cfg.admin_pass) ? 'BAT (poll 15s)' : 'TAT (thieu email/pass trong config.json)'));
  console.log('Gioi han 20 video/gio + 30 video/ngay.');
});
