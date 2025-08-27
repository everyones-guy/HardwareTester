// File: src/components/Arcade/scenes/FirmwareRoomScene.ts
import Phaser from "phaser";
import BaseRoom from "@/components/Arcade/scenes/BaseRoom";
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";

export default class FirmwareRoomScene extends BaseRoom {
    constructor() { super("FirmwareRoomScene"); }

    create() {
        this.createRoom({ w: 1600, h: 900 });
        this.add.text(24, 16, "Firmware Bay — select & flash", { fontSize: "14px", color: "#fff" }).setScrollFactor(0);

        const chip = this.physics.add.staticSprite(500, 300, "chip");
        this.add.text(470, 330, "Press E to flash", { fontSize: "12px", color: "#a78bfa" });

        const keyE = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);

        this.physics.add.overlap(this.player, chip, () => {
            if (Phaser.Input.Keyboard.JustDown(keyE)) {
                ArcadeEventBus.emit("firmware:flash", { deviceId: "demo-001", firmwareId: "fw-latest" });
            }
        });

        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }
}