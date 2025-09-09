import Phaser from "phaser";
import { ArcadeEventBus, DevicesUpdatedEvent, DeviceSummary } from "@/components/Arcade/events/EventBus";

type Accent = { fill: number; stroke: number };
const ACCENTS: Record<DeviceSummary["type"], Accent> = {
    USB: { fill: 0x4b8df8, stroke: 0x1f2937 },
    WiFi: { fill: 0x22a699, stroke: 0x1f2937 },
    Bluetooth: { fill: 0x7b61ff, stroke: 0x1f2937 },
    Serial: { fill: 0xc0840a, stroke: 0x1f2937 },
    Other: { fill: 0x6c9bd2, stroke: 0x1f2937 },
};

export default class ControllerSwarmScene extends Phaser.Scene {
    controller!: Phaser.GameObjects.Container;
    followers: Phaser.GameObjects.Container[] = [];
    followerKinds: DeviceSummary["type"][] = [];

    history: Phaser.Math.Vector2[] = [];
    historyMax = 800;
    followerSpacing = 20;

    cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
    wasd!: Record<string, Phaser.Input.Keyboard.Key>;

    constructor() { super("ControllerSwarmScene"); }

    create() {
        this.add.grid(640, 360, 1280, 720, 40, 40, 0x0, 0, 0x3a3a3a, 0.18);

        this.controller = this.makeBot(640, 360, true, "CONTROLLER", { fill: 0x2aa198, stroke: 0x1f2937 });
        for (let i = 0; i < this.historyMax; i++) this.history.push(new Phaser.Math.Vector2(this.controller.x, this.controller.y));

        this.cursors = this.input.keyboard!.createCursorKeys();
        this.wasd = {
            W: this.input.keyboard!.addKey("W"),
            A: this.input.keyboard!.addKey("A"),
            S: this.input.keyboard!.addKey("S"),
            D: this.input.keyboard!.addKey("D"),
        };

        // idle controller bob
        this.tweens.add({ targets: this.controller.list, duration: 450, y: "+=2", yoyo: true, repeat: -1, ease: "sine.inOut" });

        // react -> phaser: device updates
        ArcadeEventBus.on<DevicesUpdatedEvent>("devices.updated", ({ devices }) => {
            this.syncFollowers(devices);
        });

        // also expose for devtools
        (window as any).Arcade = (window as any).Arcade || {};
        (window as any).Arcade.setPeripheralCount = (n: number) => this.setPeripheralCount(n);
        (window as any).Arcade.addPeripheral = () => this.addFollower("Other", "BOT");
    }

    update(_: number, delta: number) {
        const dt = delta / 1000;
        const move = new Phaser.Math.Vector2(0, 0);
        const speed = 220;

        if (this.cursors.left?.isDown || this.wasd.A.isDown) move.x -= 1;
        if (this.cursors.right?.isDown || this.wasd.D.isDown) move.x += 1;
        if (this.cursors.up?.isDown || this.wasd.W.isDown) move.y -= 1;
        if (this.cursors.down?.isDown || this.wasd.S.isDown) move.y += 1;

        if (move.lengthSq() > 0) {
            move.normalize().scale(speed * dt);
            this.controller.x = Phaser.Math.Clamp(this.controller.x + move.x, 40, 1240);
            this.controller.y = Phaser.Math.Clamp(this.controller.y + move.y, 40, 680);
        }

        this.history.unshift(new Phaser.Math.Vector2(this.controller.x, this.controller.y));
        if (this.history.length > this.historyMax) this.history.pop();

        const followerSpeed = 240;
        for (let i = 0; i < this.followers.length; i++) {
            const bot = this.followers[i];
            const idx = Math.min((i + 1) * this.followerSpacing, this.history.length - 1);
            const target = this.history[idx];
            const dx = target.x - (bot.x as number);
            const dy = target.y - (bot.y as number);
            const dist = Math.hypot(dx, dy);
            if (dist > 0.01) {
                const step = Math.min(followerSpeed * dt, dist);
                bot.x += (dx / dist) * step;
                bot.y += (dy / dist) * step;
            }
        }
    }

