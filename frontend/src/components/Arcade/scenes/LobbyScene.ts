// File: src/components/Arcade/scenes/LobbyScene.ts
import Phaser from "phaser";
import BaseRoom from "@/components/Arcade/scenes/BaseRoom";
import { loadCommonAssets } from "@/components/Arcade/utils/Sprites";
import TestsBossRoomScene from "@/components/Arcade/scenes/TestBossRoomScene";
import { registerPixelSprites } from "@/components/Arcade/utils/SpriteFactory";

export default class LobbyScene extends BaseRoom {
    constructor() { super("LobbyScene"); }

    preload() {
        loadCommonAssets(this);
        registerPixelSprites(this);
    }

    create() {
        this.createRoom({ w: 2000, h: 1100 });

        const title = this.add.text(24, 16, "UHT Arcade Lobby", { fontSize: "16px", color: "#fff" });
        title.setScrollFactor(0);

        // Doors to rooms
        const doors = [
            { x: 200, y: 300, label: "Emulator Room", target: "EmulatorRoomScene" },
            { x: 500, y: 300, label: "Hardware Lab", target: "HardwareRoomScene" },
            { x: 800, y: 300, label: "Firmware Bay", target: "FirmwareRoomScene" },
        ];

        // Start up one test
        doors.push({ x: 1100, y: 300, label: "Tests Boss Room", target: "TestBossRoomScene" });

        doors.forEach(d => {
            const door = this.physics.add.staticSprite(d.x, d.y, "door");
            const text = this.add.text(d.x - 50, d.y + 24, d.label, { fontSize: "12px", color: "#cbd5e1" });
            // Overlap to change scenes
            this.physics.add.overlap(this.player, door, () => {
                this.scene.start(d.target);
            });
        });

        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
    }
}