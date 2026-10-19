// AstraLabs splash: the dot field, drawn on the GPU.
// Same picture as the Canvas fallback in Splash.qml: a 16px grid of 2px dots, unlit until the
// ignition ring passes, acid on the ring, then the resting grey (brighter toward the centre)
// that matches the wallpaper. Compile with tools/build_shaders.sh.
#version 440

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 res;        // item size in logical pixels
    float progress;  // ignition ring, 0 to 1
    float pitch;     // grid pitch (16)
    float band;      // ring half-width (22)
    float still;     // 1 when animations are off: draw the finished field
};

const vec3 VOID = vec3(10.0, 9.0, 9.0) / 255.0;
const vec3 BONE = vec3(237.0, 230.0, 225.0) / 255.0;
const vec3 ACID = vec3(182.0, 255.0, 46.0) / 255.0;

void main() {
    vec2 p = qt_TexCoord0 * res;
    // nearest grid point; the grid starts 8px in, like the wallpaper
    vec2 g = 8.0 + floor((p - 8.0) / pitch + 0.5) * pitch;
    vec2 off = abs(p - g);
    bool onDot = off.x < 1.0 && off.y < 1.0 && g.x >= 8.0 && g.y >= 8.0 && g.x < res.x && g.y < res.y;

    vec3 col = VOID;
    if (onDot) {
        vec2 c = res * 0.5;
        float reach = length(c);
        float d = distance(g, c);
        float rest = 0.07 + max(0.0, 1.0 - d / reach) * 0.11;
        float R = reach * progress;
        vec3 dotCol = BONE;
        float a;
        if (still > 0.5) {
            a = rest;
        } else if (d > R) {
            a = 0.05;                                   // unlit
        } else {
            float ring = max(0.0, 1.0 - abs(d - R) / band);
            if (ring > 0.05 && progress < 1.0) {
                dotCol = ACID;
                a = 0.3 + ring * 0.7;
            } else {
                a = rest;
            }
        }
        col = mix(VOID, dotCol, a);
    }
    fragColor = vec4(col, 1.0) * qt_Opacity;
}
