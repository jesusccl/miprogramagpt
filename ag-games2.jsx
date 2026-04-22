// ===================== TOUCH D-PAD =====================
function TouchDPad({ onDir, style }) {
  const btn = (label, dir, icon) => (
    <button
      onTouchStart={e=>{e.preventDefault();onDir(dir);}}
      onMouseDown={()=>onDir(dir)}
      style={{
        width:52,height:52,borderRadius:12,background:'rgba(255,255,255,0.08)',
        border:'1px solid rgba(255,255,255,0.15)',color:'var(--text)',fontSize:20,
        display:'flex',alignItems:'center',justifyContent:'center',userSelect:'none',
        WebkitTapHighlightColor:'transparent',touchAction:'manipulation',
      }}
    >{icon}</button>
  );
  return (
    <div style={{display:'grid',gridTemplateColumns:'52px 52px 52px',gridTemplateRows:'52px 52px 52px',gap:4,...style}}>
      <div/>{btn('up','up','↑')}<div/>
      {btn('left','left','←')}{btn('down','down','↓')}{btn('right','right','→')}
      <div/><div/><div/>
    </div>
  );
}

// ===================== TETRIS =====================
const T_PIECES = [
  {shape:[[1,1,1,1]],color:'#06b6d4'},
  {shape:[[1,1],[1,1]],color:'#facc15'},
  {shape:[[0,1,0],[1,1,1]],color:'#a855f7'},
  {shape:[[0,1,1],[1,1,0]],color:'#22c55e'},
  {shape:[[1,1,0],[0,1,1]],color:'#ef4444'},
  {shape:[[1,0,0],[1,1,1]],color:'#3b82f6'},
  {shape:[[0,0,1],[1,1,1]],color:'#f97316'},
];
const T_W=10,T_H=20,T_CELL=24;

