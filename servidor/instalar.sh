#!/usr/bin/env bash
# ------------------------------------------------------------------
#  AugustoGames: instala el sitio (con Furious Cars 2) en este PC con
#  Ubuntu y lo publica en internet.
#
#  Uso (desde la carpeta del proyecto):
#    bash servidor/instalar.sh                       red local + enlace público gratis (Cloudflare)
#    bash servidor/instalar.sh --dominio TU.DOMINIO  dominio propio con HTTPS (abre los puertos 80 y 443 en el router)
#    bash servidor/instalar.sh --solo-local          solo para los equipos de tu casa
# ------------------------------------------------------------------
set -euo pipefail

MODO="tunel"
DOMINIO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dominio) MODO="dominio"; DOMINIO="${2:-}"; shift 2 ;;
    --solo-local) MODO="local"; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "Opción desconocida: $1 (usa --help)"; exit 1 ;;
  esac
done
if [[ "$MODO" == "dominio" && -z "$DOMINIO" ]]; then echo "Falta el dominio: --dominio juegos.midominio.com"; exit 1; fi

AZUL=$'\e[1;34m'; VERDE=$'\e[1;32m'; AMARILLO=$'\e[1;33m'; ROJO=$'\e[1;31m'; FIN=$'\e[0m'
paso() { echo; echo "${AZUL}==> $*${FIN}"; }
ok()   { echo "${VERDE}✔ $*${FIN}"; }
aviso(){ echo "${AMARILLO}! $*${FIN}"; }

if [[ "$(uname -s)" != "Linux" ]] || ! command -v apt-get >/dev/null; then
  echo "${ROJO}Este instalador es para Ubuntu (o Debian).${FIN}"; exit 1
fi
SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"

DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGEN="$(dirname "$DIR_SCRIPT")"
WEB=/var/www/augustogames
if [[ ! -f "$ORIGEN/index.html" || ! -f "$ORIGEN/furious-cars-2.html" ]]; then
  echo "${ROJO}No encuentro los juegos en $ORIGEN. Ejecuta el script desde la carpeta del proyecto.${FIN}"; exit 1
fi

paso "Instalando programas necesarios (te pedirá tu contraseña)"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq rsync curl ca-certificates gnupg >/dev/null
if ! command -v caddy >/dev/null; then
  # Ubuntu 24.04 trae Caddy; en versiones anteriores se usa el repositorio oficial
  if ! $SUDO apt-get install -y -qq caddy >/dev/null 2>&1; then
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | $SUDO gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | $SUDO tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    $SUDO apt-get update -qq
    $SUDO apt-get install -y -qq caddy >/dev/null
  fi
fi
ok "Caddy $(caddy version | cut -d' ' -f1) instalado"

paso "Copiando los juegos a $WEB"
bash "$DIR_SCRIPT/actualizar.sh" --sin-git

