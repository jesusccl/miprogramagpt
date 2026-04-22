// ===================== SHARED STYLES =====================
const gBtnStyle = {
  padding: '10px 24px', borderRadius: 99, fontWeight: 800, fontSize: 14,
  background: 'var(--purple)', color: '#fff', letterSpacing: '0.03em',
  transition: 'opacity 0.15s, transform 0.1s',
};
const gOverlay = {
  position:'absolute', inset:0, display:'flex', flexDirection:'column',
  alignItems:'center', justifyContent:'center', gap:10,
  background:'rgba(7,7,26,0.88)', borderRadius:12, backdropFilter:'blur(4px)',
};

// ===================== SNAKE =====================
function SnakeGame() {
  const canvasRef = React.useRef(null);
  const stateRef = React.useRef(null);
  const [score, setScore] = React.useState(0);
  const [status, setStatus] = React.useState('idle'); // idle | playing | over

  React.useEffect(()=>{
    if(status==='over'&&score>0) window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'snake',score}}));
  },[status]);

  const CELL=22, COLS=20, ROWS=18;

  function initState() {
    return {
      snake:[{x:10,y:9},{x:9,y:9},{x:8,y:9}],
      dir:{x:1,y:0}, next:{x:1,y:0},
      food: randFood([{x:10,y:9}]),
      score:0, alive:true,
    };
  }
  function randFood(snake) {
    let p;
    do { p={x:Math.floor(Math.random()*20),y:Math.floor(Math.random()*18)}; }
    while(snake.some(s=>s.x===p.x&&s.y===p.y));
    return p;
  }

  const start = () => {
    stateRef.current = initState();
    setScore(0); setStatus('playing');
  };

  React.useEffect(() => {
    if (status !== 'playing') return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const s = stateRef.current;

    const draw = () => {
      ctx.fillStyle = '#080818'; ctx.fillRect(0,0,COLS*CELL,ROWS*CELL);
      for(let x=0;x<COLS;x++) for(let y=0;y<ROWS;y++){
        ctx.fillStyle='rgba(255,255,255,0.025)';
        ctx.fillRect(x*CELL+CELL/2-1,y*CELL+CELL/2-1,2,2);
      }
      // food glow
      ctx.shadowColor='#ff6b35'; ctx.shadowBlur=14;
      ctx.fillStyle='#ff6b35';
      ctx.beginPath();
      ctx.arc(s.food.x*CELL+CELL/2,s.food.y*CELL+CELL/2,CELL/2-3,0,Math.PI*2);
      ctx.fill(); ctx.shadowBlur=0;
      // snake
      s.snake.forEach((seg,i)=>{
        const t=i/Math.max(s.snake.length-1,1);
        const l=68-t*12, h=140+t*50;
        ctx.fillStyle=`oklch(${l}% 0.28 ${h}deg)`;
        ctx.shadowColor=i===0?`oklch(68% 0.28 140deg)`:'transparent';
        ctx.shadowBlur=i===0?10:0;
        ctx.beginPath();
        ctx.roundRect(seg.x*CELL+2,seg.y*CELL+2,CELL-4,CELL-4,i===0?6:4);
        ctx.fill();
      });
      ctx.shadowBlur=0;
    };

    const tick = () => {
      s.dir=s.next;
      const h={x:s.snake[0].x+s.dir.x,y:s.snake[0].y+s.dir.y};
      if(h.x<0||h.x>=COLS||h.y<0||h.y>=ROWS||s.snake.some(sg=>sg.x===h.x&&sg.y===h.y)){
        s.alive=false; setStatus('over'); return;
      }
      s.snake.unshift(h);
      if(h.x===s.food.x&&h.y===s.food.y){
        s.score+=10; setScore(s.score); s.food=randFood(s.snake);
      } else s.snake.pop();
      draw();
    };

    draw();
    const iv=setInterval(()=>{ if(!s.alive){clearInterval(iv);return;} tick(); },110);
    return ()=>clearInterval(iv);
  }, [status]);

  React.useEffect(()=>{
    const onKey=e=>{
      if(!stateRef.current) return;
      const d=stateRef.current.dir;
      const m={ArrowUp:{x:0,y:-1},ArrowDown:{x:0,y:1},ArrowLeft:{x:-1,y:0},ArrowRight:{x:1,y:0},
               w:{x:0,y:-1},s:{x:0,y:1},a:{x:-1,y:0},d:{x:1,y:0}};
      const nxt=m[e.key];
      if(nxt&&!(nxt.x===-d.x&&nxt.y===-d.y)){ e.preventDefault(); stateRef.current.next=nxt; }
    };
    window.addEventListener('keydown',onKey);
    return ()=>window.removeEventListener('keydown',onKey);
  },[]);

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Puntos: <strong style={{color:'var(--green)',fontSize:18}}>{score}</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative'}}>
        <canvas ref={canvasRef} width={COLS*CELL} height={ROWS*CELL} style={{borderRadius:12,display:'block',border:'1px solid var(--border)'}}/>
        {status==='idle'&&<div style={gOverlay}><div style={{fontSize:56}}>🐍</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Snake</div><div style={{color:'var(--muted)',fontSize:13}}>Usa ← → ↑ ↓ o WASD</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>💀</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Game Over</div><div style={{color:'var(--orange)',fontSize:32,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Reintentar</button></div>}
      </div>
      <div style={{color:'var(--muted)',fontSize:12}}>← → ↑ ↓ &nbsp;o&nbsp; WASD para mover</div>
    </div>
  );
}

