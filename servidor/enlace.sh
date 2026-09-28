#!/usr/bin/env bash
# Muestra las direcciones donde se puede jugar ahora mismo.
SUDO=""; [[ $EUID -ne 0 ]] && SUDO="sudo"
IP_LOCAL="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "En este PC:          http://localhost/"
[[ -n "$IP_LOCAL" ]] && echo "En tu casa (wifi):   http://$IP_LOCAL/"
if systemctl is-active --quiet augusto-tunel 2>/dev/null; then
  ENLACE="$($SUDO journalctl -u augusto-tunel --no-pager -n 300 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1)"
  if [[ -n "$ENLACE" ]]; then
    echo "Para todo el mundo:  $ENLACE"
    echo "Furious Cars 2:      $ENLACE/furious-cars-2.html"
  else
    echo "El enlace público se está creando; vuelve a probar en unos segundos."
  fi
else
  echo "(El enlace público de Cloudflare no está activo.)"
fi
systemctl is-active --quiet caddy 2>/dev/null && echo "Servidor web: activo ✔" || echo "Servidor web: DETENIDO ✘  →  sudo systemctl start caddy"