function TetrisGame() {
  const canvasRef=React.useRef(null);
  const stRef=React.useRef(null);
  const ivRef=React.useRef(null);
  const [score,setScore]=React.useState(0);
  const [lines,setLines]=React.useState(0);
  const [level,setLevel]=React.useState(1);
  const [status,setStatus]=React.useState('idle');
  const isMobile=window.innerWidth<600;

  const empty=()=>Array(T_H).fill(null).map(()=>Array(T_W).fill(0));
  const randPiece=()=>{const p=T_PIECES[Math.floor(Math.random()*T_PIECES.length)];return {shape:p.shape.map(r=>[...r]),color:p.color,x:3,y:0};};
  const rotate=sh=>{const r=sh[0].length,c=sh.length;return Array(r).fill(0).map((_,i)=>Array(c).fill(0).map((_,j)=>sh[c-1-j][i]));};
  const fits=(board,piece,dx=0,dy=0,sh=null)=>{const s=sh||piece.shape;return s.every((row,r)=>row.every((v,c)=>{if(!v)return true;const nx=piece.x+c+dx,ny=piece.y+r+dy;return nx>=0&&nx<T_W&&ny<T_H&&(ny<0||!board[ny][nx]);}));};
  const place=(board,piece)=>{const b=board.map(r=>[...r]);piece.shape.forEach((row,r)=>row.forEach((v,c)=>{if(v&&piece.y+r>=0)b[piece.y+r][piece.x+c]=piece.color;}));return b;};
  const clearLines=(board)=>{const kept=board.filter(r=>r.some(v=>!v));const cleared=T_H-kept.length;const newRows=Array(cleared).fill(null).map(()=>Array(T_W).fill(0));return{board:[...newRows,...kept],cleared};};

  const start=()=>{
    const s={board:empty(),cur:randPiece(),next:randPiece(),score:0,lines:0,level:1,running:true};
    stRef.current=s;setScore(0);setLines(0);setLevel(1);setStatus('playing');
  };

  const drawGame=React.useCallback(()=>{
    const canvas=canvasRef.current; if(!canvas) return;
    const ctx=canvas.getContext('2d');
    const s=stRef.current; if(!s) return;
    ctx.fillStyle='#080818';ctx.fillRect(0,0,T_W*T_CELL,T_H*T_CELL);
    // grid
    ctx.strokeStyle='rgba(255,255,255,0.03)';ctx.lineWidth=1;
    for(let x=0;x<=T_W;x++){ctx.beginPath();ctx.moveTo(x*T_CELL,0);ctx.lineTo(x*T_CELL,T_H*T_CELL);ctx.stroke();}
    for(let y=0;y<=T_H;y++){ctx.beginPath();ctx.moveTo(0,y*T_CELL);ctx.lineTo(T_W*T_CELL,y*T_CELL);ctx.stroke();}
    // board
    s.board.forEach((row,r)=>row.forEach((v,c)=>{
      if(!v) return;
      ctx.fillStyle=v;ctx.shadowColor=v;ctx.shadowBlur=6;
      ctx.beginPath();ctx.roundRect(c*T_CELL+1,r*T_CELL+1,T_CELL-2,T_CELL-2,3);ctx.fill();
      ctx.fillStyle='rgba(255,255,255,0.25)';ctx.shadowBlur=0;
      ctx.fillRect(c*T_CELL+2,r*T_CELL+2,T_CELL-4,3);
    }));
    // ghost
    let gy=0; while(fits(s.board,s.cur,0,gy+1)) gy++;
    s.cur.shape.forEach((row,r)=>row.forEach((v,c)=>{
      if(!v) return;
      ctx.fillStyle='rgba(255,255,255,0.08)';ctx.shadowBlur=0;
      ctx.beginPath();ctx.roundRect((s.cur.x+c)*T_CELL+1,(s.cur.y+r+gy)*T_CELL+1,T_CELL-2,T_CELL-2,3);ctx.fill();
    }));
    // current piece
    s.cur.shape.forEach((row,r)=>row.forEach((v,c)=>{
      if(!v) return;
      ctx.fillStyle=s.cur.color;ctx.shadowColor=s.cur.color;ctx.shadowBlur=8;
      ctx.beginPath();ctx.roundRect((s.cur.x+c)*T_CELL+1,(s.cur.y+r)*T_CELL+1,T_CELL-2,T_CELL-2,3);ctx.fill();
      ctx.fillStyle='rgba(255,255,255,0.3)';ctx.shadowBlur=0;
      ctx.fillRect((s.cur.x+c)*T_CELL+2,(s.cur.y+r)*T_CELL+2,T_CELL-4,3);
    }));
    ctx.shadowBlur=0;
  },[]);

  const moveDown=React.useCallback(()=>{
    const s=stRef.current; if(!s||!s.running) return;
    if(fits(s.board,s.cur,0,1)){s.cur.y++;drawGame();}
    else {
      const nb=place(s.board,s.cur);
      const {board:cb,cleared}=clearLines(nb);
      const pts=[0,100,300,500,800][cleared]||0;
      s.score+=pts*(s.level);s.lines+=cleared;s.level=Math.floor(s.lines/10)+1;
      s.board=cb;s.cur=s.next;s.next=randPiece();
      setScore(s.score);setLines(s.lines);setLevel(s.level);
      if(!fits(s.board,s.cur)){
        s.running=false;setStatus('over');
        window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'tetris',score:s.score}}));
        return;
      }
      drawGame();
    }
  },[drawGame]);

  React.useEffect(()=>{
    if(status!=='playing') return;
    drawGame();
    const speed=Math.max(80,500-((stRef.current?.level||1)-1)*40);
    ivRef.current=setInterval(moveDown,speed);
    return ()=>clearInterval(ivRef.current);
  },[status,moveDown,level]);

  React.useEffect(()=>{
    if(status==='playing'&&ivRef.current){
      clearInterval(ivRef.current);
      const speed=Math.max(80,500-(level-1)*40);
      ivRef.current=setInterval(moveDown,speed);
    }
  },[level]);

  const doAction=React.useCallback((action)=>{
    const s=stRef.current; if(!s||!s.running) return;
    if(action==='left'&&fits(s.board,s.cur,-1,0)){s.cur.x--;drawGame();}
    else if(action==='right'&&fits(s.board,s.cur,1,0)){s.cur.x++;drawGame();}
    else if(action==='down') moveDown();
    else if(action==='rotate'){const r=rotate(s.cur.shape);if(fits(s.board,s.cur,0,0,r)){s.cur.shape=r;drawGame();}}
    else if(action==='drop'){while(fits(s.board,s.cur,0,1))s.cur.y++;moveDown();}
  },[drawGame,moveDown]);

  React.useEffect(()=>{
    const k=e=>{
      const m={ArrowLeft:'left',ArrowRight:'right',ArrowDown:'down',ArrowUp:'rotate',' ':'drop'};
      if(m[e.key]){e.preventDefault();doAction(m[e.key]);}
    };
    window.addEventListener('keydown',k);
    return ()=>window.removeEventListener('keydown',k);
  },[doAction]);

  const next=stRef.current?.next;

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',gap:12,alignItems:'flex-start'}}>
        <div style={{position:'relative'}}>
          <canvas ref={canvasRef} width={T_W*T_CELL} height={T_H*T_CELL} style={{borderRadius:12,display:'block',border:'1px solid var(--border)'}}/>
          {status==='idle'&&<div style={gOverlay}><div style={{fontSize:52}}>🟦</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Tetris</div><div style={{color:'var(--muted)',fontSize:13}}>← → ↓ mover · ↑ rotar · Espacio = caída</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
          {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>💥</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Game Over</div><div style={{color:'var(--cyan)',fontSize:26,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Reintentar</button></div>}
        </div>
        <div style={{display:'flex',flexDirection:'column',gap:12,minWidth:90}}>
          <div style={{background:'var(--surface2)',border:'1px solid var(--border)',borderRadius:12,padding:'10px 14px'}}>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em',marginBottom:4}}>PUNTOS</div>
            <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:20,color:'var(--cyan)'}}>{score}</div>
          </div>
          <div style={{background:'var(--surface2)',border:'1px solid var(--border)',borderRadius:12,padding:'10px 14px'}}>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em',marginBottom:4}}>LÍNEAS</div>
            <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:20,color:'var(--green)'}}>{lines}</div>
          </div>
          <div style={{background:'var(--surface2)',border:'1px solid var(--border)',borderRadius:12,padding:'10px 14px'}}>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em',marginBottom:4}}>NIVEL</div>
            <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:20,color:'var(--orange)'}}>{level}</div>
          </div>
          {next&&<div style={{background:'var(--surface2)',border:'1px solid var(--border)',borderRadius:12,padding:'10px 14px'}}>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em',marginBottom:6}}>SIGUIENTE</div>
            <div style={{display:'grid',gridTemplateColumns:`repeat(${next.shape[0].length},14px)`,gap:2}}>
              {next.shape.flat().map((v,i)=><div key={i} style={{width:14,height:14,borderRadius:3,background:v?next.color:'transparent'}}/>)}
            </div>
          </div>}
          <button style={gBtnStyle} onClick={start}>↺</button>
        </div>
      </div>
      {isMobile&&status==='playing'&&(
        <div style={{display:'flex',gap:12,alignItems:'center',marginTop:4}}>
          <TouchDPad onDir={doAction}/>
          <button onTouchStart={e=>{e.preventDefault();doAction('drop');}} onMouseDown={()=>doAction('drop')}
            style={{...gBtnStyle,padding:'14px 20px',fontSize:18}}>⬇⬇</button>
          <button onTouchStart={e=>{e.preventDefault();doAction('rotate');}} onMouseDown={()=>doAction('rotate')}
            style={{...gBtnStyle,padding:'14px 20px',fontSize:18,background:'var(--cyan)'}}>↻</button>
        </div>
      )}
    </div>
  );
}