paso "Configurando el servidor web"
SITIO=":80"; [[ "$MODO" == "dominio" ]] && SITIO="$DOMINIO"
[[ -f /etc/caddy/Caddyfile && ! -f /etc/caddy/Caddyfile.original ]] && $SUDO cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.original
$SUDO tee /etc/caddy/Caddyfile >/dev/null <<EOF
# AugustoGames (generado por servidor/instalar.sh)
$SITIO {
	root * $WEB
	file_server
	encode zstd gzip
	# que los cambios se vean al momento; las imágenes y modelos se guardan en caché
	@paginas path / *.html *.jsx
	header @paginas Cache-Control "no-cache"
	header /assets/* Cache-Control "public, max-age=604800"
	header X-Content-Type-Options nosniff
}
EOF
$SUDO caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null
$SUDO systemctl enable --now caddy >/dev/null 2>&1 || true
$SUDO systemctl reload caddy 2>/dev/null || $SUDO systemctl restart caddy
ok "Servidor web activo"

if command -v ufw >/dev/null && $SUDO ufw status | grep -q "Status: active"; then
  $SUDO ufw allow 80/tcp >/dev/null
  [[ "$MODO" == "dominio" ]] && $SUDO ufw allow 443/tcp >/dev/null
  ok "Cortafuegos (ufw) abierto para la web"
fi

ENLACE=""
if [[ "$MODO" == "tunel" ]]; then
  paso "Creando el enlace público gratuito (Cloudflare Tunnel)"
  if ! command -v cloudflared >/dev/null; then
    ARQ="$(dpkg --print-architecture)"   # amd64, arm64, armhf…
    TMP="$(mktemp -d)"
    curl -fsSL -o "$TMP/cloudflared.deb" "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$ARQ.deb"
    $SUDO apt-get install -y -qq "$TMP/cloudflared.deb" >/dev/null
    rm -rf "$TMP"
  fi
  $SUDO tee /etc/systemd/system/augusto-tunel.service >/dev/null <<'EOF'
[Unit]
Description=Enlace público de AugustoGames (Cloudflare Tunnel)
After=network-online.target caddy.service
Wants=network-online.target

[Service]
ExecStart=/usr/bin/cloudflared tunnel --no-autoupdate --url http://localhost:80
Restart=always
RestartSec=5
DynamicUser=yes

[Install]
WantedBy=multi-user.target
EOF
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable augusto-tunel >/dev/null 2>&1
  $SUDO systemctl restart augusto-tunel
  echo -n "Esperando el enlace"
  CONECTADO=""
  for _ in $(seq 1 60); do
    LOG="$($SUDO journalctl -u augusto-tunel --no-pager -n 300 2>/dev/null || true)"
    ENLACE="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' <<<"$LOG" | tail -1 || true)"
    grep -q "Registered tunnel connection" <<<"$LOG" && CONECTADO=1
    [[ -n "$ENLACE" && -n "$CONECTADO" ]] && break
    echo -n "."; sleep 1
  done
  echo
  if [[ -n "$ENLACE" && -z "$CONECTADO" ]]; then
    aviso "Cloudflare dio el enlace pero todavía no conecta. Si en unos minutos sigue sin cargar, tu red bloquea el puerto 7844 (revisa el router o usa --dominio)."
  fi
else
  if systemctl list-unit-files augusto-tunel.service >/dev/null 2>&1; then
    $SUDO systemctl disable --now augusto-tunel >/dev/null 2>&1 || true
  fi
fi

IP_LOCAL="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo
echo "${VERDE}════════════════════════════════════════════════════════${FIN}"
echo "${VERDE}  ¡AugustoGames está en línea!${FIN}"
echo "${VERDE}════════════════════════════════════════════════════════${FIN}"
echo "  En este PC:           http://localhost/"
[[ -n "$IP_LOCAL" ]] && echo "  En tu casa (wifi):    http://$IP_LOCAL/"
case "$MODO" in
  tunel)
    if [[ -n "$ENLACE" ]]; then
      echo "  Para todo el mundo:   $ENLACE"
      echo "  Furious Cars 2:       $ENLACE/furious-cars-2.html"
    else
      aviso "El enlace público aún no aparece. Prueba en un minuto con: bash servidor/enlace.sh"
    fi
    echo
    aviso "El enlace de Cloudflare cambia si reinicias el PC. Míralo con: bash servidor/enlace.sh"
    ;;
  dominio)
    echo "  Para todo el mundo:   https://$DOMINIO/"
    echo
    aviso "Recuerda abrir los puertos 80 y 443 del router hacia $IP_LOCAL y apuntar $DOMINIO a tu IP pública."
    ;;
  local)
    echo "  (solo disponible dentro de tu red)"
    ;;
esac
echo
echo "  Para publicar cambios del juego:  bash servidor/actualizar.sh"
echo "  El sitio arranca solo cada vez que enciendes el PC."
echo
