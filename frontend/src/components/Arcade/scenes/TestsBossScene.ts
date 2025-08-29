// File: src/components/Arcade/scenes/TestsBossScene.ts
import Phaser from "phaser";
import BaseRoom from "./BaseRoom";
import { ArcadeEventBus } from "../events/EventBus";

export default class TestsBossScene extends BaseRoom {
    constructor() { super("TestsBossScene"); }

    create() {
        this.createRoom({ w: 1800, h: 1000 });
        this.add.text(24, 16, "Tests Boss Room — Trigger BVT Flow", { fontSize: "14px", color: "#fff" }).setScrollFactor(0);

        const bossDoor = this.physics.add.staticSprite(600, 400, "door");
        this.add.text(560, 430, "Press E to run BVT", { fontSize: "12px", color: "#f472b6" });

        const keyE = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);

        this.physics.add.overlap(this.player, bossDoor, () => {
            if (Phaser.Input.Keyboard.JustDown(keyE)) {
                ArcadeEventBus.emit("ui:toast", { message: "BVT Flow Initiated" });
                ArcadeEventBus.emit("mqtt:send", { topic: "uht/tests/runBVT", payload: JSON.stringify({ profile: "default" }) });
            }
        });

        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }
}