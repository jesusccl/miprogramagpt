// ===================== GAME DATA =====================
const GAMES_DATA = [
  { id:'snake',      title:'Snake',          cat:'arcade',    catLabel:'Arcade',     emoji:'🐍', bg:'#0f2d1a', accent:'#22c55e', plays:'2.1M', rating:4.8, desc:'Come manzanas y crece sin chocarte con las paredes' },
  { id:'memory',     title:'Memory Match',   cat:'puzzle',    catLabel:'Puzzle',     emoji:'🃏', bg:'#1e1030', accent:'#a855f7', plays:'1.3M', rating:4.6, desc:'Encuentra todos los pares de cartas antes de quedarte sin intentos' },
  { id:'tictactoe',  title:'Tres en Raya',   cat:'strategy',  catLabel:'Estrategia', emoji:'⭕', bg:'#0d1f3c', accent:'#3b82f6', plays:'980K', rating:4.5, desc:'El clásico juego de X y O contra la inteligencia artificial' },
  { id:'bricks',     title:'Brick Breaker',  cat:'arcade',    catLabel:'Arcade',     emoji:'🧱', bg:'#2d1a00', accent:'#f59e0b', plays:'1.8M', rating:4.7, desc:'Destruye todos los ladrillos con la pelota y la paleta' },
  { id:'game2048',   title:'2048',           cat:'puzzle',    catLabel:'Puzzle',     emoji:'🔢', bg:'#2d1220', accent:'#ec4899', plays:'5.2M', rating:4.9, desc:'Combina las fichas para llegar a la legendaria ficha 2048' },
  { id:'wham',       title:'Whack-a-Mole',   cat:'action',    catLabel:'Acción',     emoji:'🐭', bg:'#1a2d0f', accent:'#84cc16', plays:'3.4M', rating:4.7, desc:'¡Golpea todos los ratones que puedas en 30 segundos!' },
  { id:'tetris',     title:'Tetris',         cat:'puzzle',    catLabel:'Puzzle',     emoji:'🟦', bg:'#0d1e2d', accent:'#06b6d4', plays:'8.1M', rating:5.0, desc:'El legendario juego de bloques que cae. ¡Completa líneas!' },
  { id:'pong',       title:'Pong',           cat:'arcade',    catLabel:'Arcade',     emoji:'🏓', bg:'#1a1030', accent:'#f0abfc', plays:'4.7M', rating:4.8, desc:'El primer videojuego de la historia. Primero en llegar a 5 gana' },
  { id:'space',      title:'Space Invaders', cat:'action',    catLabel:'Acción',     emoji:'👾', bg:'#0a0a20', accent:'#818cf8', plays:'6.3M', rating:4.9, desc:'Defiende la Tierra de las oleadas de alienígenas invasores' },
  { id:'gta_augusto',       title:'GTA Augusto',       cat:'action',   catLabel:'Acción',     emoji:'🚗', bg:'#2d0d1a', accent:'#a855f7', plays:'9.9M', rating:5.0, desc:'Augusto recorre la ciudad esquivando tráfico y la policía, recolectando billetes' },
  { id:'minecraft_augusto', title:'Minecraft Augusto', cat:'puzzle',   catLabel:'Puzzle',     emoji:'⛏️', bg:'#0d2d1a', accent:'#22c55e', plays:'7.5M', rating:4.9, desc:'Mina bloques, colecciona recursos y construye en el mundo de Augusto' },
  { id:'wwe_augusto',       title:'WWE Augusto',       cat:'action',   catLabel:'Acción',     emoji:'🤼', bg:'#2d1a0d', accent:'#ef4444', plays:'6.6M', rating:4.8, desc:'Augusto sube al ring y derrota a los luchadores con su Stunner final' },
];

const CATEGORIES = [
  { id:'all',      label:'Todos',       icon:'🎮' },
  { id:'arcade',   label:'Arcade',      icon:'🕹️' },
  { id:'puzzle',   label:'Puzzle',      icon:'🧩' },
  { id:'action',   label:'Acción',      icon:'⚡' },
  { id:'strategy', label:'Estrategia',  icon:'♟️' },
];

