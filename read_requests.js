const admin = require('firebase-admin');
const database = require('firebase-admin/database');
const sa = require('C:/Users/HP/Downloads/cinevault-ec9d1-c444c3b53ff5.json');
admin.initializeApp({credential: admin.cert(sa), databaseURL: 'https://cinevault-ec9d1-default-rtdb.asia-southeast1.firebasedatabase.app'});
const db = database.getDatabase();

function fmtTime(t) {
  if (!t) return '?';
  const d = new Date(typeof t === 'number' ? t : Date.parse(t));
  if (isNaN(d.getTime())) return String(t);
  return d.toLocaleString('vi-VN', {timeZone: 'Asia/Ho_Chi_Minh'});
}

db.ref('requests').once('value').then(s => {
  const v = s.val();
  if (!v) { console.log('(KHONG CO YEU CAU NAO)'); process.exit(0); }
  const list = Object.entries(v).sort((a,b) => (b[1].ts||0)-(a[1].ts||0));
  console.log('TONG CONG: ' + list.length + ' yeu cau');
  list.forEach(([k, r]) => {
    console.log('=========================================');
    console.log('ID: ' + k);
    console.log('Ten: ' + (r.name || '?'));
    console.log('Loai: ' + (r.type || '?'));
    console.log('Noi dung: ' + (r.content || r.message || '?'));
    console.log('Thoi gian: ' + fmtTime(r.ts || r.time || r.timestamp));
  });
  process.exit(0);
}).catch(e => { console.log('ERR: ' + e.message); process.exit(1); });