// ===================== PONG =====================
function PongGame() {
  const canvasRef=React.useRef(null);
  const stRef=React.useRef(null);
  const rafRef=React.useRef(null);
  const [playerScore,setPlayerScore]=React.useState(0);
  const [aiScore,setAiScore]=React.useState(0);
  const [status,setStatus]=React.useState('idle');
  const W=400,H=280,PW=10,PH=60,BR=6;

  const start=()=>{
    stRef.current={
      py:H/2-PH/2,ay:H/2-PH/2,
      ball:{x:W/2,y:H/2,vx:4*(Math.random()>0.5?1:-1),vy:3*(Math.random()>0.5?1:-1)},
      ps:0,as:0,running:true,
    };
    setPlayerScore(0);setAiScore(0);setStatus('playing');
  };

  React.useEffect(()=>{
    if(status!=='playing') return;
    const canvas=canvasRef.current;
    const ctx=canvas.getContext('2d');
    const s=stRef.current;

    const draw=()=>{
      ctx.fillStyle='#080818';ctx.fillRect(0,0,W,H);
      ctx.setLineDash([8,8]);ctx.strokeStyle='rgba(255,255,255,0.08)';ctx.lineWidth=2;
      ctx.beginPath();ctx.moveTo(W/2,0);ctx.lineTo(W/2,H);ctx.stroke();ctx.setLineDash([]);
      // paddles
      const grad1=ctx.createLinearGradient(0,s.py,0,s.py+PH);
      grad1.addColorStop(0,'var(--cyan)');grad1.addColorStop(1,'var(--purple)');
      ctx.fillStyle=grad1;ctx.shadowColor='var(--cyan)';ctx.shadowBlur=12;
      ctx.beginPath();ctx.roundRect(12,s.py,PW,PH,PW/2);ctx.fill();
      const grad2=ctx.createLinearGradient(0,s.ay,0,s.ay+PH);
      grad2.addColorStop(0,'var(--orange)');grad2.addColorStop(1,'var(--pink)');
      ctx.fillStyle=grad2;ctx.shadowColor='var(--orange)';ctx.shadowBlur=12;
      ctx.beginPath();ctx.roundRect(W-PW-12,s.ay,PW,PH,PW/2);ctx.fill();
      // ball
      ctx.fillStyle='#fff';ctx.shadowColor='#fff';ctx.shadowBlur=16;
      ctx.beginPath();ctx.arc(s.ball.x,s.ball.y,BR,0,Math.PI*2);ctx.fill();
      ctx.shadowBlur=0;
      // scores
      ctx.font=`bold 28px 'Exo 2', sans-serif`;ctx.fillStyle='rgba(255,255,255,0.4)';ctx.textAlign='center';
      ctx.fillText(s.ps,W/2-60,36);ctx.fillText(s.as,W/2+60,36);
    };

    const tick=()=>{
      const b=s.ball;
      b.x+=b.vx;b.y+=b.vy;
      if(b.y<=BR||b.y>=H-BR) b.vy*=-1;
      // player paddle
      if(b.x<=12+PW+BR&&b.y>=s.py&&b.y<=s.py+PH&&b.vx<0){
        b.vx=Math.abs(b.vx)*1.05;b.vy+=((b.y-(s.py+PH/2))/(PH/2))*2;
      }
      // ai paddle
      if(b.x>=W-PW-12-BR&&b.y>=s.ay&&b.y<=s.ay+PH&&b.vx>0){
        b.vx=-Math.abs(b.vx)*1.05;b.vy+=((b.y-(s.ay+PH/2))/(PH/2))*2;
      }
      // cap speed
      const spd=Math.sqrt(b.vx**2+b.vy**2);if(spd>12){b.vx=b.vx/spd*12;b.vy=b.vy/spd*12;}
      // AI movement
      const aiCenter=s.ay+PH/2;const aiSpeed=3.2;
      if(aiCenter<b.y-4) s.ay=Math.min(H-PH,s.ay+aiSpeed);
      else if(aiCenter>b.y+4) s.ay=Math.max(0,s.ay-aiSpeed);
      // scoring
      if(b.x<0){s.as++;setAiScore(s.as);if(s.as>=5){s.running=false;setStatus('over');window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'pong',score:s.ps*100}}));return;}b.x=W/2;b.y=H/2;b.vx=4;b.vy=3*(Math.random()>0.5?1:-1);}
      if(b.x>W){s.ps++;setPlayerScore(s.ps);if(s.ps>=5){s.running=false;setStatus('won');window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'pong',score:500}}));return;}b.x=W/2;b.y=H/2;b.vx=-4;b.vy=3*(Math.random()>0.5?1:-1);}
      draw();
      rafRef.current=requestAnimationFrame(tick);
    };

    draw();
    rafRef.current=requestAnimationFrame(tick);
    return ()=>cancelAnimationFrame(rafRef.current);
  },[status]);

  React.useEffect(()=>{
    const onMove=e=>{
      if(!stRef.current) return;
      const rect=canvasRef.current?.getBoundingClientRect();if(!rect) return;
      stRef.current.py=Math.max(0,Math.min(H-PH,(e.clientY-rect.top)-PH/2));
    };
    const onTouch=e=>{
      if(!stRef.current) return;
      const rect=canvasRef.current?.getBoundingClientRect();if(!rect) return;
      const t=e.touches[0];
      stRef.current.py=Math.max(0,Math.min(H-PH,(t.clientY-rect.top)-PH/2));
    };
    window.addEventListener('mousemove',onMove);
    window.addEventListener('touchmove',onTouch,{passive:true});
    return ()=>{window.removeEventListener('mousemove',onMove);window.removeEventListener('touchmove',onTouch);};
  },[]);

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--cyan)',fontWeight:800,fontSize:16}}>TÚ: {playerScore}</span>
        <span style={{color:'var(--muted)'}}>vs</span>
        <span style={{color:'var(--orange)',fontWeight:800,fontSize:16}}>IA: {aiScore}</span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative'}}>
        <canvas ref={canvasRef} width={W} height={H} style={{borderRadius:12,display:'block',border:'1px solid var(--border)',cursor:'none'}}/>
        {status==='idle'&&<div style={gOverlay}><div style={{fontSize:52}}>🏓</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Pong</div><div style={{color:'var(--muted)',fontSize:13}}>Mueve el ratón para controlar la paleta izquierda</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>🤖</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>La IA gana</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Revancha</button></div>}
        {status==='won'&&<div style={gOverlay}><div style={{fontSize:52}}>🏆</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡Ganaste!</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Jugar de nuevo</button></div>}
      </div>
      <div style={{color:'var(--muted)',fontSize:12}}>Mueve el ratón (o toca la pantalla) para controlar tu paleta · Primero en llegar a 5 gana</div>
    </div>
  );
}

