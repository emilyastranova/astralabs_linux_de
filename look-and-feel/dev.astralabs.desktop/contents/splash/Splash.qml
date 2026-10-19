/*
    AstraLabs splash screen.

    The dot field ignites from the centre of the screen, the mark flickers on like a tube,
    the wordmark strobes on, then the registration marks set. It ends on the same picture
    as the AstraLabs wallpaper (same grid, same lockup size), so the desktop takes over
    without a jump.

    SPDX-License-Identifier: AGPL-3.0-only
*/

import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: root
    color: "#0a0909"

    property int stage

    // Animations off in System Settings: show the finished frame
    readonly property bool still: Kirigami.Units.longDuration <= 1

    // Same lockup size as the wallpaper renderer
    readonly property real lockupWidth: Math.round(Math.min(width * 0.3, height * 0.42))
    readonly property real lockupHeight: lockupWidth * 105 / 904.68

    // Ignition ring, 0 → 1. Ease in-out cubic: the slow start shows the ring being born at the centre.
    property real fieldProgress: 0
    NumberAnimation on fieldProgress {
        id: ignite
        running: false
        from: 0; to: 1
        duration: 1300
        easing.type: Easing.InOutCubic
    }

    /* ---------- dot field, on the GPU ----------
       A fragment shader draws every dot each frame, so the ring moves at the display's full
       refresh rate. Source: shaders/field.frag, compiled by tools/build_shaders.sh. */
    ShaderEffect {
        id: fieldGpu
        anchors.fill: parent
        fragmentShader: "shaders/field.frag.qsb"
        property vector2d res: Qt.vector2d(width, height)
        property real progress: root.fieldProgress
        property real pitch: 16
        property real band: 22
        property real still: root.still ? 1 : 0
    }

    /* ---------- dot field, CPU fallback ----------
       Only used if the shader can't load. Draws the same picture with JavaScript, repainting
       just the band the ring has moved through each frame. */
    Canvas {
        id: field
        anchors.fill: parent
        // software rendering can't run shaders at all, so fall back there too
        visible: fieldGpu.status === ShaderEffect.Error || fieldGpu.GraphicsInfo.api === GraphicsInfo.Software
        renderStrategy: Canvas.Cooperative

        readonly property int pitch: 16
        readonly property real progress: root.fieldProgress
        property real lastR: -1
        property bool primed: false

        function reach() {
            const cx = width / 2, cy = height / 2;
            return Math.hypot(cx, cy);
        }
        // resting brightness: matches the wallpaper (0.07 + 0.11 toward the centre)
        function rest(d, max) {
            return 0.07 + Math.max(0, 1 - d / max) * 0.11;
        }

        // The splash window can start at 0×0; prime the grid once it has a real size
        onWidthChanged: { primed = false; lastR = -1; requestPaint(); }
        onHeightChanged: { primed = false; lastR = -1; requestPaint(); }

        onVisibleChanged: { primed = false; lastR = -1; requestPaint(); }

        onPaint: {
            if (!visible || width <= 0 || height <= 0) return;
            const ctx = getContext("2d");
            const cx = width / 2, cy = height / 2, max = reach();
            if (!primed) {
                ctx.fillStyle = "#0a0909";
                ctx.fillRect(0, 0, width, height);
                for (let gx = 8; gx < width; gx += pitch)
                    for (let gy = 8; gy < height; gy += pitch) {
                        const d = Math.hypot(gx - cx, gy - cy);
                        ctx.fillStyle = root.still ? Qt.rgba(237 / 255, 230 / 255, 225 / 255, rest(d, max))
                                                   : "rgba(237,230,225,0.05)";
                        ctx.fillRect(gx - 1, gy - 1, 2, 2);
                    }
                primed = true;
                if (root.still) return;
            }
            // Only redraw the band the ring has moved through since the last frame
            const R = max * progress, band = 22, lo = Math.max(0, lastR - band - 2), hi = R + band;
            for (let gx = 8; gx < width; gx += pitch)
                for (let gy = 8; gy < height; gy += pitch) {
                    const d = Math.hypot(gx - cx, gy - cy);
                    if (d < lo || d > hi) continue;
                    ctx.fillStyle = "#0a0909";
                    ctx.fillRect(gx - 1.5, gy - 1.5, 3, 3);
                    if (d > R) {
                        ctx.fillStyle = "rgba(237,230,225,0.05)";
                    } else {
                        const ring = Math.max(0, 1 - Math.abs(d - R) / band);
                        ctx.fillStyle = ring > 0.05 && progress < 1
                            ? Qt.rgba(182 / 255, 1, 46 / 255, 0.3 + ring * 0.7)
                            : Qt.rgba(237 / 255, 230 / 255, 225 / 255, rest(d, max));
                    }
                    ctx.fillRect(gx - 1, gy - 1, 2, 2);
                }
            lastR = R;
        }

        onProgressChanged: if (visible) requestPaint()
    }

    /* ---------- lockup ---------- */
    Item {
        id: lockup
        anchors.centerIn: parent
        width: root.lockupWidth
        height: root.lockupHeight

        Image {
            id: mark
            anchors.fill: parent
            source: "images/lockup-mark.svg"
            sourceSize.width: width
            sourceSize.height: height
            opacity: root.still ? 1 : 0
        }
        Image {
            id: wordmark
            anchors.fill: parent
            source: "images/lockup-wordmark.svg"
            sourceSize.width: width
            sourceSize.height: height
            opacity: root.still ? 1 : 0
        }
    }

    /* ---------- registration marks (same placement as the wallpaper) ---------- */
    readonly property int regInset: 8 + 16 * Math.max(2, Math.round(Math.min(width, height) / 360))
    readonly property int regArm: Math.max(12, Math.round(Math.min(width, height) * 0.014))

    component Reg: Item {
        width: 1; height: 1
        opacity: root.still ? 1 : 0
        Rectangle { x: -root.regArm; y: 0; width: root.regArm * 2 + 1; height: 1; color: "#b6ff2e" }
        Rectangle { x: 0; y: -root.regArm; width: 1; height: root.regArm * 2 + 1; color: "#b6ff2e" }
    }
    Reg { id: regTL; x: root.regInset; y: root.regInset }
    Reg { id: regBR; x: root.width - 1 - root.regInset; y: root.height - 1 - root.regInset }

    /* ---------- sequence ----------
       Hard cuts only: PropertyAction + PauseAnimation are whole-frame steps, never eased. */
    component Strobe: SequentialAnimation {
        id: strobe
        property Item item
        PropertyAction { target: strobe.item; property: "opacity"; value: 0 }
        PauseAnimation { duration: 40 }
        PropertyAction { target: strobe.item; property: "opacity"; value: 1 }
        PauseAnimation { duration: 40 }
        PropertyAction { target: strobe.item; property: "opacity"; value: 0 }
        PauseAnimation { duration: 55 }
        PropertyAction { target: strobe.item; property: "opacity"; value: 1 }
        PauseAnimation { duration: 55 }
        PropertyAction { target: strobe.item; property: "opacity"; value: 0.35 }
        PauseAnimation { duration: 55 }
        PropertyAction { target: strobe.item; property: "opacity"; value: 1 }
    }

    SequentialAnimation {
        id: boot
        running: false

        PauseAnimation { duration: 450 }                 // the unlit grid holds first
        ScriptAction { script: ignite.start() }
        PauseAnimation { duration: 1050 }

        // Mark: fluorescent tube, two false starts then a hold
        SequentialAnimation {
            PropertyAction { target: mark; property: "opacity"; value: 0.85 }
            PauseAnimation { duration: 60 }
            PropertyAction { target: mark; property: "opacity"; value: 0 }
            PauseAnimation { duration: 170 }
            PropertyAction { target: mark; property: "opacity"; value: 0.5 }
            PauseAnimation { duration: 30 }
            PropertyAction { target: mark; property: "opacity"; value: 0.1 }
            PauseAnimation { duration: 120 }
            PropertyAction { target: mark; property: "opacity"; value: 1 }
            PauseAnimation { duration: 30 }
            PropertyAction { target: mark; property: "opacity"; value: 0.35 }
            PauseAnimation { duration: 40 }
            PropertyAction { target: mark; property: "opacity"; value: 1 }
        }
        PauseAnimation { duration: 160 }
        Strobe { item: wordmark }
        PauseAnimation { duration: 180 }
        ParallelAnimation {
            Strobe { item: regTL }
            SequentialAnimation { PauseAnimation { duration: 110 } Strobe { item: regBR } }
        }
    }

    Component.onCompleted: {
        field.requestPaint();
        if (!still) boot.start();
    }
}
