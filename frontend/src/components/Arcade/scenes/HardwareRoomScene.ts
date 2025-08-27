// File: src/components/Arcade/scenes/HardwareRoomScene.ts
import Phaser from "phaser";
import BaseRoom from "@/components/Arcade/scenes/BaseRoom";
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";

export default class HardwareRoomScene extends BaseRoom {
    constructor() { super("HardwareRoomScene"); }

    create() {
        this.createRoom({ w: 1600, h: 900 });
        this.add.text(24, 16, "Hardware Lab — discover & map peripherals", { fontSize: "14px", color: "#fff" }).setScrollFactor(0);

        const discoveryCrate = this.physics.add.staticSprite(400, 400, "crate");
        this.add.text(360, 430, "Press E to discover devices", { fontSize: "12px", color: "#eab308" });

        const keyE = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);

        this.physics.add.overlap(this.player, discoveryCrate, () => {
            if (Phaser.Input.Keyboard.JustDown(keyE)) {
                ArcadeEventBus.emit("hardware:discover");
            }
        });

        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);

        for (let i = 0; i < 5; i++) {
            const kid = this.physics.add.sprite(600 + i*40, 420, "minibot");
            this.physics.add.overlap(this.player, kid, () => {
            this.events.emit("arcade:addItem", { name: "Peripheral Bot" });
            kid.destroy();
            });
         }
    }
}