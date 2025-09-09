import Phaser from "phaser";

type BotType = "controller" | "peripheral";

interface Bot extends Phaser.GameObjects.Container {
    botType: BotType;
    speed: number;
}

export default class ControllerScene extends Phaser.Scene {
    controller!: Bot;
    cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
    wasd!: Record<string, Phaser.Input.Keyboard.Key>;
    followers: Bot[] = [];
    history: Phaser.Math.Vector2[] = [];
    historyMax = 600;      // how many past positions to keep
    followerSpacing = 18;  // trail distance between followers (history steps)
    grid?: Phaser.GameObjects.Grid;

    constructor() {
        super("ControllerScene");
    }

    preload() {
        // no assets; we draw vectors
    }

    create() {
        // optional background grid for “hardware floor”
        this.grid = this.add.grid(640, 360, 1280, 720, 40, 40, 0x0, 0, 0x3a3a3a, 0.18);
        this.grid.setVisible(true);

        this.controller = this.makeBot(640, 360, "controller");
        this.controller.speed = 220;

        // keyboard
        this.cursors = this.input.keyboard!.createCursorKeys();
        this.wasd = {
            W: this.input.keyboard!.addKey("W"),
            A: this.input.keyboard!.addKey("A"),
            S: this.input.keyboard!.addKey("S"),
            D: this.input.keyboard!.addKey("D"),
        };

        // hotkeys
        this.input.keyboard!.on("keydown-SPACE", () => this.addPeripheral());
        this.input.keyboard!.on("keydown-G", () => this.grid?.setVisible(!this.grid?.visible));

        // seed history with current position
        for (let i = 0; i < this.historyMax; i++) {
            this.history.push(new Phaser.Math.Vector2(this.controller.x, this.controller.y));
        }

        // create a couple followers to start
        for (let i = 0; i < 4; i++) this.addPeripheral();

        // gentle idle “walk” anim using y-bob + arm swing
        this.tweens.add({
            targets: this.controller.list,
            duration: 450,
            y: "+=2",
            yoyo: true,
            repeat: -1,
            ease: "sine.inOut",
        });
    }

    update(time: number, delta: number) {
        const dt = delta / 1000;
        const move = new Phaser.Math.Vector2(0, 0);

        if (this.cursors.left?.isDown || this.wasd.A.isDown) move.x -= 1;
        if (this.cursors.right?.isDown || this.wasd.D.isDown) move.x += 1;
        if (this.cursors.up?.isDown || this.wasd.W.isDown) move.y -= 1;
        if (this.cursors.down?.isDown || this.wasd.S.isDown) move.y += 1;

        if (move.lengthSq() > 0) {
            move.normalize().scale(this.controller.speed * dt);
            this.controller.x = Phaser.Math.Clamp(this.controller.x + move.x, 40, 1240);
            this.controller.y = Phaser.Math.Clamp(this.controller.y + move.y, 40, 680);
        }

        // push current position into history front
        this.history.unshift(new Phaser.Math.Vector2(this.controller.x, this.controller.y));
        if (this.history.length > this.historyMax) this.history.pop();

        // followers target an older history index for “snake” trail
        this.followers.forEach((bot, i) => {
            const targetIndex = Math.min((i + 1) * this.followerSpacing, this.history.length - 1);
            const target = this.history[targetIndex];
            const to = new Phaser.Math.Vector2(target.x - bot.x, target.y - bot.y);
            const dist = to.length();

            if (dist > 0.01) {
                const step = Math.min(bot.speed * dt, dist);
                to.normalize().scale(step);
                bot.x += to.x;
                bot.y += to.y;
            }
        });
    }

    /** Public API (usable from React): window.phaserAddPeripheral?.() */
    addPeripheral = () => {
        const idx = this.followers.length;
        const bot = this.makeBot(
            this.controller.x + Phaser.Math.Between(-35, 35),
            this.controller.y + Phaser.Math.Between(-35, 35),
            "peripheral",
            idx
        );
        bot.speed = 240; // slightly faster so it can catch up
        this.followers.push(bot);

        // little “link” flash
        const line = this.add.line(0, 0, this.controller.x, this.controller.y, bot.x, bot.y, 0x00c2ff, 0.6)
            .setLineWidth(2, 2);
        this.tweens.add({
            targets: line,
            alpha: 0,
            duration: 500,
            onComplete: () => line.destroy(),
        });
    };

    private makeBot(x: number, y: number, type: BotType, labelIndex?: number): Bot {
        const bodyColor = type === "controller" ? 0x2aa198 : 0x6c9bd2; // teal vs blue
        const body = this.add.roundedRectangle(0, 0, type === "controller" ? 70 : 44, type === "controller" ? 60 : 36, 10, bodyColor).setStrokeStyle(2, 0x1f2937);
        const wheelL = this.add.circle(-(body.width / 2 - 12), body.height / 2, type === "controller" ? 8 : 6, 0x1f2937);
        const wheelR = this.add.circle(+(body.width / 2 - 12), body.height / 2, type === "controller" ? 8 : 6, 0x1f2937);
        const eyeL = this.add.circle(-10, -6, type === "controller" ? 5 : 4, 0xffffff);
        const eyeR = this.add.circle(10, -6, type === "controller" ? 5 : 4, 0xffffff);
        const pupilL = this.add.circle(-10, -6, type === "controller" ? 2.5 : 2, 0x1f2937);
        const pupilR = this.add.circle(10, -6, type === "controller" ? 2.5 : 2, 0x1f2937);

        const tagText = this.add.text(0, (body.height / 2) + 14,
            type === "controller" ? "CONTROLLER" : `BOT ${labelIndex ?? ""}`,
            { fontFamily: "monospace", fontSize: type === "controller" ? "12px" : "10px", color: "#e5e7eb" }
        ).setOrigin(0.5, 0);

        const container = this.add.container(x, y, [body, wheelL, wheelR, eyeL, eyeR, pupilL, pupilR, tagText]) as Bot;
        container.botType = type;
        container.speed = 200;

        // subtle idle wiggle for peripherals
        if (type === "peripheral") {
            this.tweens.add({
                targets: container,
                rotation: { from: -0.02, to: 0.02 },
                duration: 800,
                yoyo: true,
                repeat: -1,
                ease: "sine.inOut",
            });
        }
        return container;
    }
}
