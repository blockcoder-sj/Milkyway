/* Pure daily-bar transforms and an accessible, dependency-free SVG chart. */
(() => {
  const finite = Number.isFinite;
  const MOVING_AVERAGES=Object.freeze([
    Object.freeze({period:5,color:'#e5e9f2'}), Object.freeze({period:20,color:'#f2c761'}),
    Object.freeze({period:60,color:'#53cdb5'}), Object.freeze({period:120,color:'#aa92ee'})
  ]);
  const DEFAULTS=Object.freeze({style:'candle',scale:'linear',interval:'day',volume:false,ma5:true,ma20:true,ma60:true,ma120:true});
  const fmt = (value,digits=2) => finite(value) ? new Intl.NumberFormat('ko-KR',{maximumFractionDigits:digits}).format(value) : '—';
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
  function prepare(raw,options) {
    // Include preceding completed bars for SMA warm-up; never include a later bar.
    const all=aggregate(validBars(raw).filter(row=>row.date<=options.end),options.interval);
    const offset=all.findIndex(row=>row.date>=options.start);
    if(offset<0)return {rows:[],averages:[]};
    return {rows:all.slice(offset),averages:MOVING_AVERAGES.filter(ma=>options['ma'+ma.period])
      .map(ma=>({...ma,values:average(all,ma.period).slice(offset)}))};
  }
  function create(svg,tooltip,legend) {
    let visible=[],averages=[],geometry=null,crosshair=null,digits=2;
    function readout(index) {
      const row=visible[index];if(!row)return;
      tooltip.innerHTML=`<time>${row.date}</time>`+[['시',row.open],['고',row.high],['저',row.low],['종',row.close]]
        .map(([label,value])=>`<span>${label} <b>${fmt(value,digits)}</b></span>`).join('');
      if(legend)legend.innerHTML=averages.map(ma=>`<span class="market-ma" data-ma="${ma.period}"><i></i>MA ${ma.period} <b>${fmt(ma.values[index],digits)}</b></span>`).join('');
    }
    function resetCursor(){
      crosshair?.setAttribute('visibility','hidden');
      if(visible.length)readout(visible.length-1);
    }
    svg.addEventListener('pointerleave',resetCursor);
    svg.addEventListener('pointermove',event=>{
      if(!visible.length||!geometry)return;
      const box=svg.getBoundingClientRect();if(!box.width||!box.height)return;
      const {width,height,left,right,top,bottom,xScale,inverseY,step}=geometry;
      const pointerX=(event.clientX-box.left)/box.width*width;
      const pointerY=(event.clientY-box.top)/box.height*height;
      if(!finite(pointerX)||!finite(pointerY)||pointerX<left||pointerX>right||pointerY<top||pointerY>bottom){resetCursor();return;}
      const index=Math.max(0,Math.min(visible.length-1,Math.round((pointerX-left)/step-.5)));
      readout(index);if(!crosshair)return;
      const x=xScale(index),dateX=Math.max(left,Math.min(right-92,x-46));
      crosshair.innerHTML=`<path d="M ${x} ${top} V ${bottom} M ${left} ${pointerY} H ${right}" fill="none" stroke="#768296" stroke-width=".8" stroke-dasharray="3 4"/>
        <rect x="${right+1}" y="${pointerY-10}" width="84" height="20" rx="3" fill="#343f51"/>
        <text class="chart-badge" x="${right+7}" y="${pointerY+4}">${axisFmt(inverseY(pointerY))}</text>
        <rect x="${dateX}" y="${height-25}" width="92" height="21" rx="3" fill="#343f51"/>
        <text class="chart-badge" x="${dateX+46}" y="${height-10}" text-anchor="middle">${visible[index].date}</text>`;
      crosshair.setAttribute('visibility','visible');
    });
    return {draw(raw,settings) {
      const options={...DEFAULTS,...settings},prepared=prepare(raw,options);
      visible=prepared.rows;averages=prepared.averages;geometry=null;crosshair=null;digits=[2,3,4].includes(options.digits)?options.digits:2;
      if(!visible.length){svg.innerHTML='';tooltip.textContent='선택한 기간의 차트 데이터가 없습니다.';if(legend)legend.innerHTML='';return null;}
      const box=svg.getBoundingClientRect();
      const width=Math.max(280,box.width||960),height=Math.max(240,box.height||380);
      const left=14,right=width-90,top=20,bottom=height-(options.volume?100:36);
      svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
      const prices=visible.flatMap(row=>[row.low??row.close,row.high??row.close,row.close]);
      for(const ma of averages)prices.push(...ma.values.filter(finite));
      const low=Math.min(...prices),high=Math.max(...prices);
      const transform=options.scale==='log'?Math.log:value=>value;
      const rawMin=transform(low),rawMax=transform(high);
      const padding=(rawMax-rawMin)*.08||Math.max(Math.abs(rawMin)*.01,.01);
      const min=rawMin-padding,span=rawMax-rawMin+padding*2;
      const y=value=>bottom-(transform(value)-min)/span*(bottom-top);
      const inverseY=pixel=>{const value=min+(bottom-pixel)/(bottom-top)*span;return options.scale==='log'?Math.exp(value):value;};
      const step=(right-left)/visible.length,xScale=index=>left+(index+.5)*step;
      geometry={width,height,left,right,top,bottom,xScale,inverseY,step};
      const polyline=(values,color,period)=>{
        const points=values.map((value,index)=>finite(value)?[xScale(index),y(value)]:null).filter(Boolean);
        const tag=period?` data-ma="${period}"`:'';
        if(points.length===1)return `<circle${tag} cx="${points[0][0]}" cy="${points[0][1]}" r="3" fill="${color}"/>`;
        return points.length?`<polyline${tag} fill="none" stroke="${color}" stroke-width="1.4" stroke-linejoin="round" points="${points.map(p=>p.map(v=>v.toFixed(2)).join(',')).join(' ')}"/>`:'';
      };
      const last=visible.at(-1),lastY=y(last.close),lastColor=last.open===null?'#786699':last.close>=last.open?'#b94450':'#3269af';
      let html='';
      for(let i=0;i<=4;i++){
        const line=bottom-i*(bottom-top)/4;
        html+=`<line x1="${left}" x2="${right}" y1="${line}" y2="${line}" stroke="#202a39" stroke-width=".7"/>`;
        if(Math.abs(line-lastY)>18)html+=`<text x="${right+9}" y="${line+4}">${axisFmt(inverseY(line))}</text>`;
      }
      html+=`<line x1="${right}" x2="${right}" y1="${top}" y2="${bottom}" stroke="#263142" stroke-width=".7"/>`;
      if(options.style==='candle') {
        const candleWidth=Math.max(.8,Math.min(12,step*.68));
        html+=visible.map((row,index)=>{
          if(row.open===null)return `<circle cx="${xScale(index)}" cy="${y(row.close)}" r="2.5" fill="#aa92ee"/>`;
          const color=row.close>=row.open?'#ee6671':'#5298ee';
          return `<line x1="${xScale(index)}" x2="${xScale(index)}" y1="${y(row.high)}" y2="${y(row.low)}" stroke="${color}" stroke-width="1"/><rect data-candle x="${xScale(index)-candleWidth/2}" y="${Math.min(y(row.open),y(row.close))}" width="${candleWidth}" height="${Math.max(1,Math.abs(y(row.open)-y(row.close)))}" fill="${color}"/>`;
        }).join('');
      } else html+=polyline(visible.map(row=>row.close),'#c3acff');
      for(const ma of averages)html+=polyline(ma.values,ma.color,ma.period);
      html+=`<line x1="${left}" x2="${right}" y1="${lastY}" y2="${lastY}" stroke="${lastColor}" stroke-width=".7" stroke-dasharray="3 4"/><rect x="${right+1}" y="${lastY-10}" width="84" height="20" rx="3" fill="${lastColor}"/><text class="chart-badge" x="${right+7}" y="${lastY+4}">${axisFmt(last.close)}</text>`;
      if(options.volume){
        const maximum=Math.max(1,...visible.map(row=>row.volume||0)),barWidth=Math.max(1,Math.min(8,step*.68));
        html+=`<text x="${left}" y="${bottom+22}">거래량</text>`;
        html+=visible.map((row,index)=>row.volume===null?'':`<rect data-volume x="${xScale(index)-barWidth/2}" y="${height-30-row.volume/maximum*36}" width="${barWidth}" height="${row.volume/maximum*36}" fill="#34445e"/>`).join('');
      }
      const ticks=width<450?[0,visible.length-1]:[0,Math.floor((visible.length-1)/2),visible.length-1];
      for(const index of [...new Set(ticks)])html+=`<text x="${xScale(index)}" y="${height-10}" text-anchor="${visible.length===1?'middle':index===0?'start':index===visible.length-1?'end':'middle'}">${visible[index].date}</text>`;
      html+='<g data-chart-crosshair visibility="hidden" pointer-events="none"></g>';
      svg.innerHTML=html;crosshair=svg.querySelector?.('[data-chart-crosshair]');readout(visible.length-1);
      return {...metrics(visible),count:visible.length,rows:visible,first_close:visible[0].close,last_close:last.close,averages};
    }};
  }
  window.MilkywayMarketChart=Object.freeze({MOVING_AVERAGES,DEFAULTS,validBars,aggregate,average,metrics,prepare,create});
})();
