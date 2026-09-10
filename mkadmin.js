const admin = require('firebase-admin');
const auth = require('firebase-admin/auth');
const sa = require('C:/Users/HP/Downloads/cinevault-ec9d1-c444c3b53ff5.json');
admin.initializeApp({credential: admin.cert(sa)});
auth.getAuth().createUser({email: 'duoc7919@gmail.com', password: 'thanhduoc1234511', displayName: 'Admin'})
  .then(u => { console.log('TAO TAI KHOAN OK: ' + u.uid); process.exit(0); })
  .catch(e => { console.log('ERR: ' + e.code + ' - ' + e.message); process.exit(1); });
