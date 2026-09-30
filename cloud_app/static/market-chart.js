/* Pure daily-bar transforms and an accessible, dependency-free SVG chart. */
(() => {
  const finite = Number.isFinite;
  const fmt = value => finite(value) ? new Intl.NumberFormat('ko-KR',{maximumFractionDigits:4}).format(value) : '—';
  const axisFmt=value=>new Intl.NumberFormat('ko-KR',{maximumFractionDigits:Math.abs(value)<10?4:2}).format(value);
  function validBars(rows) {
    if(!Array.isArray(rows)) return [];
    const unique=new Map();
    for(const row of rows.slice(0,1100)) {
      if(!row || typeof row!=='object')continue;
      if(!/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !finite(row.close)||row.close<=0||row.close>1e16) continue;
      const stamp=new Date(row.date+'T00:00:00Z');
      if(!finite(stamp.getTime())||stamp.toISOString().slice(0,10)!==row.date)continue;
      const complete=['open','high','low'].every(key=>finite(row[key])&&row[key]>0&&row[key]<=1e16)&&row.low<=Math.min(row.open,row.close)&&row.high>=Math.max(row.open,row.close);
      unique.set(row.date,{date:row.date,close:row.close,open:complete?row.open:null,high:complete?row.high:null,low:complete?row.low:null,volume:finite(row.volume)&&row.volume>=0?row.volume:null});
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
      if(prev) { if(prev.open===null||row.open===null){prev.open=null;prev.high=null;prev.low=null;}else{prev.high=Math.max(prev.high,row.high);prev.low=Math.min(prev.low,row.low);}prev.close=row.close;prev.date=row.date;prev.volume=prev.volume===null||row.volume===null?null:prev.volume+row.volume; }
      else groups.set(key,{...row});
    }
    return [...groups.values()];
  }
  function average(rows,period) {
    return rows.map((row,index)=> index<period-1?null:rows.slice(index-period+1,index+1).reduce((sum,item)=>sum+item.close,0)/period);
  }
  function metrics(rows) {
    if(!rows.length)return null;
    let peak=rows[0].close,drawdown=0,drawdown_peak=peak,drawdown_trough=peak;
    for(const row of rows){peak=Math.max(peak,row.close);const value=(row.close/peak-1)*100;if(value<drawdown){drawdown=value;drawdown_peak=peak;drawdown_trough=row.close;}}
    return {change:rows.length>1?(rows.at(-1).close/rows[0].close-1)*100:null,high:rows.some(r=>finite(r.high))?Math.max(...rows.map(r=>r.high).filter(finite)):null,low:rows.some(r=>finite(r.low))?Math.min(...rows.map(r=>r.low).filter(finite)):null,drawdown:rows.length>1?drawdown:null,drawdown_peak,drawdown_trough};
  }
  function create(svg,tooltip) {
    let visible=[],geometry={width:960,left:88,right:936};
    svg.addEventListener('pointermove',event=>{
      if(!visible.length)return;
      const box=svg.getBoundingClientRect();
      if(!box.width)return;
      const x=(event.clientX-box.left)/box.width*geometry.width;
      const index=Math.max(0,Math.min(visible.length-1,Math.round((x-geometry.left)/(geometry.right-geometry.left)*Math.max(1,visible.length-1))));
      const row=visible[index];
      tooltip.textContent=`${row.date} · 시가 ${fmt(row.open)} · 고가 ${fmt(row.high)} · 저가 ${fmt(row.low)} · 종가 ${fmt(row.close)} · 거래량 ${fmt(row.volume)}${row.open===null?' · OHLC 불완전: 종가만 표시':''}`;
    });
    return {draw(raw,options) {
      visible=aggregate(validBars(raw).filter(row=>row.date>=options.start&&row.date<=options.end),options.interval);
      if(!visible.length){svg.innerHTML='';tooltip.textContent='선택한 기간의 차트 데이터가 없습니다.';return null;}
      const box=svg.getBoundingClientRect();
      const width=Math.max(280,box.width||960),height=Math.max(240,box.height||340);
      const left=88,right=width-22,top=24,bottom=height-(options.volume?104:42);
      geometry={width,left,right};svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
      const low=Math.min(...visible.map(row=>Math.min(row.low??row.close,row.close))),high=Math.max(...visible.map(row=>Math.max(row.high??row.close,row.close)));
      const transform=options.scale==='log'?Math.log:value=>value;
      const rawMin=transform(low),rawMax=transform(high);
      const padding=(rawMax-rawMin)*.06||Math.max(Math.abs(rawMin)*.01,.01);
      const min=rawMin-padding,span=rawMax-rawMin+padding*2;
      const y=value=>bottom-(transform(value)-min)/span*(bottom-top);
      const xScale=index=>visible.length===1?(left+right)/2:left+index/(visible.length-1)*(right-left);
      const polyline=(values,color)=>{
        const points=values.map((value,index)=>finite(value)?[xScale(index),y(value)]:null).filter(Boolean);
        if(points.length===1)return `<circle cx="${points[0][0]}" cy="${points[0][1]}" r="4" fill="${color}"/>`;
        return points.length?`<polyline fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" points="${points.map(p=>p.map(v=>v.toFixed(2)).join(',')).join(' ')}"/>`:'';
      };
      let html='';
      for(let i=0;i<=4;i++){
        const value=options.scale==='log'?Math.exp(min+span*i/4):min+span*i/4;
        const line=bottom-i*(bottom-top)/4;
        html+=`<line x1="${left}" x2="${right}" y1="${line}" y2="${line}" stroke="rgba(170,155,200,.2)"/><text x="${left-8}" y="${line+4}" text-anchor="end">${axisFmt(value)}</text>`;
      }
      if(options.style==='candle') {
        const candleWidth=Math.max(.8,Math.min(12,(right-left)/visible.length*.7));
        html+=visible.map((row,index)=>{if(row.open===null)return `<circle cx="${xScale(index)}" cy="${y(row.close)}" r="2.5" fill="#c3acff"/>`;const color=row.close>=row.open?'#ff8b9e':'#73aaf7';return `<line x1="${xScale(index)}" x2="${xScale(index)}" y1="${y(row.high)}" y2="${y(row.low)}" stroke="${color}"/><rect x="${xScale(index)-candleWidth/2}" y="${Math.min(y(row.open),y(row.close))}" width="${candleWidth}" height="${Math.max(1,Math.abs(y(row.open)-y(row.close)))}" fill="${color}"/>`;}).join('');
      } else html+=polyline(visible.map(row=>row.close),'#c3acff');
      if(options.ma20) html+=polyline(average(visible,20),'#ffd380');
      if(options.ma60) html+=polyline(average(visible,60),'#70dfc7');
      if(options.volume){
        const maximum=Math.max(1,...visible.map(row=>row.volume||0));
        const barWidth=Math.max(1,Math.min(8,(right-left)/visible.length*.7));
        html+=`<text x="${left}" y="${bottom+24}">거래량 · 최대 ${fmt(maximum===1&&!visible.some(row=>row.volume)?0:maximum)}</text>`;
        html+=visible.map((row,index)=>{if(row.volume===null)return '';return `<rect x="${xScale(index)-barWidth/2}" y="${height-34-row.volume/maximum*40}" width="${barWidth}" height="${row.volume/maximum*40}" fill="#9180b0"/>`;}).join('');
      }
      for(const index of [...new Set([0,Math.floor((visible.length-1)/2),visible.length-1])])html+=`<text x="${xScale(index)}" y="${height-10}" text-anchor="${visible.length===1?'middle':index===0?'start':index===visible.length-1?'end':'middle'}">${visible[index].date}</text>`;
      svg.innerHTML=html;
      tooltip.textContent=`${visible[0].date} ~ ${visible.at(-1).date} · ${visible.length}개 봉 · 차트 위에 포인터를 올리면 해당 봉의 가격을 확인할 수 있습니다.`;
      return {...metrics(visible),count:visible.length,rows:visible,first_close:visible[0].close,last_close:visible.at(-1).close};
    }};
  }
  window.MilkywayMarketChart=Object.freeze({validBars,aggregate,average,metrics,create});
})();
