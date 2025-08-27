// File: src/components/Arcade/scenes/TestsBossRoomScene.ts
import Phaser from "phaser";
import BaseRoom from "@/components/Arcade/scenes/BaseRoom";
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";
import { useArcadeStore } from "@/components/Arcade/utils/arcadeStore";


export default class TestBossRoomScene extends BaseRoom {
    constructor() { super("TestBossRoomScene"); }


    create() {
        this.createRoom({ w: 1600, h: 900 });
        this.add.text(24, 16, "Tests Boss Room — trigger BVT and stream metrics", { fontSize: "14px", color: "#fff" }).setScrollFactor(0);


        const bossDoor = this.physics.add.staticSprite(500, 350, "terminal_px");
        this.add.text(450, 380, "Press E to start BVT", { fontSize: "12px", color: "#93c5fd" });


        const keyE = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.E);


        this.physics.add.overlap(this.player, bossDoor, () => {
            if (Phaser.Input.Keyboard.JustDown(keyE)) {
                ArcadeEventBus.emit("ui:toast", { message: "Starting BVT..." });
                ArcadeEventBus.emit("tests:bvt:start", {} as any);
            }
        });


        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }
}