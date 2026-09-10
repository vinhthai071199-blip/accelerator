const admin = require('firebase-admin');
const auth = require('firebase-admin/auth');
const sa = require('C:/Users/HP/Downloads/cinevault-ec9d1-c444c3b53ff5.json');
admin.initializeApp({credential: admin.cert(sa)});

auth.getAuth().createCustomToken('LDa2nYFq8iY9XdhuMY1Rx8kjoPG2')
  .then(tok => {
    const https = require('https');
    const post = (url, data) => new Promise((res, rej) => {
      const u = new URL(url);
      const req = https.request(u, {method: 'POST', headers: {'Content-Type': 'application/json'}}, r => {
        let b = ''; r.on('data', c => b += c); r.on('end', () => res(JSON.parse(b)));
      });
      req.on('error', rej); req.write(JSON.stringify(data)); req.end();
    });
    const get = url => new Promise((res, rej) => {
      https.get(url, r => { let b=''; r.on('data', c=>b+=c); r.on('end',()=>res({code:r.statusCode, body:b})); }).on('error', rej);
    });
    return post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyCvCjTJ30HSsHv-oM1H4nngEHhzMyqjLtw', {token: tok, returnSecureToken: true})
      .then(r => get('https://cinevault-ec9d1-default-rtdb.asia-southeast1.firebasedatabase.app/feedback.json?auth=' + r.idToken))
      .then(r => { console.log('AUTH READ HTTP ' + r.code + ': ' + (r.body || '(null)').slice(0, 100)); process.exit(0); });
  })
  .catch(e => { console.log('ERR: ' + e.message); process.exit(1); });
