const GAME_COMPONENTS = {
  snake:              () => <SnakeGame />,
  memory:             () => <MemoryGame />,
  tictactoe:          () => <TicTacToeGame />,
  bricks:             () => <BrickBreakerGame />,
  game2048:           () => <Game2048 />,
  wham:               () => <WhackAMole />,
  tetris:             () => <TetrisGame />,
  pong:               () => <PongGame />,
  space:              () => <SpaceInvaders />,
  gta_augusto:        () => <GTAAugustoGame />,
  minecraft_augusto:  () => <MinecraftAugustoGame />,
  wwe_augusto:        () => <WWEAugustoGame />,
};

function GameModal({ game, onClose, onScore }) {
  const GameComp = GAME_COMPONENTS[game.id];
  const isIframeGame = ['gta_augusto','minecraft_augusto','wwe_augusto'].includes(game.id);

  React.useEffect(() => {
    // Listen for score events from games
    const handler = e => {
      if (e.detail.game === game.id) {
        onScore(e.detail.game, e.detail.score);
      }
    };
    window.addEventListener('ag_score', handler);
    return () => window.removeEventListener('ag_score', handler);
  }, [game.id, onScore]);

  React.useEffect(() => {
    const esc = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [onClose]);

  return (
    <div style={{
      position:'fixed', inset:0, zIndex:200,
      background:'rgba(7,7,26,0.94)', backdropFilter:'blur(14px)',
      display:'flex', flexDirection:'column', alignItems:'center',
      padding:'14px', overflowY:'auto', animation:'fadeUp 0.22s ease',
    }}>
      {/* Top bar */}
      <div style={{
        width:'100%', maxWidth:960, display:'flex', alignItems:'center',
        gap:12, marginBottom:18, flexShrink:0,
      }}>
        <button onClick={onClose} style={{
          background:'var(--surface2)', border:'1px solid var(--border)',
          color:'var(--text)', borderRadius:99, padding:'7px 16px',
          fontFamily:'var(--font-body)', fontWeight:700, fontSize:13,
          display:'flex', alignItems:'center', gap:6, transition:'background 0.15s', cursor:'pointer',
        }}
        onMouseOver={e=>e.currentTarget.style.background='var(--surface3)'}
        onMouseOut={e=>e.currentTarget.style.background='var(--surface2)'}>
          ← Volver
        </button>

        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div style={{width:34,height:34,borderRadius:9,background:game.bg,
            display:'flex',alignItems:'center',justifyContent:'center',fontSize:18,
            border:`1px solid ${game.accent}44`}}>{game.emoji}</div>
          <div>
            <div style={{fontFamily:'var(--font-display)',fontWeight:900,fontSize:16,lineHeight:1.1}}>{game.title}</div>
            <div style={{color:'var(--muted)',fontSize:11,display:'flex',gap:6}}>
              <span style={{color:game.accent}}>{game.catLabel}</span>
              <span>·</span><span>⭐ {game.rating}</span>
              <span>·</span><span>🎮 {game.plays}</span>
            </div>
          </div>
        </div>

        {/* Best score badge */}
        {(() => { const best = getScores(game.id)[0]; return best ? (
          <div style={{
            marginLeft:8, background:'rgba(250,204,21,0.1)', border:'1px solid rgba(250,204,21,0.3)',
            borderRadius:99, padding:'4px 12px', fontSize:12, fontWeight:700, color:'#facc15',
          }}>🏆 Récord: {best.score.toLocaleString()}</div>
        ) : null; })()}

        <div style={{marginLeft:'auto',color:'var(--muted)',fontSize:12,display:'flex',alignItems:'center',gap:6}}>
          <kbd style={{background:'var(--surface2)',border:'1px solid var(--border)',
            borderRadius:6,padding:'2px 8px',fontSize:11}}>ESC</kbd> para salir
        </div>
      </div>

      {/* Game area */}
      <div style={{
        background:'var(--surface)', border:'1px solid var(--border)',
        borderRadius:20,
        padding: isIframeGame ? '10px' : '28px 20px',
        boxShadow:`0 0 80px ${game.accent}18, 0 24px 80px rgba(0,0,0,0.6)`,
        maxWidth:960, width:'100%',
      }}>
        {GameComp && <GameComp />}
      </div>
    </div>
  );
}

// Score notification toast
function ScoreToast({ score, game, onDone }) {
  React.useEffect(() => {
    const t = setTimeout(onDone, 2800);
    return () => clearTimeout(t);
  }, []);
  return (
    <div style={{
      position:'fixed', bottom:28, right:24, zIndex:500,
      background:'var(--surface)', border:`1px solid ${game.accent}66`,
      borderRadius:16, padding:'14px 20px', display:'flex', alignItems:'center', gap:12,
      boxShadow:`0 8px 40px rgba(0,0,0,0.5), 0 0 0 1px ${game.accent}33`,
      animation:'fadeUp 0.3s ease',
    }}>
      <div style={{fontSize:28}}>{game.emoji}</div>
      <div>
        <div style={{fontWeight:800,fontSize:14,color:'var(--text)'}}>{game.title} — ¡Partida guardada!</div>
        <div style={{color:game.accent,fontFamily:'var(--font-display)',fontWeight:900,fontSize:18}}>
          {score.toLocaleString()} pts
        </div>
      </div>
      <div style={{width:4,height:40,borderRadius:99,background:game.accent,opacity:0.6,marginLeft:4}}/>
    </div>
  );
}

function App() {
  const [activeGame, setActiveGame] = React.useState(() => {
    try { const s=localStorage.getItem('ag_active_game'); return s?JSON.parse(s):null; } catch{return null;}
  });
  const [toast, setToast] = React.useState(null);

  const openGame = g => {
    setActiveGame(g);
    localStorage.setItem('ag_active_game', JSON.stringify(g));
  };
  const closeGame = () => {
    setActiveGame(null);
    localStorage.removeItem('ag_active_game');
  };
  const handleScore = React.useCallback((gameId, score) => {
    if (!score || score <= 0) return;
    saveScore(gameId, score);
    const game = GAMES_DATA.find(g => g.id === gameId);
    if (game) setToast({ score, game });
    window.dispatchEvent(new Event('ag_profile_update'));
  }, []);

  // Listen to postMessage from iframe-based games (Augusto City / Minecraft / WWE)
  React.useEffect(() => {
    const onMsg = (e) => {
      const d = e.data;
      if (!d || d.type !== 'ag_score' || !d.game) return;
      const s = parseInt(d.score, 10);
      if (!isFinite(s) || s <= 0) return;
      handleScore(d.game, s);
    };
    window.addEventListener('message', onMsg);
    return () => window.removeEventListener('message', onMsg);
  }, [handleScore]);

  return (
    <>
      <AppShell onPlay={openGame} />
      {activeGame && <GameModal game={activeGame} onClose={closeGame} onScore={handleScore} />}
      {toast && <ScoreToast score={toast.score} game={toast.game} onDone={() => setToast(null)} />}
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
