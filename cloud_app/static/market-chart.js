/* Pure daily-bar transforms and an accessible, dependency-free SVG chart. */
(() => {
  const finite = Number.isFinite;
  const fmt = value => finite(value) ? new Intl.NumberFormat('ko-KR',{maximumFractionDigits:4}).format(value) : '—';
  function validBars(rows) {
    if(!Array.isArray(rows)) return [];
    const unique=new Map();
    for(const row of rows.slice(0,1100)) {
      if(!row || typeof row!=='object')continue;
      if(!/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !['open','high','low','close'].every(key=>finite(row[key])&&row[key]>0&&row[key]<=1e16)) continue;
      const stamp=new Date(row.date+'T00:00:00Z');
      if(!finite(stamp.getTime())||stamp.toISOString().slice(0,10)!==row.date)continue;
      if(row.low>Math.min(row.open,row.close) || row.high<Math.max(row.open,row.close)) continue;
      unique.set(row.date,{...row,volume:finite(row.volume)&&row.volume>=0?row.volume:null});
    }
    return [...unique.values()].sort((a,b)=>a.date.localeCompare(b.date));
  }
  function aggregate(rows,interval) {
    if(interval==='day') return rows.map(row=>({...row}));
    const groups=new Map();
    for(const row of rows) {
      const date=new Date(row.date+'T00:00:00Z');
      if(interval==='week')date.setUTCDate(date.getUTCDate()-(date.getUTCDay()+6)%7);
      const key=interval==='month'?row.date.slice(0,7):date.toISOString().slice(0,10);
      const prev=groups.get(key);
      if(prev) { prev.high=Math.max(prev.high,row.high);prev.low=Math.min(prev.low,row.low);prev.close=row.close;prev.date=row.date;prev.volume=prev.volume===null||row.volume===null?null:prev.volume+row.volume; }
      else groups.set(key,{...row});
    }
    return [...groups.values()];
  }
  function average(rows,period) {
    return rows.map((row,index)=> index<period-1?null:rows.slice(index-period+1,index+1).reduce((sum,item)=>sum+item.close,0)/period);
  }
  function metrics(rows) {
    if(rows.length<2)return null;
    let peak=rows[0].close,drawdown=0;
    for(const row of rows){peak=Math.max(peak,row.close);drawdown=Math.min(drawdown,(row.close/peak-1)*100);}
    return {change:(rows.at(-1).close/rows[0].close-1)*100,high:Math.max(...rows.map(r=>r.high)),low:Math.min(...rows.map(r=>r.low)),drawdown};
  }
  function create(svg,tooltip) {
    let visible=[],xScale;
    svg.addEventListener('pointermove',event=>{
      if(!visible.length)return;
      const box=svg.getBoundingClientRect();
      const x=(event.clientX-box.left)/box.width*960;
      const index=Math.max(0,Math.min(visible.length-1,Math.round((x-76)/864*Math.max(1,visible.length-1))));
      const row=visible[index];
      tooltip.textContent=`${row.date} · 시가 ${fmt(row.open)} · 고가 ${fmt(row.high)} · 저가 ${fmt(row.low)} · 종가 ${fmt(row.close)} · 거래량 ${fmt(row.volume)}`;
    });
    return {draw(raw,options) {
      visible=aggregate(validBars(raw).filter(row=>row.date>=options.start&&row.date<=options.end),options.interval);
      if(!visible.length){svg.innerHTML='';tooltip.textContent='선택한 기간의 차트 데이터가 없습니다.';return null;}
      const low=Math.min(...visible.map(row=>row.low)),high=Math.max(...visible.map(row=>row.high));
      const transform=options.scale==='log'?Math.log:value=>value;
      const min=transform(low),span=transform(high)-min||1;
      const y=value=>290-(transform(value)-min)/span*240;
      xScale=index=>76+index/Math.max(1,visible.length-1)*864;
      const polyline=(values,color)=>{
        const points=values.map((value,index)=>finite(value)?`${xScale(index).toFixed(2)},${y(value).toFixed(2)}`:null).filter(Boolean).join(' ');
        return points?`<polyline fill="none" stroke="${color}" stroke-width="2" points="${points}"/>`:'';
      };
      let html='';
      for(let i=0;i<=4;i++){
        const value=options.scale==='log'?Math.exp(min+span*i/4):min+span*i/4;
        const line=290-i*60;
        html+=`<line x1="76" x2="940" y1="${line}" y2="${line}" stroke="rgba(170,155,200,.14)"/><text x="68" y="${line+4}" text-anchor="end">${fmt(value)}</text>`;
      }
      if(options.style==='candle') {
        const width=Math.max(.7,Math.min(12,600/visible.length));
        html+=visible.map((row,index)=>{const color=row.close>=row.open?'#ff8b9e':'#73aaf7';return `<line x1="${xScale(index)}" x2="${xScale(index)}" y1="${y(row.high)}" y2="${y(row.low)}" stroke="${color}"/><rect x="${xScale(index)-width/2}" y="${Math.min(y(row.open),y(row.close))}" width="${width}" height="${Math.max(1,Math.abs(y(row.open)-y(row.close)))}" fill="${color}"/>`;}).join('');
      } else html+=polyline(visible.map(row=>row.close),'#b9a0ff');
      if(options.ma20) html+=polyline(average(visible,20),'#ffd380');
      if(options.ma60) html+=polyline(average(visible,60),'#70dfc7');
      if(options.volume){const maximum=Math.max(1,...visible.map(row=>row.volume||0));html+=visible.map((row,index)=>`<rect x="${xScale(index)-1}" y="${355-(row.volume||0)/maximum*42}" width="2" height="${(row.volume||0)/maximum*42}" fill="#655783"/>`).join('');}
      for(const index of [...new Set([0,Math.floor((visible.length-1)/2),visible.length-1])])html+=`<text x="${xScale(index)}" y="382" text-anchor="${index===0?'start':index===visible.length-1?'end':'middle'}">${visible[index].date}</text>`;
      svg.innerHTML=html;
      tooltip.textContent=`${visible[0].date} ~ ${visible.at(-1).date} · ${visible.length}개 봉 · 차트 위에 포인터를 올리면 해당 봉의 가격을 확인할 수 있습니다.`;
      return {...metrics(visible),count:visible.length,rows:visible};
    }};
  }
  window.MilkywayMarketChart=Object.freeze({validBars,aggregate,average,metrics,create});
})();