// ===================== MEMORY MATCH =====================
const EMOJIS=['🍎','🍊','🍋','🍇','🍓','🫐','🍒','🍑'];
function MemoryGame() {
  const [cards,setCards]=React.useState([]);
  const [flipped,setFlipped]=React.useState([]);
  const [matched,setMatched]=React.useState([]);
  const [moves,setMoves]=React.useState(0);
  const [status,setStatus]=React.useState('idle');
  const [lock,setLock]=React.useState(false);

  React.useEffect(()=>{
    if(status==='won') window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'memory',score:Math.max(10,200-moves*5)}}));
  },[status]);

  const init=()=>{
    const deck=[...EMOJIS,...EMOJIS].map((e,i)=>({id:i,emoji:e,val:e}));
    for(let i=deck.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[deck[i],deck[j]]=[deck[j],deck[i]];}
    setCards(deck); setFlipped([]); setMatched([]); setMoves(0); setStatus('playing');
  };

  const flip=id=>{
    if(lock||flipped.includes(id)||matched.includes(id)) return;
    const nf=[...flipped,id];
    setFlipped(nf);
    if(nf.length===2){
      setMoves(m=>m+1);
      const [a,b]=nf.map(i=>cards.find(c=>c.id===i));
      if(a.val===b.val){
        const nm=[...matched,...nf];
        setMatched(nm);
        if(nm.length===cards.length) setStatus('won');
        setFlipped([]);
      } else {
        setLock(true);
        setTimeout(()=>{ setFlipped([]); setLock(false); },900);
      }
    }
  };

  const cardStyle=(id,emoji)=>{
    const isFlipped=flipped.includes(id)||matched.includes(id);
    const isMatched=matched.includes(id);
    return {
      width:72,height:72,borderRadius:12,fontSize:32,display:'flex',alignItems:'center',justifyContent:'center',
      cursor:isFlipped?'default':'pointer',userSelect:'none',
      transition:'all 0.25s',
      background:isMatched?'rgba(34,197,94,0.15)':isFlipped?'var(--surface3)':'var(--surface2)',
      border:`2px solid ${isMatched?'var(--green)':isFlipped?'var(--surface3)':'var(--border)'}`,
      transform:isFlipped?'scale(1)':'scale(0.95)',
      boxShadow:isMatched?'0 0 16px rgba(34,197,94,0.3)':'none',
    };
  };

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:16}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Movimientos: <strong style={{color:'var(--purple)',fontSize:18}}>{moves}</strong></span>
        <span style={{color:'var(--muted)',fontSize:14}}>Pares: <strong style={{color:'var(--cyan)',fontSize:18}}>{matched.length/2}/8</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={init}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative',display:'grid',gridTemplateColumns:'repeat(4,72px)',gap:10}}>
        {status==='idle'?<div style={{...gOverlay,position:'static',width:318,height:318,borderRadius:16,border:'1px solid var(--border)'}}>
          <div style={{fontSize:56}}>🃏</div>
          <div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Memory Match</div>
          <div style={{color:'var(--muted)',fontSize:13}}>Encuentra todos los pares</div>
          <button style={{...gBtnStyle,marginTop:8}} onClick={init}>¡Jugar!</button>
        </div>:cards.map(c=>(
          <div key={c.id} style={cardStyle(c.id,c.emoji)} onClick={()=>flip(c.id)}>
            {(flipped.includes(c.id)||matched.includes(c.id))?c.emoji:''}
          </div>
        ))}
        {status==='won'&&<div style={{...gOverlay,borderRadius:16}}>
          <div style={{fontSize:52}}>🎉</div>
          <div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡Ganaste!</div>
          <div style={{color:'var(--cyan)',fontSize:20,fontWeight:800}}>{moves} movimientos</div>
          <button style={{...gBtnStyle,marginTop:8}} onClick={init}>Jugar de nuevo</button>
        </div>}
      </div>
    </div>
  );
}

