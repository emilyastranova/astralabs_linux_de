#!/usr/bin/env bash
# Remove the AstraLabs theme and put back the settings install.sh backed up.
set -euo pipefail

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/astralabs-theme"
BACKUP="$STATE/last-backup"

say() { printf '  %s\n' "$*"; }
echo "AstraLabs theme: uninstall"

if [[ -d "$BACKUP" ]]; then
  prev_scheme="$(cat "$BACKUP/colorscheme" 2>/dev/null || true)"
  prev_wall="$(cat "$BACKUP/wallpaper" 2>/dev/null || true)"

  # colour scheme first: it regenerates the GTK colours
  if [[ -n "$prev_scheme" && "$prev_scheme" != AstraLabs ]]; then
    plasma-apply-colorscheme "$prev_scheme" >/dev/null && say "colour scheme: $prev_scheme"
  fi
  for f in ksplashrc kscreenlockerrc konsolerc; do
    [[ -f "$BACKUP/$f" ]] && cp -p "$BACKUP/$f" "$CONF/$f" && say "restored $f"
  done
  if [[ -n "$prev_wall" ]]; then
    plasma-apply-wallpaperimage "${prev_wall#file://}" >/dev/null && say "desktop wallpaper: ${prev_wall#file://}"
  fi
else
  say "no backup found; leaving settings as they are"
fi

# drop the libadwaita import and remove installed files
GTK4="$CONF/gtk-4.0/gtk.css"
[[ -f "$GTK4" ]] && sed -i "/astralabs-libadwaita.css/d" "$GTK4"
rm -f "$CONF/gtk-4.0/astralabs-libadwaita.css"
rm -f "$DATA/color-schemes/AstraLabs.colors" "$DATA/konsole/AstraLabs.colorscheme" "$DATA/konsole/AstraLabs.profile"
rm -f "$HOME/.bashrc.d/astralabs-fetch.sh" "$HOME/.local/bin/astralabs-fetch" "$CONF/fastfetch/astralabs.jsonc"
rm -rf "$STATE/fastfetch"
rm -rf "$DATA/wallpapers/AstraLabs" "$DATA/wallpapers/AstraLabs-Field" "$DATA/plasma/look-and-feel/dev.astralabs.desktop" "$DATA/fonts/AstraLabs"
fc-cache -f >/dev/null 2>&1 || true
say "removed AstraLabs files (backups kept in $STATE)"
echo "Done."
