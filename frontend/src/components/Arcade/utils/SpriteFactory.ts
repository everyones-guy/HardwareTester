// File: src/components/Arcade/utils/SpriteFactory.ts
import Phaser from "phaser";


export function registerPixelSprites(scene: Phaser.Scene) {
    const g = scene.add.graphics();

    // Big Bot (32x32)
    g.clear();
    g.fillStyle(0x3b82f6, 1);
    g.fillRect(0, 0, 32, 32);
    g.fillStyle(0x1f2937, 1);
    g.fillRect(8, 6, 16, 6); // visor
    g.fillRect(6, 20, 20, 6); // belt
    g.generateTexture("bigbot", 32, 32);

    // Mini Bot (16x16)
    g.clear();
    g.fillStyle(0xf59e0b, 1);
    g.fillRect(0, 0, 16, 16);
    g.fillStyle(0x1f2937, 1);
    g.fillRect(4, 3, 8, 3); // visor
    g.fillRect(3, 10, 10, 3); // belt
    g.generateTexture("minibot", 16, 16);

    // Terminals
    g.clear();
    g.fillStyle(0x10b981, 1);
    g.fillRect(0, 0, 24, 16);
    g.generateTexture("terminal_px", 24, 16);

    // Crate
    g.clear();
    g.fillStyle(0xfbbf24, 1);
    g.fillRect(0, 0, 16, 16);
    g.generateTexture("crate_px", 16, 16);

    // Chip
    g.clear();
    g.fillStyle(0xa78bfa, 1);
    g.fillRect(0, 0, 12, 12);
    g.generateTexture("chip_px", 12, 12);

    g.destroy();
}