// ===================== TIC TAC TOE =====================
function TicTacToeGame() {
  const [board,setBoard]=React.useState(Array(9).fill(null));
  const [xTurn,setXTurn]=React.useState(true);
  const [status,setStatus]=React.useState('idle'); // idle | playing | won | draw
  const [winner,setWinner]=React.useState(null);
  const [winLine,setWinLine]=React.useState([]);

  React.useEffect(()=>{
    if(status==='won'&&winner==='X') window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'tictactoe',score:100}}));
  },[status]);

  const LINES=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
  const checkWinner=(b)=>{
    for(const [a,bb,c] of LINES) if(b[a]&&b[a]===b[bb]&&b[a]===b[c]) return {winner:b[a],line:[a,bb,c]};
    if(b.every(Boolean)) return {winner:'draw',line:[]};
    return null;
  };

  const minimax=(b,isMax)=>{
    const r=checkWinner(b);
    if(r) return r.winner==='O'?10:r.winner==='X'?-10:0;
    const moves=b.map((v,i)=>v?null:i).filter(i=>i!==null);
    if(isMax) return Math.max(...moves.map(i=>{const nb=[...b];nb[i]='O';return minimax(nb,false);}));
    return Math.min(...moves.map(i=>{const nb=[...b];nb[i]='X';return minimax(nb,true);}));
  };

  const aiMove=(b)=>{
    const moves=b.map((v,i)=>v?null:i).filter(i=>i!==null);
    let best=-Infinity,bestMove=moves[0];
    for(const m of moves){
      const nb=[...b];nb[m]='O';
      const score=minimax(nb,false);
      if(score>best){best=score;bestMove=m;}
    }
    return bestMove;
  };

  const play=(i)=>{
    if(board[i]||status!=='playing'||!xTurn) return;
    const nb=[...board]; nb[i]='X';
    const res=checkWinner(nb);
    if(res){setBoard(nb);setWinner(res.winner);setWinLine(res.line);setStatus(res.winner==='draw'?'draw':'won');return;}
    setBoard(nb); setXTurn(false);
    setTimeout(()=>{
      const ai=aiMove(nb);
      if(ai===undefined) return;
      const nb2=[...nb]; nb2[ai]='O';
      const res2=checkWinner(nb2);
      setBoard(nb2);
      if(res2){setWinner(res2.winner);setWinLine(res2.line);setStatus(res2.winner==='draw'?'draw':'won');}
      else setXTurn(true);
    },350);
  };

  const reset=()=>{ setBoard(Array(9).fill(null));setXTurn(true);setStatus('playing');setWinner(null);setWinLine([]); };

  const cellStyle=(i)=>({
    width:90,height:90,borderRadius:12,fontSize:36,fontWeight:900,fontFamily:'var(--font-display)',
    display:'flex',alignItems:'center',justifyContent:'center',cursor:board[i]||status!=='playing'?'default':'pointer',
    background:winLine.includes(i)?'rgba(168,85,247,0.15)':'var(--surface2)',
    border:`2px solid ${winLine.includes(i)?'var(--purple)':'var(--border)'}`,
    color:board[i]==='X'?'var(--cyan)':'var(--orange)',
    transition:'all 0.15s', userSelect:'none',
    boxShadow:winLine.includes(i)?'0 0 20px rgba(168,85,247,0.3)':'none',
  });

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:16}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Tú: <strong style={{color:'var(--cyan)'}}>X</strong> &nbsp;·&nbsp; IA: <strong style={{color:'var(--orange)'}}>O</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={reset}>{status==='idle'?'▶ Jugar':'↺ Nueva partida'}</button>
      </div>
      <div style={{position:'relative',display:'grid',gridTemplateColumns:'repeat(3,90px)',gap:8}}>
        {status==='idle'?<div style={{...gOverlay,position:'static',width:286,height:286,borderRadius:16,border:'1px solid var(--border)'}}>
          <div style={{fontSize:56}}>⭕</div>
          <div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Tres en Raya</div>
          <div style={{color:'var(--muted)',fontSize:13}}>Tú vs Inteligencia Artificial</div>
          <button style={{...gBtnStyle,marginTop:8}} onClick={reset}>¡Jugar!</button>
        </div>:board.map((_,i)=><div key={i} style={cellStyle(i)} onClick={()=>play(i)}>{board[i]}</div>)}
        {(status==='won'||status==='draw')&&<div style={{...gOverlay,borderRadius:16}}>
          <div style={{fontSize:52}}>{winner==='draw'?'🤝':winner==='X'?'🏆':'🤖'}</div>
          <div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>{winner==='draw'?'¡Empate!':winner==='X'?'¡Ganaste!':'La IA gana'}</div>
          <button style={{...gBtnStyle,marginTop:8}} onClick={reset}>Revancha</button>
        </div>}
      </div>
      {status==='playing'&&<div style={{color:'var(--muted)',fontSize:13}}>{xTurn?'Tu turno — haz clic':'La IA está pensando...'}</div>}
    </div>
  );
}