// ===================== SCORE HELPERS =====================
function getScores(gameId) {
  try { return JSON.parse(localStorage.getItem('ag_scores_'+gameId)||'[]'); } catch{return [];}
}
function saveScore(gameId, score) {
  const scores = getScores(gameId);
  scores.push({score, date: new Date().toLocaleDateString('es-ES')});
  scores.sort((a,b)=>b.score-a.score);
  localStorage.setItem('ag_scores_'+gameId, JSON.stringify(scores.slice(0,10)));
  const total = parseInt(localStorage.getItem('ag_total_score')||'0') + score;
  const games = parseInt(localStorage.getItem('ag_total_games')||'0') + 1;
  localStorage.setItem('ag_total_score', total);
  localStorage.setItem('ag_total_games', games);
}
function getProfile() {
  return {
    name: localStorage.getItem('ag_player_name') || 'Jugador',
    avatar: localStorage.getItem('ag_player_avatar') || '🎮',
    totalScore: parseInt(localStorage.getItem('ag_total_score')||'0'),
    totalGames: parseInt(localStorage.getItem('ag_total_games')||'0'),
  };
}

// ===================== HEADER =====================
function Header({ onSearch, searchVal, onProfile, profile }) {
  return (
    <header style={{
      height:'var(--header-h)', background:'rgba(7,7,26,0.97)', backdropFilter:'blur(16px)',
      borderBottom:'1px solid var(--border)', display:'flex', alignItems:'center',
      padding:'0 16px', gap:12, position:'sticky', top:0, zIndex:100, flexShrink:0,
    }}>
      <div style={{display:'flex',alignItems:'center',gap:10,flexShrink:0}}>
        <div style={{
          width:36, height:36, borderRadius:10,
          background:'linear-gradient(135deg,var(--purple),var(--cyan))',
          display:'flex', alignItems:'center', justifyContent:'center', fontSize:18,
          boxShadow:'0 0 16px rgba(168,85,247,0.4)',
        }}>🎮</div>
        <span style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:18,
          background:'linear-gradient(90deg,var(--purple),var(--cyan))',
          WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',whiteSpace:'nowrap'}}>
          AugustoGames
        </span>
      </div>

      <div style={{flex:1,maxWidth:400,position:'relative',minWidth:0}}>
        <span style={{position:'absolute',left:12,top:'50%',transform:'translateY(-50%)',color:'var(--muted)',fontSize:14,pointerEvents:'none'}}>🔍</span>
        <input value={searchVal} onChange={e=>onSearch(e.target.value)} placeholder="Buscar juegos..."
          style={{width:'100%',padding:'8px 12px 8px 36px',borderRadius:99,
            background:'var(--surface2)',border:'1px solid var(--border)',
            color:'var(--text)',fontSize:13,fontFamily:'var(--font-body)',outline:'none',transition:'border-color 0.2s'}}
          onFocus={e=>e.target.style.borderColor='var(--purple)'}
          onBlur={e=>e.target.style.borderColor='var(--border)'}/>
      </div>

      <button onClick={onProfile} title="Perfil" style={{
        marginLeft:'auto', display:'flex', alignItems:'center', gap:8,
        background:'var(--surface2)', border:'1px solid var(--border)',
        borderRadius:99, padding:'6px 14px 6px 10px', cursor:'pointer',
        color:'var(--text)', fontFamily:'var(--font-body)', fontWeight:700, fontSize:13,
        transition:'background 0.15s', flexShrink:0,
      }}
      onMouseOver={e=>e.currentTarget.style.background='var(--surface3)'}
      onMouseOut={e=>e.currentTarget.style.background='var(--surface2)'}>
        <span style={{fontSize:20}}>{profile.avatar}</span>
        <span style={{maxWidth:80,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{profile.name}</span>
      </button>
    </header>
  );
}

// ===================== SIDEBAR =====================
function Sidebar({ active, onCat, onPlay }) {
  const top3 = [...GAMES_DATA].sort((a,b)=>parseFloat(b.rating)-parseFloat(a.rating)).slice(0,3);
  return (
    <aside style={{
      width:'var(--sidebar-w)',borderRight:'1px solid var(--border)',
      padding:'16px 10px',display:'flex',flexDirection:'column',gap:4,
      overflowY:'auto',flexShrink:0,
    }}>
      <div style={{color:'var(--muted)',fontSize:10,fontWeight:800,letterSpacing:'0.12em',padding:'0 8px',marginBottom:4}}>CATEGORÍAS</div>
      {CATEGORIES.map(c=>(
        <button key={c.id} onClick={()=>onCat(c.id)} style={{
          display:'flex',alignItems:'center',gap:10,padding:'9px 12px',
          borderRadius:10,background:active===c.id?'var(--surface3)':'transparent',
          border:`1px solid ${active===c.id?'rgba(168,85,247,0.3)':'transparent'}`,
          color:active===c.id?'var(--text)':'var(--muted)',
          fontWeight:active===c.id?700:600,fontSize:14,width:'100%',textAlign:'left',
          transition:'all 0.15s',
        }}
        onMouseOver={e=>{if(active!==c.id){e.currentTarget.style.background='var(--surface2)';e.currentTarget.style.color='var(--text)';}}}
        onMouseOut={e=>{if(active!==c.id){e.currentTarget.style.background='transparent';e.currentTarget.style.color='var(--muted)';}}}
        >
          <span style={{fontSize:16}}>{c.icon}</span>{c.label}
          {active===c.id&&<div style={{marginLeft:'auto',width:6,height:6,borderRadius:99,background:'var(--purple)'}}/>}
        </button>
      ))}
      <div style={{height:1,background:'var(--border)',margin:'10px 0'}}/>
      <div style={{color:'var(--muted)',fontSize:10,fontWeight:800,letterSpacing:'0.12em',padding:'0 8px',marginBottom:4}}>TOP JUEGOS</div>
      {top3.map(g=>(
        <div key={g.id} onClick={()=>onPlay(g)} style={{
          padding:'8px 10px',borderRadius:10,cursor:'pointer',
          display:'flex',alignItems:'center',gap:10,transition:'background 0.15s',
        }}
        onMouseOver={e=>e.currentTarget.style.background='var(--surface2)'}
        onMouseOut={e=>e.currentTarget.style.background='transparent'}>
          <div style={{width:30,height:30,borderRadius:8,background:g.bg,display:'flex',alignItems:'center',justifyContent:'center',fontSize:16,flexShrink:0}}>{g.emoji}</div>
          <div style={{minWidth:0}}>
            <div style={{fontSize:12,fontWeight:700,color:'var(--text)',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{g.title}</div>
            <div style={{fontSize:11,color:'var(--muted)'}}>⭐ {g.rating}</div>
          </div>
        </div>
      ))}
    </aside>
  );
}

// ===================== GAME CARD =====================
function GameCard({ game, onClick, delay=0 }) {
  const [hov,setHov]=React.useState(false);
  const best = getScores(game.id)[0];
  return (
    <div onClick={()=>onClick(game)} onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{
        borderRadius:14,background:'var(--surface)',border:`1px solid ${hov?'rgba(255,255,255,0.12)':'var(--border)'}`,
        overflow:'hidden',cursor:'pointer',
        transform:hov?'translateY(-5px) scale(1.01)':'translateY(0) scale(1)',
        transition:'transform 0.22s cubic-bezier(0.34,1.56,0.64,1), border-color 0.2s, box-shadow 0.2s',
        boxShadow:hov?`0 16px 48px rgba(0,0,0,0.6), 0 0 0 1px ${game.accent}44`:'0 2px 8px rgba(0,0,0,0.3)',
        animation:`fadeUp 0.4s ease ${delay}s both`,
      }}>
      <div style={{height:120,background:game.bg,display:'flex',alignItems:'center',justifyContent:'center',position:'relative',overflow:'hidden'}}>
        <div style={{position:'absolute',inset:0,background:`radial-gradient(circle at center, ${game.accent}28 0%, transparent 70%)`}}/>
        <div style={{fontSize:56,filter:'drop-shadow(0 0 18px rgba(0,0,0,0.5))',
          transform:hov?'scale(1.15)':'scale(1)',transition:'transform 0.3s'}}>{game.emoji}</div>
        <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
          background:'rgba(7,7,26,0.7)',opacity:hov?1:0,transition:'opacity 0.2s'}}>
          <div style={{width:44,height:44,borderRadius:99,background:game.accent,
            display:'flex',alignItems:'center',justifyContent:'center',fontSize:18,
            boxShadow:`0 0 24px ${game.accent}99`}}>▶</div>
        </div>
        <div style={{position:'absolute',top:8,left:8,background:'rgba(7,7,26,0.82)',
          borderRadius:99,padding:'3px 9px',fontSize:10,fontWeight:800,
          color:game.accent,backdropFilter:'blur(4px)',border:`1px solid ${game.accent}44`,letterSpacing:'0.06em'}}>
          {game.catLabel}
        </div>
        {best&&<div style={{position:'absolute',top:8,right:8,background:'rgba(7,7,26,0.82)',
          borderRadius:99,padding:'3px 9px',fontSize:10,fontWeight:700,
          color:'var(--orange)',backdropFilter:'blur(4px)'}}>
          🏆 {best.score}
        </div>}
      </div>
      <div style={{padding:'10px 12px'}}>
        <div style={{fontWeight:800,fontSize:14,marginBottom:3}}>{game.title}</div>
        <div style={{color:'var(--muted)',fontSize:11,marginBottom:8,lineHeight:1.4,textWrap:'pretty',display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical',overflow:'hidden'}}>{game.desc}</div>
        <div style={{display:'flex',alignItems:'center',gap:6}}>
          <span style={{color:'#facc15',fontSize:11}}>{'★'.repeat(Math.round(game.rating))}</span>
          <span style={{color:'var(--muted)',fontSize:11}}>{game.rating}</span>
          <span style={{marginLeft:'auto',color:'var(--muted)',fontSize:11}}>🎮 {game.plays}</span>
        </div>
      </div>
    </div>
  );
}

// ===================== FEATURED BANNER =====================
function FeaturedBanner({ onPlay }) {
  const g = GAMES_DATA.find(g=>g.id==='tetris');
  return (
    <div style={{
      borderRadius:14,background:'linear-gradient(135deg,#0d1a2d 0%,#0d0d22 50%,#1a0d20 100%)',
      border:'1px solid var(--border)',padding:'24px 28px',marginBottom:20,
      display:'flex',alignItems:'center',gap:24,overflow:'hidden',position:'relative',
      animation:'fadeUp 0.3s ease',
    }}>
      <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 75% 50%,rgba(6,182,212,0.1) 0%,transparent 60%)'}}/>
      <div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at 25% 50%,rgba(168,85,247,0.07) 0%,transparent 60%)'}}/>
      <div style={{position:'relative',flex:1,minWidth:0}}>
        <div style={{display:'inline-flex',alignItems:'center',gap:6,background:'var(--orange)',
          borderRadius:99,padding:'3px 12px',fontSize:11,fontWeight:800,color:'#000',
          letterSpacing:'0.05em',marginBottom:10}}>🔥 DESTACADO</div>
        <h2 style={{fontFamily:'var(--font-display)',fontSize:28,fontWeight:900,marginBottom:6,lineHeight:1.1}}>
          {g.emoji} {g.title}
        </h2>
        <p style={{color:'var(--muted)',fontSize:13,marginBottom:16,textWrap:'pretty',maxWidth:340}}>{g.desc}</p>
        <div style={{display:'flex',alignItems:'center',gap:14,flexWrap:'wrap'}}>
          <button onClick={()=>onPlay(g)} style={{
            padding:'10px 24px',borderRadius:99,
            background:'linear-gradient(90deg,var(--purple),var(--cyan))',
            color:'#fff',fontWeight:800,fontSize:14,fontFamily:'var(--font-body)',
            boxShadow:'0 4px 20px rgba(168,85,247,0.4)',transition:'transform 0.15s,box-shadow 0.2s',
          }}
          onMouseOver={e=>{e.target.style.transform='scale(1.04)';e.target.style.boxShadow='0 6px 28px rgba(168,85,247,0.6)';}}
          onMouseOut={e=>{e.target.style.transform='scale(1)';e.target.style.boxShadow='0 4px 20px rgba(168,85,247,0.4)';}}>
            ▶ Jugar Ahora
          </button>
          <span style={{color:'var(--muted)',fontSize:12}}>⭐ {g.rating} · 🎮 {g.plays}</span>
        </div>
      </div>
      <div style={{fontSize:80,flexShrink:0,filter:'drop-shadow(0 0 24px rgba(6,182,212,0.4))',
        animation:'pulse 3s ease infinite'}}>{g.emoji}</div>
    </div>
  );
}

// ===================== LEADERBOARD MODAL =====================
function LeaderboardModal({ onClose }) {
  const [tab,setTab]=React.useState(GAMES_DATA[0].id);
  const scores=getScores(tab);
  const game=GAMES_DATA.find(g=>g.id===tab);
  return (
    <div style={{position:'fixed',inset:0,zIndex:300,background:'rgba(7,7,26,0.9)',backdropFilter:'blur(10px)',
      display:'flex',alignItems:'center',justifyContent:'center',padding:16,animation:'fadeUp 0.2s ease'}}>
      <div style={{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:20,
        width:'100%',maxWidth:500,maxHeight:'80vh',display:'flex',flexDirection:'column',overflow:'hidden'}}>
        <div style={{padding:'20px 20px 0',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
          <h2 style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:22}}>🏆 Mejores Puntuaciones</h2>
          <button onClick={onClose} style={{background:'var(--surface2)',border:'1px solid var(--border)',
            color:'var(--muted)',borderRadius:99,width:32,height:32,fontSize:16,display:'flex',alignItems:'center',justifyContent:'center'}}>✕</button>
        </div>
        {/* Game tabs */}
        <div style={{padding:'12px 20px',display:'flex',gap:6,overflowX:'auto',flexShrink:0}}>
          {GAMES_DATA.map(g=>(
            <button key={g.id} onClick={()=>setTab(g.id)} style={{
              padding:'6px 12px',borderRadius:99,fontSize:12,fontWeight:700,whiteSpace:'nowrap',
              background:tab===g.id?game.accent:'var(--surface2)',
              color:tab===g.id?'#000':'var(--muted)',border:'1px solid var(--border)',
              transition:'all 0.15s',
            }}>{g.emoji} {g.title}</button>
          ))}
        </div>
        <div style={{flex:1,overflowY:'auto',padding:'0 20px 20px'}}>
          {scores.length===0?(
            <div style={{textAlign:'center',padding:'40px 0',color:'var(--muted)'}}>
              <div style={{fontSize:40,marginBottom:8}}>{game.emoji}</div>
              <div style={{fontWeight:700}}>Sin partidas todavía</div>
              <div style={{fontSize:13,marginTop:4}}>¡Juega para aparecer aquí!</div>
            </div>
          ):(
            <div style={{display:'flex',flexDirection:'column',gap:6}}>
              {scores.map((s,i)=>(
                <div key={i} style={{display:'flex',alignItems:'center',gap:12,
                  background:'var(--surface2)',borderRadius:10,padding:'10px 14px',
                  border:`1px solid ${i===0?game.accent+'44':'var(--border)'}`,
                  boxShadow:i===0?`0 0 16px ${game.accent}22`:'none'}}>
                  <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:18,
                    color:['var(--orange)','var(--muted)','#cd7f32'][i]||'var(--muted)',
                    width:28,textAlign:'center'}}>
                    {['🥇','🥈','🥉'][i]||`#${i+1}`}
                  </div>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:800,fontSize:15,color:i===0?game.accent:'var(--text)'}}>{s.score.toLocaleString()} pts</div>
                    <div style={{fontSize:11,color:'var(--muted)'}}>{s.date}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ===================== PROFILE MODAL =====================
function ProfileModal({ onClose }) {
  const [profile,setProfile]=React.useState(getProfile);
  const [editName,setEditName]=React.useState(false);
  const [nameVal,setNameVal]=React.useState(profile.name);
  const AVATARS=['🎮','🕹️','👾','🦊','🐉','⚡','🌟','🔥','💎','🎯','🚀','🏆'];

  const saveName=()=>{
    if(nameVal.trim()){
      localStorage.setItem('ag_player_name',nameVal.trim());
      setProfile(p=>({...p,name:nameVal.trim()}));
    }
    setEditName(false);
  };
  const setAvatar=a=>{
    localStorage.setItem('ag_player_avatar',a);
    setProfile(p=>({...p,avatar:a}));
  };

  const allBests=GAMES_DATA.map(g=>({game:g,best:getScores(g.id)[0]})).filter(x=>x.best);

  return (
    <div style={{position:'fixed',inset:0,zIndex:300,background:'rgba(7,7,26,0.9)',backdropFilter:'blur(10px)',
      display:'flex',alignItems:'center',justifyContent:'center',padding:16,animation:'fadeUp 0.2s ease'}}>
      <div style={{background:'var(--surface)',border:'1px solid var(--border)',borderRadius:20,
        width:'100%',maxWidth:480,maxHeight:'85vh',display:'flex',flexDirection:'column',overflow:'hidden'}}>
        {/* Header */}
        <div style={{padding:'20px',display:'flex',alignItems:'center',justifyContent:'space-between',
          borderBottom:'1px solid var(--border)'}}>
          <h2 style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:22}}>👤 Mi Perfil</h2>
          <button onClick={onClose} style={{background:'var(--surface2)',border:'1px solid var(--border)',
            color:'var(--muted)',borderRadius:99,width:32,height:32,fontSize:16,
            display:'flex',alignItems:'center',justifyContent:'center'}}>✕</button>
        </div>
        <div style={{flex:1,overflowY:'auto',padding:20,display:'flex',flexDirection:'column',gap:20}}>
          {/* Avatar + Name */}
          <div style={{display:'flex',alignItems:'center',gap:16}}>
            <div style={{width:64,height:64,borderRadius:18,background:'var(--surface2)',
              display:'flex',alignItems:'center',justifyContent:'center',fontSize:36,
              border:'2px solid var(--purple)',boxShadow:'0 0 20px rgba(168,85,247,0.3)'}}>
              {profile.avatar}
            </div>
            <div style={{flex:1}}>
              {editName?(
                <div style={{display:'flex',gap:8}}>
                  <input value={nameVal} onChange={e=>setNameVal(e.target.value)}
                    onKeyDown={e=>e.key==='Enter'&&saveName()}
                    autoFocus
                    style={{flex:1,background:'var(--surface2)',border:'1px solid var(--purple)',
                      borderRadius:8,padding:'7px 12px',color:'var(--text)',fontSize:15,
                      fontFamily:'var(--font-body)',fontWeight:700,outline:'none'}}/>
                  <button onClick={saveName} style={{...gBtnStyle,padding:'7px 16px',fontSize:13}}>✓</button>
                </div>
              ):(
                <div style={{display:'flex',alignItems:'center',gap:8}}>
                  <span style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:20}}>{profile.name}</span>
                  <button onClick={()=>setEditName(true)} style={{background:'transparent',border:'none',
                    color:'var(--muted)',fontSize:14,padding:4,cursor:'pointer'}}>✏️</button>
                </div>
              )}
              <div style={{color:'var(--muted)',fontSize:12,marginTop:2}}>Jugador de AugustoGames</div>
            </div>
          </div>

          {/* Avatar picker */}
          <div>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:800,letterSpacing:'0.1em',marginBottom:8}}>ELIGE TU AVATAR</div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
              {AVATARS.map(a=>(
                <button key={a} onClick={()=>setAvatar(a)} style={{
                  width:40,height:40,borderRadius:10,fontSize:22,
                  background:profile.avatar===a?'var(--surface3)':'var(--surface2)',
                  border:`2px solid ${profile.avatar===a?'var(--purple)':'transparent'}`,
                  transition:'all 0.15s',cursor:'pointer',
                  boxShadow:profile.avatar===a?'0 0 12px rgba(168,85,247,0.4)':'none',
                }}>{a}</button>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:800,letterSpacing:'0.1em',marginBottom:8}}>ESTADÍSTICAS</div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
              {[
                {label:'Partidas jugadas',val:profile.totalGames,color:'var(--cyan)',icon:'🎮'},
                {label:'Puntuación total',val:profile.totalScore.toLocaleString(),color:'var(--orange)',icon:'⭐'},
              ].map(stat=>(
                <div key={stat.label} style={{background:'var(--surface2)',borderRadius:12,padding:'14px',
                  border:'1px solid var(--border)'}}>
                  <div style={{fontSize:24,marginBottom:4}}>{stat.icon}</div>
                  <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:22,color:stat.color}}>{stat.val}</div>
                  <div style={{color:'var(--muted)',fontSize:12}}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Best scores */}
          {allBests.length>0&&<div>
            <div style={{color:'var(--muted)',fontSize:11,fontWeight:800,letterSpacing:'0.1em',marginBottom:8}}>MEJORES PUNTUACIONES</div>
            <div style={{display:'flex',flexDirection:'column',gap:6}}>
              {allBests.sort((a,b)=>b.best.score-a.best.score).map(({game,best})=>(
                <div key={game.id} style={{display:'flex',alignItems:'center',gap:10,
                  background:'var(--surface2)',borderRadius:10,padding:'10px 12px',border:'1px solid var(--border)'}}>
                  <div style={{width:28,height:28,borderRadius:8,background:game.bg,
                    display:'flex',alignItems:'center',justifyContent:'center',fontSize:16}}>{game.emoji}</div>
                  <span style={{flex:1,fontSize:13,fontWeight:700}}>{game.title}</span>
                  <span style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:15,color:game.accent}}>
                    {best.score.toLocaleString()} pts
                  </span>
                </div>
              ))}
            </div>
          </div>}
        </div>
      </div>
    </div>
  );
}

