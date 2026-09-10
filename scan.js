const fs = require('fs');
const d = 'C:/Users/HP/OneDrive/Documents/Default Project/';
['Acceleratorares.html', 'admin.html'].forEach((f) => {
  const t = fs.readFileSync(d + f, 'utf8');
  console.log('=== ' + f + ': ' + t.length + ' bytes ===');
  // 1. ID duoc JS goi nhung khong co trong HTML
  const ids = [...new Set([...t.matchAll(/getElementById\("([^"]+)"\)/g)].map(m => m[1]))];
  const deadIds = ids.filter(id => !t.includes('id="' + id + '"'));
  console.log('ID thua: ' + (deadIds.length ? deadIds.join(', ') : 'khong co'));
  // 2. Ham dinh nghia nhung khong bao gio goi (tru onclick= trong HTML)
  const funcs = [...new Set([...t.matchAll(/function (\w+)\(/g)].map(m => m[1]))];
  const never = funcs.filter(fn => {
    const inJs = (t.split('function ' + fn).length - 1);
    const inHtml = (t.split(fn + '(').length - 1) - inJs;
    return inHtml <= 0 && inJs <= 1;
  });
  console.log('Ham chet: ' + (never.length ? never.join(', ') : 'khong co'));
  // 3. class CSS dinh nghia nhung khong dung
  const defs = [...new Set([...t.matchAll(/\.([a-zA-Z][\w-]*)\s*\{/g)].map(m => m[1]))];
  const unused = defs.filter(c => {
    const total = (t.split(c).length - 1);
    const inDef = 1;
    return total <= inDef;
  });
  console.log('CSS thua: ' + (unused.length ? unused.join(', ') : 'khong co'));
});