// ===================== BRICK BREAKER =====================
function BrickBreakerGame() {
  const canvasRef=React.useRef(null);
  const stRef=React.useRef(null);
  const rafRef=React.useRef(null);
  const [score,setScore]=React.useState(0);
  const [lives,setLives]=React.useState(3);
  const [status,setStatus]=React.useState('idle');

  React.useEffect(()=>{
    if((status==='over'||status==='won')&&score>0) window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'bricks',score}}));
  },[status]);

  const W=380,H=340,PW=70,PH=10,BR=5,BC=8,BW=36,BH=14,BPX=6,BPY=6,BYO=50;
  const BCOLORS=['#a855f7','#ec4899','#3b82f6','#22c55e','#f59e0b','#ef4444'];

  const initBricks=()=>{
    const b=[];
    for(let r=0;r<BR;r++) for(let c=0;c<BC;c++) b.push({x:c*(BW+BPX)+30,y:r*(BH+BPY)+BYO,alive:true,color:BCOLORS[r%BCOLORS.length]});
    return b;
  };

  const start=()=>{
    stRef.current={
      px:W/2-PW/2,ball:{x:W/2,y:H-60,vx:3,vy:-4},
      bricks:initBricks(),score:0,lives:3,running:true,paused:false,
    };
    setScore(0);setLives(3);setStatus('playing');
  };

  React.useEffect(()=>{
    if(status!=='playing') return;
    const canvas=canvasRef.current;
    const ctx=canvas.getContext('2d');
    const s=stRef.current;

    const draw=()=>{
      ctx.fillStyle='#080818'; ctx.fillRect(0,0,W,H);
      // bricks
      s.bricks.forEach(b=>{
        if(!b.alive) return;
        ctx.shadowColor=b.color; ctx.shadowBlur=8;
        ctx.fillStyle=b.color;
        ctx.beginPath(); ctx.roundRect(b.x,b.y,BW,BH,4); ctx.fill();
        ctx.fillStyle='rgba(255,255,255,0.2)';
        ctx.beginPath(); ctx.roundRect(b.x+2,b.y+2,BW-4,3,2); ctx.fill();
      });
      ctx.shadowBlur=0;
      // paddle
      const grad=ctx.createLinearGradient(s.px,0,s.px+PW,0);
      grad.addColorStop(0,'var(--purple)'); grad.addColorStop(1,'var(--cyan)');
      ctx.fillStyle=grad;
      ctx.beginPath(); ctx.roundRect(s.px,H-PH-8,PW,PH,PH/2); ctx.fill();
      // ball
      ctx.shadowColor='var(--cyan)'; ctx.shadowBlur=12;
      ctx.fillStyle='#fff';
      ctx.beginPath(); ctx.arc(s.ball.x,s.ball.y,BR,0,Math.PI*2); ctx.fill();
      ctx.shadowBlur=0;
    };

    const tick=()=>{
      const b=s.ball;
      b.x+=b.vx; b.y+=b.vy;
      if(b.x<=BR||b.x>=W-BR) b.vx*=-1;
      if(b.y<=BR) b.vy*=-1;
      // paddle
      if(b.y>=H-PH-8-BR&&b.y<=H-8&&b.x>=s.px&&b.x<=s.px+PW){
        b.vy=Math.abs(b.vy)*-1;
        b.vx=((b.x-s.px-PW/2)/(PW/2))*5;
      }
      // bricks
      s.bricks.forEach(br=>{
        if(!br.alive) return;
        if(b.x>br.x&&b.x<br.x+BW&&b.y>br.y&&b.y<br.y+BH){
          br.alive=false; b.vy*=-1; s.score+=10; setScore(s.score);
        }
      });
      // lost ball
      if(b.y>H+20){
        s.lives--; setLives(s.lives);
        if(s.lives<=0){ s.running=false; setStatus('over'); return; }
        s.ball={x:W/2,y:H-60,vx:3,vy:-4};
      }
      // win
      if(s.bricks.every(br=>!br.alive)){ s.running=false; setStatus('won'); return; }
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
      const rect=canvasRef.current?.getBoundingClientRect();
      if(!rect) return;
      stRef.current.px=Math.max(0,Math.min(W-PW,(e.clientX-rect.left)-PW/2));
    };
    window.addEventListener('mousemove',onMove);
    return ()=>window.removeEventListener('mousemove',onMove);
  },[]);

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Puntos: <strong style={{color:'var(--orange)',fontSize:18}}>{score}</strong></span>
        <span style={{color:'var(--muted)',fontSize:14}}>Vidas: <strong style={{color:'var(--pink)',fontSize:18}}>{'❤️'.repeat(lives)}</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative'}}>
        <canvas ref={canvasRef} width={W} height={H} style={{borderRadius:12,display:'block',border:'1px solid var(--border)'}}/>
        {status==='idle'&&<div style={gOverlay}><div style={{fontSize:56}}>🧱</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Brick Breaker</div><div style={{color:'var(--muted)',fontSize:13}}>Mueve el ratón para mover la paleta</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>💥</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Game Over</div><div style={{color:'var(--orange)',fontSize:28,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Reintentar</button></div>}
        {status==='won'&&<div style={gOverlay}><div style={{fontSize:52}}>🎆</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡Nivel completado!</div><div style={{color:'var(--cyan)',fontSize:28,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Jugar de nuevo</button></div>}
      </div>
      <div style={{color:'var(--muted)',fontSize:12}}>Mueve el ratón sobre el juego para controlar</div>
    </div>
  );
}

// ===================== 2048 =====================
function Game2048() {
  const empty=()=>Array(4).fill(null).map(()=>Array(4).fill(0));
  const addRandom=(g)=>{
    const cells=[];
    g.forEach((r,ri)=>r.forEach((v,ci)=>{ if(!v) cells.push([ri,ci]); }));
    if(!cells.length) return;
    const [r,c]=cells[Math.floor(Math.random()*cells.length)];
    g[r][c]=Math.random()<0.9?2:4;
  };

  const initGrid=()=>{ const g=empty(); addRandom(g); addRandom(g); return g; };
  const [grid,setGrid]=React.useState(empty());
  const [score,setScore]=React.useState(0);

  React.useEffect(()=>{
    if((status==='over'||status==='won')&&score>0) window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'game2048',score}}));
  },[status]);

  const [best,setBest]=React.useState(()=>parseInt(localStorage.getItem('ag2048best')||'0'));
  const [status,setStatus]=React.useState('idle');

  const start=()=>{ setGrid(initGrid()); setScore(0); setStatus('playing'); };

  const slide=(row)=>{
    let sc=0;
    const r=row.filter(v=>v);
    for(let i=0;i<r.length-1;i++) if(r[i]===r[i+1]){r[i]*=2;sc+=r[i];r.splice(i+1,1);}
    while(r.length<4) r.push(0);
    return {row:r,sc};
  };

  const move=(dir)=>{
    if(status!=='playing') return;
    let g=grid.map(r=>[...r]); let sc=0;
    if(dir==='left') g=g.map(r=>{const {row,sc:s}=slide(r);sc+=s;return row;});
    else if(dir==='right') g=g.map(r=>{const {row,sc:s}=slide([...r].reverse());sc+=s;return row.reverse();});
    else if(dir==='up'){
      for(let c=0;c<4;c++){const col=g.map(r=>r[c]);const {row,sc:s}=slide(col);sc+=s;row.forEach((v,r)=>g[r][c]=v);}
    }
    else{
      for(let c=0;c<4;c++){const col=g.map(r=>r[c]).reverse();const {row,sc:s}=slide(col);sc+=s;row.reverse().forEach((v,r)=>g[r][c]=v);}
    }
    const ns=score+sc;
    addRandom(g);
    setGrid(g); setScore(ns);
    if(ns>best){setBest(ns);localStorage.setItem('ag2048best',ns);}
    if(g.flat().includes(2048)) setStatus('won');
    else{
      const hasMoves=g.flat().some(v=>!v)||
        g.some((r,ri)=>r.some((v,ci)=>(ci<3&&v===r[ci+1])||(ri<3&&v===g[ri+1][ci])));
      if(!hasMoves) setStatus('over');
    }
  };

  React.useEffect(()=>{
    const k=e=>{
      const m={ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down'};
      if(m[e.key]){e.preventDefault();move(m[e.key]);}
    };
    window.addEventListener('keydown',k);
    return ()=>window.removeEventListener('keydown',k);
  },[grid,status,score]);

  const tileColor={0:'#1a1a35',2:'#eee4da',4:'#ede0c8',8:'#f2b179',16:'#f59563',32:'#f67c5f',64:'#f65e3b',128:'#edcf72',256:'#edcc61',512:'#edc850',1024:'#edc53f',2048:'#edc22e'};
  const tileText=v=>v>256?'#fff':v>4?'#776e65':'#776e65';
  const tileBg=v=>tileColor[v]||(v?'#3c3a32':'#1a1a35');

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:12,flexWrap:'wrap',justifyContent:'center'}}>
        <div style={{background:'var(--surface3)',borderRadius:10,padding:'6px 16px',textAlign:'center'}}>
          <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em'}}>PUNTOS</div>
          <div style={{color:'var(--text)',fontSize:18,fontWeight:800}}>{score}</div>
        </div>
        <div style={{background:'var(--surface3)',borderRadius:10,padding:'6px 16px',textAlign:'center'}}>
          <div style={{color:'var(--muted)',fontSize:11,fontWeight:700,letterSpacing:'0.08em'}}>MEJOR</div>
          <div style={{color:'var(--orange)',fontSize:18,fontWeight:800}}>{best}</div>
        </div>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Nuevo'}</button>
      </div>
      <div style={{position:'relative',background:'var(--surface2)',borderRadius:14,padding:10,border:'1px solid var(--border)'}}>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,80px)',gap:8}}>
          {grid.flat().map((v,i)=>(
            <div key={i} style={{
              width:80,height:80,borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center',
              background:tileBg(v),color:v?tileText(v):'transparent',
              fontSize:v>999?18:v>99?22:v>9?26:30,fontWeight:900,fontFamily:'var(--font-display)',
              transition:'background 0.1s',
              boxShadow:v>=2048?'0 0 20px rgba(237,194,46,0.5)':v>=128?'0 0 12px rgba(237,194,46,0.2)':'none',
            }}>{v||''}</div>
          ))}
        </div>
        {status==='idle'&&<div style={gOverlay}><div style={{fontFamily:'var(--font-display)',fontSize:52,fontWeight:900,color:'var(--orange)'}}>2048</div><div style={{color:'var(--muted)',fontSize:13}}>Combina fichas iguales</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='won'&&<div style={gOverlay}><div style={{fontSize:52}}>🏆</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡2048!</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Seguir jugando</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>😵</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Sin movimientos</div><div style={{color:'var(--orange)',fontSize:22,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Reintentar</button></div>}
      </div>
      <div style={{color:'var(--muted)',fontSize:12}}>← → ↑ ↓ para mover las fichas</div>
    </div>
  );
}

