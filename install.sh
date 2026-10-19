#!/usr/bin/env bash
# Install the AstraLabs theme for KDE Plasma 6 (and the GTK apps that run inside it).
# Everything goes into your home directory; nothing needs root.
#
#   ./install.sh            install and apply
#   ./install.sh --no-apply install only, then pick pieces in System Settings
#
# Your current settings are backed up first. ./uninstall.sh restores them.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="$DATA/astralabs-theme"
APPLY=1
[[ "${1:-}" == "--no-apply" ]] && APPLY=0

say() { printf '  %s\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "Missing $1; is this a Plasma 6 session?" >&2; exit 1; }; }
need kwriteconfig6; need kreadconfig6

echo "AstraLabs theme"

# ---------- back up what we are about to change ----------
# Only back up settings from before AstraLabs. On a reinstall, keep the original backup
# so ./uninstall.sh still returns to the theme you had before.
if [[ -d "$STATE/last-backup" && "$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)" == AstraLabs ]]; then
  say "keeping the original backup at $(readlink -f "$STATE/last-backup")"
else
  BACKUP="$STATE/backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BACKUP"
  for f in kdeglobals kwinrc plasmarc ksplashrc kscreenlockerrc konsolerc kcminputrc; do
    [[ -f "$CONF/$f" ]] && cp -p "$CONF/$f" "$BACKUP/"
  done
  [[ -f "$CONF/gtk-4.0/gtk.css" ]] && cp -p "$CONF/gtk-4.0/gtk.css" "$BACKUP/gtk4-gtk.css"
  # the desktop wallpaper lives in the Plasma containment config; remember it so uninstall can put it back
  kreadconfig6 --file kdeglobals --group General --key ColorScheme > "$BACKUP/colorscheme" || true
  grep -m1 -A1 '\[Wallpaper\]\[org.kde.image\]\[General\]' "$CONF/plasma-org.kde.plasma.desktop-appletsrc" 2>/dev/null \
    | sed -n 's/^Image=//p' > "$BACKUP/wallpaper" || true
  ln -sfn "$BACKUP" "$STATE/last-backup"
  say "backed up current settings to $BACKUP"
fi

# ---------- install files ----------
mkdir -p "$DATA/color-schemes" "$DATA/konsole" "$DATA/fonts/AstraLabs" "$DATA/wallpapers" "$DATA/plasma/look-and-feel" "$CONF/gtk-4.0"
cp "$HERE/color-schemes/AstraLabs.colors" "$DATA/color-schemes/"
cp "$HERE/konsole/AstraLabs.colorscheme" "$HERE/konsole/AstraLabs.profile" "$DATA/konsole/"
cp "$HERE"/fonts/*.ttf "$HERE/fonts/OFL.txt" "$DATA/fonts/AstraLabs/"
for w in AstraLabs AstraLabs-Field; do
  rm -rf "$DATA/wallpapers/$w"; cp -r "$HERE/wallpapers/$w" "$DATA/wallpapers/"
done
rm -rf "$DATA/plasma/look-and-feel/dev.astralabs.desktop"
cp -r "$HERE/look-and-feel/dev.astralabs.desktop" "$DATA/plasma/look-and-feel/"
cp "$HERE/gtk/astralabs-libadwaita.css" "$CONF/gtk-4.0/"
# fastfetch summary with the AstraLabs logo
mkdir -p "$STATE/fastfetch" "$CONF/fastfetch" "$HOME/.local/bin"
cp "$HERE/fastfetch/astralabs-logo.txt" "$HERE/fastfetch/astralabs-terminal.png" "$STATE/fastfetch/"
cp "$HERE/fastfetch/astralabs.jsonc" "$CONF/fastfetch/"
install -m 755 "$HERE/fastfetch/astralabs-fetch" "$HOME/.local/bin/astralabs-fetch"
fc-cache -f "$DATA/fonts/AstraLabs" >/dev/null 2>&1 || true
say "installed colour scheme, Konsole profile, Martian Mono, wallpapers, global theme, splash and astralabs-fetch"

[[ $APPLY == 0 ]] && { echo "Done. Apply pieces from System Settings, or run ./install.sh without --no-apply."; exit 0; }

# ---------- apply ----------
plasma-apply-colorscheme AstraLabs >/dev/null && say "colour scheme: AstraLabs (Qt, KDE, Breeze GTK, titlebars)"

# libadwaita ignores GTK themes; import our colours from gtk.css.
# kde-gtk-config rewrites gtk.css when the colour scheme changes, so add the import after applying it.
GTK4="$CONF/gtk-4.0/gtk.css"
touch "$GTK4"
grep -q "astralabs-libadwaita.css" "$GTK4" || printf "@import 'astralabs-libadwaita.css';\n" >> "$GTK4"
say "libadwaita apps: AstraLabs colours (restart open GTK 4 apps)"

plasma-apply-wallpaperimage "$DATA/wallpapers/AstraLabs" >/dev/null && say "desktop wallpaper: AstraLabs"

kwriteconfig6 --file kscreenlockerrc --group Greeter --key WallpaperPlugin org.kde.image
kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image "file://$DATA/wallpapers/AstraLabs"
kwriteconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key PreviewImage "file://$DATA/wallpapers/AstraLabs"
say "lock screen wallpaper: AstraLabs"

kwriteconfig6 --file ksplashrc --group KSplash --key Engine KSplashQML
kwriteconfig6 --file ksplashrc --group KSplash --key Theme dev.astralabs.desktop
say "splash screen: AstraLabs (next login)"

kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile AstraLabs.profile
say "Konsole default profile: AstraLabs (new windows)"

# Fedora's ~/.bashrc loads ~/.bashrc.d/*; show the summary in new terminals
if command -v fastfetch >/dev/null; then
  mkdir -p "$HOME/.bashrc.d"
  cp "$HERE/fastfetch/astralabs-fetch.bashrc" "$HOME/.bashrc.d/astralabs-fetch.sh"
  say "new terminals: AstraLabs system summary (remove ~/.bashrc.d/astralabs-fetch.sh to turn off)"
else
  say "fastfetch not installed; skipping the terminal summary (sudo dnf install fastfetch)"
fi

echo "Done. Preview the splash any time with: ksplashqml --test --window dev.astralabs.desktop"