// ===================== APP SHELL =====================
function AppShell({ onPlay }) {
  const [search,setSearch]=React.useState('');
  const [cat,setCat]=React.useState('all');
  const [showLeaderboard,setShowLeaderboard]=React.useState(false);
  const [showProfile,setShowProfile]=React.useState(false);
  const [profile,setProfile]=React.useState(getProfile);

  React.useEffect(()=>{
    const handler=()=>setProfile(getProfile());
    window.addEventListener('ag_profile_update',handler);
    return ()=>window.removeEventListener('ag_profile_update',handler);
  },[]);

  const filtered=GAMES_DATA.filter(g=>{
    if(cat!=='all'&&g.cat!==cat) return false;
    if(search&&!g.title.toLowerCase().includes(search.toLowerCase())&&!g.catLabel.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{display:'flex',flexDirection:'column',height:'100vh',overflow:'hidden'}}>
      <Header onSearch={setSearch} searchVal={search} onProfile={()=>setShowProfile(true)} profile={profile}/>
      <div style={{display:'flex',flex:1,overflow:'hidden'}}>
        <Sidebar active={cat} onCat={setCat} onPlay={onPlay}/>
        <main style={{flex:1,overflowY:'auto',padding:'20px'}}>
          {cat==='all'&&!search&&<FeaturedBanner onPlay={onPlay}/>}

          <div style={{marginBottom:14,display:'flex',alignItems:'center',gap:10}}>
            <h2 style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:18}}>
              {search?`"${search}"`:cat==='all'?'Todos los Juegos':CATEGORIES.find(c=>c.id===cat)?.label}
            </h2>
            <span style={{color:'var(--muted)',fontSize:12,background:'var(--surface2)',
              borderRadius:99,padding:'2px 10px',border:'1px solid var(--border)'}}>{filtered.length}</span>
            <button onClick={()=>setShowLeaderboard(true)} style={{
              marginLeft:'auto',background:'var(--surface2)',border:'1px solid var(--border)',
              color:'var(--text)',borderRadius:99,padding:'6px 14px',fontSize:12,fontWeight:700,
              fontFamily:'var(--font-body)',display:'flex',alignItems:'center',gap:6,transition:'background 0.15s',
            }}
            onMouseOver={e=>e.currentTarget.style.background='var(--surface3)'}
            onMouseOut={e=>e.currentTarget.style.background='var(--surface2)'}>
              🏆 Ranking
            </button>
          </div>

          {filtered.length===0?(
            <div style={{textAlign:'center',padding:'60px 0',color:'var(--muted)'}}>
              <div style={{fontSize:48,marginBottom:12}}>🔍</div>
              <div style={{fontSize:16,fontWeight:700}}>No se encontraron juegos</div>
            </div>
          ):(
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(190px,1fr))',gap:14}}>
              {filtered.map((g,i)=><GameCard key={g.id} game={g} onClick={onPlay} delay={i*0.04}/>)}
            </div>
          )}
        </main>
      </div>
      {showLeaderboard&&<LeaderboardModal onClose={()=>setShowLeaderboard(false)}/>}
      {showProfile&&<ProfileModal onClose={()=>{setShowProfile(false);setProfile(getProfile());}}/>}
    </div>
  );
}

Object.assign(window, { AppShell, GAMES_DATA, saveScore, getScores, getProfile });
