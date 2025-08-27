// File: src/components/Arcade/scenes/EmulatorRoomScene.ts
import Phaser from "phaser";
import BaseRoom from "@/components/Arcade/scenes/BaseRoom";
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";

export default class EmulatorRoomScene extends BaseRoom {
    constructor() { super("EmulatorRoomScene"); }

    create() {
        this.createRoom({ w: 1600, h: 900 });
        this.add.text(24, 16, "Emulator Room — assemble your virtual controller", { fontSize: "14px", color: "#fff" }).setScrollFactor(0);

        const terminal = this.physics.add.staticSprite(300, 300, "terminal");
        this.add.text(260, 330, "Press E to build controller", { fontSize: "12px", color: "#a3e635" });

        // Interaction key
        const keyE = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);

        this.physics.add.overlap(this.player, terminal, () => {
            if (Phaser.Input.Keyboard.JustDown(keyE)) {
                ArcadeEventBus.emit("ui:toast", { message: "Controller assembled in emulator" });
                ArcadeEventBus.emit("mqtt:send", { topic: "uht/emulator/build", payload: JSON.stringify({ profile: "default" }) });
            }
        });

        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);

        // Use bigbot as player sprite if present
        // In BaseRoom, after createRoom, you can swap texture:
        this.player.setTexture("bigbot");
    }
}