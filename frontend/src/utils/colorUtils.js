// hex ↔ rgb helpers + linear interp
function hexToRgb(h) {
  const m = h.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
  return m
    ? [parseInt(m[1],16), parseInt(m[2],16), parseInt(m[3],16)]
    : [0,0,0];
}
function rgbToHex([r,g,b]) {
  return "#" + [r,g,b].map(v=>{
    const s=v.toString(16);
    return s.length==1?'0'+s:s;
  }).join("");
}
function lerp(a,b,t){return a + (b-a)*t;}
function interpColor(c1, c2, t){
  const [r1,g1,b1]=hexToRgb(c1), [r2,g2,b2]=hexToRgb(c2);
  return rgbToHex([lerp(r1,r2,t)|0, lerp(g1,g2,t)|0, lerp(b1,b2,t)|0]);
}


export function triColorGradient(c1, c2, c3, n) {
  const out = [];
  const mid = Math.floor((n - 1) / 2);
  for (let i = 0; i < n; i++) {
    let t, col;
    if (i <= mid) {
      t = mid > 0 ? i / mid : 0;
      col = interpColor(c1, c2, t);
    } else {
      t = (i - mid) / (n - 1 - mid);
      col = interpColor(c2, c3, t);
    }
    out.push(col);
  }
  return out;
}

export {
  hexToRgb,
  rgbToHex,
  lerp,
  interpColor
};