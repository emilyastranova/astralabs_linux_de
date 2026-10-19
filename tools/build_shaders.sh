#!/usr/bin/env bash
# Compile the splash shader to Qt's .qsb format (SPIR-V plus GLSL, HLSL and MSL variants).
# Needs qsb from qt6-qtshadertools. The compiled file is committed, so installing doesn't need it.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QSB="$(command -v qsb || echo /usr/lib64/qt6/bin/qsb)"
DIR="$HERE/look-and-feel/dev.astralabs.desktop/contents/splash/shaders"
"$QSB" --glsl "100 es,120,150" --hlsl 50 --msl 12 -o "$DIR/field.frag.qsb" "$DIR/field.frag"
echo "built $DIR/field.frag.qsb"