// ===================== WHACK A MOLE =====================
function WhackAMole() {
  const [holes,setHoles]=React.useState(Array(9).fill(false));
  const [score,setScore]=React.useState(0);
  const [timeLeft,setTimeLeft]=React.useState(30);
  const [status,setStatus]=React.useState('idle');

  React.useEffect(()=>{
    if(status==='over'&&score>0) window.dispatchEvent(new CustomEvent('ag_score',{detail:{game:'wham',score}}));
  },[status]);
  const timersRef=React.useRef([]);
  const intervalRef=React.useRef(null);

  const start=()=>{
    setScore(0);setTimeLeft(30);setHoles(Array(9).fill(false));setStatus('playing');
  };

  React.useEffect(()=>{
    if(status!=='playing') return;
    intervalRef.current=setInterval(()=>{
      setTimeLeft(t=>{ if(t<=1){setStatus('over');return 0;} return t-1; });
    },1000);
    return ()=>clearInterval(intervalRef.current);
  },[status]);

  React.useEffect(()=>{
    if(status!=='playing') return;
    const pop=()=>{
      const i=Math.floor(Math.random()*9);
      setHoles(h=>{const n=[...h];n[i]=true;return n;});
      const t=setTimeout(()=>{
        setHoles(h=>{const n=[...h];n[i]=false;return n;});
      },700+Math.random()*400);
      timersRef.current.push(t);
    };
    const iv=setInterval(pop,600);
    return ()=>{ clearInterval(iv); timersRef.current.forEach(clearTimeout); };
  },[status]);

  const whack=(i)=>{
    if(!holes[i]||status!=='playing') return;
    setHoles(h=>{const n=[...h];n[i]=false;return n;});
    setScore(s=>s+10);
  };

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:14}}>
      <div style={{display:'flex',alignItems:'center',gap:20}}>
        <span style={{color:'var(--muted)',fontSize:14}}>Puntos: <strong style={{color:'var(--green)',fontSize:18}}>{score}</strong></span>
        <span style={{color:'var(--muted)',fontSize:14}}>Tiempo: <strong style={{color:timeLeft<=10?'var(--pink)':'var(--cyan)',fontSize:18}}>{timeLeft}s</strong></span>
        <button style={gBtnStyle} onMouseOver={e=>e.target.style.opacity='0.8'} onMouseOut={e=>e.target.style.opacity='1'} onClick={start}>{status==='idle'?'▶ Jugar':'↺ Reiniciar'}</button>
      </div>
      <div style={{position:'relative',background:'var(--surface2)',borderRadius:16,padding:16,border:'1px solid var(--border)'}}>
        <div style={{display:'grid',gridTemplateColumns:'repeat(3,100px)',gap:12}}>
          {holes.map((up,i)=>(
            <div key={i} onClick={()=>whack(i)} style={{
              width:100,height:100,borderRadius:50,
              background:up?'var(--surface3)':'#0d0d22',
              border:`3px solid ${up?'var(--green)':'var(--border)'}`,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontSize:48,cursor:up?'pointer':'default',
              transition:'all 0.12s',
              transform:up?'scale(1.08)':'scale(1)',
              boxShadow:up?'0 0 20px rgba(34,197,94,0.35)':'none',
            }}>{up?'🐭':''}</div>
          ))}
        </div>
        {status==='idle'&&<div style={gOverlay}><div style={{fontSize:56}}>🐭</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>Whack-a-Mole</div><div style={{color:'var(--muted)',fontSize:13}}>Golpea los ratones en 30 segundos</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>¡Jugar!</button></div>}
        {status==='over'&&<div style={gOverlay}><div style={{fontSize:52}}>⏱️</div><div style={{fontFamily:'var(--font-display)',fontSize:22,fontWeight:900}}>¡Tiempo!</div><div style={{color:'var(--green)',fontSize:28,fontWeight:900}}>{score} pts</div><button style={{...gBtnStyle,marginTop:8}} onClick={start}>Jugar de nuevo</button></div>}
      </div>
    </div>
  );
}

Object.assign(window, { SnakeGame, MemoryGame, TicTacToeGame, BrickBreakerGame, Game2048, WhackAMole });
