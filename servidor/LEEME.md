# Montar AugustoGames en tu PC con Ubuntu

Con estos scripts tu PC se convierte en el servidor de AugustoGames (con Furious Cars 2 y los demás juegos) y cualquiera puede jugar desde internet.

## Cómo funciona

- **Caddy** es un servidor web liviano que entrega los juegos desde tu PC.
- **Cloudflare Tunnel** crea un enlace público gratuito, tipo `https://algo.trycloudflare.com`. No hay que tocar el router, y el enlace ya viene con HTTPS.
- Todo arranca solo cada vez que enciendes el PC.

El juego se dibuja con la tarjeta gráfica de cada jugador, así que tu PC solo envía los archivos (unos 8 MB la primera vez). Aguanta bien a muchos jugadores a la vez, incluso con internet de casa.

## 1. Descargar el proyecto en tu PC

Abre una terminal (Ctrl + Alt + T) y escribe:

```bash
sudo apt install -y git
git clone -b claude/compassionate-faraday-68hhm6 https://github.com/jesusccl/miprogramagpt.git
cd miprogramagpt
```

> Si el repositorio es privado, GitHub te pedirá tu usuario y un *token* en vez de la contraseña. Lo creas en GitHub → Settings → Developer settings → Personal access tokens.

## 2. Instalar y publicar

```bash
bash servidor/instalar.sh
```

Te pedirá tu contraseña de Ubuntu. Al terminar verás algo así:

```
  En este PC:           http://localhost/
  En tu casa (wifi):    http://192.168.1.50/
  Para todo el mundo:   https://palabras-al-azar.trycloudflare.com
  Furious Cars 2:       https://palabras-al-azar.trycloudflare.com/furious-cars-2.html
```

Comparte el enlace de **"Para todo el mundo"** con tus amigos.

## Comandos útiles

| Quiero… | Comando |
|---|---|
| Ver el enlace actual | `bash servidor/enlace.sh` |
| Publicar la última versión del juego | `bash servidor/actualizar.sh` |
| Apagar el sitio | `sudo systemctl stop augusto-tunel caddy` |
| Volver a encenderlo | `sudo systemctl start caddy augusto-tunel` |
| Que no arranque solo al encender el PC | `sudo systemctl disable augusto-tunel caddy` |

## El enlace de Cloudflare cambia al reiniciar

El enlace gratuito `trycloudflare.com` es nuevo cada vez que se reinicia el PC o el servicio; el actual se ve con `bash servidor/enlace.sh`. Para tener **una dirección fija** hay dos caminos:

**A. Dominio propio con Cloudflare** (recomendado, sin tocar el router): compra un dominio barato o usa uno que ya tengas en Cloudflare y crea un túnel con nombre desde el panel *Zero Trust → Networks → Tunnels*. Cloudflare te da un comando `sudo cloudflared service install …` que dejará tu dominio apuntando a `http://localhost:80`.

**B. Dominio gratuito de DuckDNS + router**:
1. Crea un subdominio en <https://www.duckdns.org> (por ejemplo `augustogames.duckdns.org`) y apúntalo a tu IP pública.
2. En tu router, redirige los puertos **80 y 443** a la IP local de tu PC (la que muestra `enlace.sh`).
3. Ejecuta:
   ```bash
   bash servidor/instalar.sh --dominio augustogames.duckdns.org
   ```
   Caddy obtiene solo el certificado HTTPS.

> Algunas compañías de internet no permiten abrir puertos (usan *CG-NAT*). En ese caso usa el camino A.

## Solo para tu casa

```bash
bash servidor/instalar.sh --solo-local
```

Así el sitio queda disponible solo en tu red: se entra con `http://IP-de-tu-PC/` desde el celular o la tele conectados al mismo wifi.

## Problemas comunes

- **La página no carga desde el celular en casa**: revisa que estén en el mismo wifi y que el cortafuegos no bloquee (el instalador abre el puerto 80 si usas `ufw`).
- **"Cloudflare dio el enlace pero todavía no conecta"**: algunas redes bloquean el puerto 7844 de Cloudflare. Prueba en otra red o usa la opción de dominio.
- **El mando de consola no funciona en `http://`**: los navegadores solo permiten mandos en páginas `https://`. Entra por el enlace de Cloudflare o por tu dominio.
- **El juego se queda en "Cargando motor gráfico…"**: el navegador del jugador necesita internet, porque el motor 3D (three.js) se descarga desde `cdn.jsdelivr.net`.