    // react devices -> followers
    private syncFollowers(devs: DeviceSummary[]) {
        // grow or shrink
        while (this.followers.length < devs.length) {
            const next = devs[this.followers.length];
            this.addFollower(next.type, next.name || "BOT");
        }
        while (this.followers.length > devs.length) {
            const dead = this.followers.pop();
            dead?.destroy();
            this.followerKinds.pop();
        }

        // update labels/colors by kind
        devs.forEach((d, i) => {
            if (!this.followers[i]) return;
            const c = ACCENTS[d.type];
            this.paintFollower(this.followers[i], c, d.name || "BOT");
            this.followerKinds[i] = d.type;
        });
    }

    private setPeripheralCount(n: number) {
        const dummy: DeviceSummary[] = Array.from({ length: n }).map((_, i) => ({
            id: i, name: `BOT ${i + 1}`, type: "Other" as const, online: true,
        }));
        this.syncFollowers(dummy);
    }

    private addFollower(kind: DeviceSummary["type"], label: string) {
        const accent = ACCENTS[kind];
        const bot = this.makeBot(
            this.controller.x + Phaser.Math.Between(-35, 35),
            this.controller.y + Phaser.Math.Between(-35, 35),
            false,
            label,
            accent
        );
        // wiggle
        this.tweens.add({ targets: bot, rotation: { from: -0.02, to: 0.02 }, duration: 800, yoyo: true, repeat: -1, ease: "sine.inOut" });

        // link flash
        const line = this.add.line(0, 0, this.controller.x, this.controller.y, bot.x, bot.y, 0x00c2ff, 0.7).setLineWidth(2, 2);
        this.tweens.add({ targets: line, alpha: 0, duration: 500, onComplete: () => line.destroy() });

        this.followers.push(bot);
        this.followerKinds.push(kind);
    }

    private paintFollower(bot: Phaser.GameObjects.Container, accent: Accent, label: string) {
        // children[0] is the rounded rect body, last is text label in our build order
        const body = bot.list[0] as Phaser.GameObjects.Shape;
        body.setFillStyle(accent.fill);
        body.setStrokeStyle(2, accent.stroke);
        const text = bot.list[bot.list.length - 1] as Phaser.GameObjects.Text;
        text.setText(label);
    }

    private makeBot(x: number, y: number, isController: boolean, label: string, accent?: Accent) {
        const bodyW = isController ? 70 : 44;
        const bodyH = isController ? 60 : 36;
        const fill = accent?.fill ?? (isController ? 0x2aa198 : 0x6c9bd2);
        const stroke = accent?.stroke ?? 0x1f2937;

        const body = this.add.roundedRectangle(0, 0, bodyW, bodyH, 10, fill).setStrokeStyle(2, stroke);
        const wheelL = this.add.circle(-(bodyW / 2 - 12), bodyH / 2, isController ? 8 : 6, 0x1f2937);
        const wheelR = this.add.circle(+(bodyW / 2 - 12), bodyH / 2, isController ? 8 : 6, 0x1f2937);
        const eyeL = this.add.circle(-10, -6, isController ? 5 : 4, 0xffffff);
        const eyeR = this.add.circle(10, -6, isController ? 5 : 4, 0xffffff);
        const pupilL = this.add.circle(-10, -6, isController ? 2.5 : 2, 0x1f2937);
        const pupilR = this.add.circle(10, -6, isController ? 2.5 : 2, 0x1f2937);
        const tag = this.add.text(0, bodyH / 2 + 14, label, {
            fontFamily: "monospace", fontSize: isController ? "12px" : "10px", color: "#e5e7eb",
        }).setOrigin(0.5, 0);

        return this.add.container(x, y, [body, wheelL, wheelR, eyeL, eyeR, pupilL, pupilR, tag]);
    }
}