// ===================== SPACE INVADERS =====================
function SpaceInvaders() {
  const canvasRef=React.useRef(null);
  const stRef=React.useRef(null);
  const rafRef=React.useRef(null);
  const [score,setScore]=React.useState(0);
  const [lives,setLives]=React.useState(3);
  const [status,setStatus]=React.useState('idle');
  const W=400,H=340;

  const mkInvaders=()=>{
    const inv=[];
    for(let r=0;r<4;r++) for(let c=0;c<9;c++){
      inv.push({x:40+c*38,y:40+r*36,alive:true,row:r,pts:[30,20,20,10][r]});
    }
    return inv;
  };

  const start=()=>{
    stRef.current={
      px:W/2,bullets:[],eBullets:[],
      inv:mkInvaders(),invDir:1,invSpeed:0.4,invTimer:0,
      score:0,lives:3,running:true,
      shootCooldown:0,eShootTimer:60,
    };
    setScore(0);setLives(3);setStatus('playing');
  };

  const INVADER_EMOJIS=['👾','👾','🤖','🤖'];

  React.useEffect(()=>{
    if(status!=='playing') return;
    const canvas=canvasRef.current;
    const ctx=canvas.getContext('2d');
    const s=stRef.current;

    const draw=()=>{
      ctx.fillStyle='#080818';ctx.fillRect(0,0,W,H);
      // stars
      ctx.fillStyle='rgba(255,255,255,0.4)';
      [[20,30],[80,60],[150,20],[220,80],[300,40],[370,70],[50,120],[280,110],[340,130]].forEach(([x,y])=>{
        ctx.beginPath();ctx.arc(x,y,1,0,Math.PI*2);ctx.fill();
      });
      // invaders
      s.inv.forEach(inv=>{
        if(!inv.alive) return;
        ctx.font='20px serif';ctx.textAlign='center';
        ctx.fillText(INVADER_EMOJIS[inv.row],inv.x,inv.y+16);
      });
      // player
      ctx.shadowColor='var(--cyan)';ctx.shadowBlur=10;
      ctx.fillStyle='var(--cyan)';
      ctx.beginPath();ctx.moveTo(s.px,H-30);ctx.lineTo(s.px-16,H-14);ctx.lineTo(s.px+16,H-14);ctx.closePath();ctx.fill();
      ctx.fillRect(s.px-4,H-38,8,10);
      ctx.shadowBlur=0;
      // bullets
      s.bullets.forEach(b=>{
        ctx.fillStyle='var(--cyan)';ctx.shadowColor='var(--cyan)';ctx.shadowBlur=8;
        ctx.beginPath();ctx.roundRect(b.x-2,b.y-8,4,12,2);ctx.fill();
      });
      // enemy bullets
      s.eBullets.forEach(b=>{
        ctx.fillStyle='var(--orange)';ctx.shadowColor='var(--orange)';ctx.shadowBlur=8;
        ctx.beginPath();ctx.roundRect(b.x-2,b.y,4,10,2);ctx.fill();
      });
      ctx.shadowBlur=0;
      // HUD
      ctx.font="bold 13px 'Nunito', sans-serif";ctx.fillStyle='rgba(255,255,255,0.5)';ctx.textAlign='left';
      ctx.fillText(`❤️ ${s.lives}`,10,H-6);
      ctx.textAlign='right';ctx.fillText(`${s.score} pts`,W-10,H-6);
    };

    const tick=()=>{
      if(!s.running) return;
      s.shootCooldown=Math.max(0,s.shootCooldown-1);
      // move bullets
      s.bullets=s.bullets.filter(b=>b.y>-10);
      s.bullets.forEach(b=>b.y-=7);
      s.eBullets=s.eBullets.filter(b=>b.y<H+10);
      s.eBullets.forEach(b=>b.y+=4);
      // move invaders
      s.invTimer++;
      const alive=s.inv.filter(i=>i.alive);
      const speed=Math.max(8,40-Math.floor((36-alive.length)/4)*3);
      if(s.invTimer>=speed){
        s.invTimer=0;
        const minX=Math.min(...alive.map(i=>i.x));
        const maxX=Math.max(...alive.map(i=>i.x));
        if((s.invDir>0&&maxX>W-30)||(s.invDir<0&&minX<30)){
          s.inv.forEach(i=>i.y+=18);s.invDir*=-1;
        } else s.inv.forEach(i=>i.x+=s.invDir*18);
      }
      // check if invaders reached player
      if(alive.some(i=>i.y>H-60)){s.running=false;setStatus('over');window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'space',score:s.score}}));return;}
      // bullet-invader collision
      s.bullets.forEach(b=>{
        s.inv.forEach(inv=>{
          if(inv.alive&&Math.abs(b.x-inv.x)<16&&Math.abs(b.y-inv.y)<16){
            inv.alive=false;b.y=-100;s.score+=inv.pts;setScore(s.score);
          }
        });
      });
      // enemy bullet-player collision
      s.eBullets.forEach(b=>{
        if(Math.abs(b.x-s.px)<14&&b.y>H-44){
          b.y=H+100;s.lives--;setLives(s.lives);
          if(s.lives<=0){s.running=false;setStatus('over');window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'space',score:s.score}}));return;}
        }
      });
      // enemy shooting
      s.eShootTimer--;
      if(s.eShootTimer<=0){
        s.eShootTimer=30+Math.random()*50;
        if(alive.length){const shooter=alive[Math.floor(Math.random()*alive.length)];s.eBullets.push({x:shooter.x,y:shooter.y+16});}
      }
      // win
      if(!alive.length){s.running=false;setStatus('won');window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'space',score:s.score+s.lives*100}}));return;}
      draw();
      rafRef.current=requestAnimationFrame(tick);
    };

    draw();
    rafRef.current=requestAnimationFrame(tick);
    return ()=>cancelAnimationFrame(rafRef.current);
  },[status]);

  React.useEffect(()=>{
    const keys={};
    const kd=e=>{ keys[e.key]=true; if(e.key===' '){e.preventDefault();shoot();} };
    const ku=e=>{ keys[e.key]=false; };
    const move=()=>{
      if(!stRef.current?.running) return;
      if(keys['ArrowLeft']||keys['a']) stRef.current.px=Math.max(18,stRef.current.px-5);
      if(keys['ArrowRight']||keys['d']) stRef.current.px=Math.min(W-18,stRef.current.px+5);
    };
    const iv=setInterval(move,16);
    window.addEventListener('keydown',kd);window.addEventListener('keyup',ku);
    return ()=>{window.removeEventListener('keydown',kd);window.removeEventListener('keyup',ku);clearInterval(iv);};
  },[status]);

  const shoot=()=>{
    const s=stRef.current;if(!s?.running||s.shootCooldown>0) return;
    s.bullets.push({x:s.px,y:W-40});s.shootCooldown=12;
  };
  const moveLeft=()=>{ if(stRef.current?.running) stRef.current.px=Math.max(18,stRef.current.px-16); };
  const moveRight=()=>{ if(stRef.current?.running) stRef.current.px=Math.min(W-18,stRef.current.px+16); };

  const isMobile=window.innerWidth<600;

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Puntos: <strong style={{color:'var(--green)',fontSize:18}}>{score}</strong></span>
        <span style={{color:'var(--muted)',fontSize:14}}>Vidas: <strong style={{color:'var(--pink)',fontSize:16}}>{'❤️'.repeat(Math.max(0,lives))}</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative'}}>
        <canvas ref={canvasRef} width={W} height={H} style={{borderRadius:12,display:'block',border:'1px solid var(--border)'}}/>
        {status==='idle'&&<div style={gOverlay}><div style={{fontSize:52}}>👾</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Space Invaders</div><div style={{color:'var(--muted)',fontSize:13}}>← → mover · Espacio = disparar</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>🚀💥</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Game Over</div><div style={{color:'var(--orange)',fontSize:26,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Reintentar</button></div>}
        {status==='won'&&<div style={gOverlay}><div style={{fontSize:52}}>🌟</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡Galaxia salvada!</div><div style={{color:'var(--cyan)',fontSize:26,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Siguiente oleada</button></div>}
      </div>
      {(isMobile||true)&&status==='playing'&&(
        <div style={{display:'flex',gap:16,marginTop:4}}>
          <button onTouchStart={e=>{e.preventDefault();moveLeft();}} onMouseDown={moveLeft}
            style={{...gBtnStyle,padding:'14px 28px',fontSize:22}}>◀</button>
          <button onTouchStart={e=>{e.preventDefault();shoot();}} onMouseDown={shoot}
            style={{...gBtnStyle,padding:'14px 28px',fontSize:22,background:'var(--cyan)',color:'#000'}}>🔫</button>
          <button onTouchStart={e=>{e.preventDefault();moveRight();}} onMouseDown={moveRight}
            style={{...gBtnStyle,padding:'14px 28px',fontSize:22}}>▶</button>
        </div>
      )}
      <div style={{color:'var(--muted)',fontSize:12}}>← → mover · Espacio para disparar</div>
    </div>
  );
}

Object.assign(window, { TetrisGame, PongGame, SpaceInvaders, TouchDPad });
