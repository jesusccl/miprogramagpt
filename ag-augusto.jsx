// ===================== AUGUSTO GAMES (HTML iframes) =====================
// Los 3 juegos de Augusto son HTMLs standalone (three.js, controles táctiles,
// físicas propias). Se cargan en un iframe aislado para no chocar con el shell.
// El bridge inyectado en cada HTML envía `postMessage({type:'ag_score',...})`
// cuando termina la partida → el shell lo recibe y guarda el récord.

function AugustoIframe({ src, title, aspectRatio }) {
  const frameRef = React.useRef(null);
  const [loaded, setLoaded] = React.useState(false);

  const openFullscreen = () => {
    const el = frameRef.current;
    if (!el) return;
    if (el.requestFullscreen) el.requestFullscreen();
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
  };

  const wrapStyle = {
    width: '100%',
    maxWidth: 900,
    aspectRatio: aspectRatio || '16 / 10',
    position: 'relative',
    borderRadius: 14,
    overflow: 'hidden',
    background: '#000',
    border: '1px solid var(--border)',
    boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
  };

  return (
    <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:10,width:'100%'}}>
      <div style={wrapStyle}>
        {!loaded && (
          <div style={{
            position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
            color:'var(--muted)',fontSize:14,zIndex:1,
          }}>
            <div style={{textAlign:'center'}}>
              <div style={{fontSize:32,marginBottom:8,animation:'pulse 1.5s ease infinite'}}>🎮</div>
              <div>Cargando {title}…</div>
            </div>
          </div>
        )}
        <iframe
          ref={frameRef}
          src={src}
          title={title}
          onLoad={() => setLoaded(true)}
          allow="gamepad; fullscreen; accelerometer; gyroscope; autoplay"
          allowFullScreen
          style={{
            width:'100%',height:'100%',border:'none',display:'block',
            background:'#000',
          }}
        />
      </div>
      <div style={{display:'flex',gap:10,alignItems:'center',flexWrap:'wrap',justifyContent:'center'}}>
        <button onClick={openFullscreen} style={{
          background:'var(--surface2)',border:'1px solid var(--border)',
          color:'var(--text)',borderRadius:99,padding:'7px 16px',
          fontFamily:'var(--font-body)',fontWeight:700,fontSize:13,
          display:'flex',alignItems:'center',gap:6,cursor:'pointer',
        }}
        onMouseOver={e=>e.currentTarget.style.background='var(--surface3)'}
        onMouseOut={e=>e.currentTarget.style.background='var(--surface2)'}>
          ⛶ Pantalla completa
        </button>
        <div style={{color:'var(--muted)',fontSize:11,maxWidth:500,textAlign:'center'}}>
          Tus récords se guardan automáticamente al terminar la partida.
        </div>
      </div>
    </div>
  );
}

function GTAAugustoGame() {
  return <AugustoIframe src="augusto-city.html" title="GTA Augusto" aspectRatio="16 / 10" />;
}

function MinecraftAugustoGame() {
  return <AugustoIframe src="minecraft.html" title="Minecraft Augusto" aspectRatio="16 / 10" />;
}

function WWEAugustoGame() {
  return <AugustoIframe src="wwe.html" title="WWE Augusto" aspectRatio="16 / 10" />;
}

Object.assign(window, { GTAAugustoGame, MinecraftAugustoGame, WWEAugustoGame });
