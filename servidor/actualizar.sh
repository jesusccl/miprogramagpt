#!/usr/bin/env bash
# Publica la última versión de los juegos en el servidor de este PC.
#   bash servidor/actualizar.sh            descarga los cambios de GitHub (git pull) y los publica
#   bash servidor/actualizar.sh --sin-git  publica lo que ya hay en la carpeta
set -euo pipefail
SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"
DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGEN="$(dirname "$DIR_SCRIPT")"
WEB=/var/www/augustogames

if [[ "${1:-}" != "--sin-git" && -d "$ORIGEN/.git" ]]; then
  echo "Descargando cambios de GitHub…"
  git -C "$ORIGEN" pull --ff-only || echo "! No se pudo actualizar desde GitHub; publico la versión local."
fi

$SUDO mkdir -p "$WEB"
# solo lo que el navegador necesita (sin herramientas, scripts ni historial de git)
$SUDO rsync -a --delete \
  --exclude '.git' --exclude '.gitignore' --exclude 'tools/' --exclude 'servidor/' \
  --exclude 'CNAME' --exclude '*.md' --exclude '__pycache__/' \
  "$ORIGEN/" "$WEB/"
$SUDO chmod -R a+rX "$WEB"
$SUDO systemctl reload caddy 2>/dev/null || true
echo "✔ Juegos publicados en $WEB ($(find "$WEB" -type f | wc -l) archivos)"
