// File: src/components/Arcade/utils/Sprites.ts
import Phaser from "phaser";
export function loadCommonAssets(scene: Phaser.Scene) {
    // Pixel-art robot + kids (peripherals)
    scene.load.image("bigBot", "https://dummyimage.com/32x32/22d3ee/000000&text=B");
    scene.load.image("miniBot", "https://dummyimage.com/16x16/fcd34d/000000&text=P");
    scene.load.image("door", "https://dummyimage.com/24x32/93c5fd/000000&text>D");
    scene.load.image("terminal", "https://dummyimage.com/24x16/34d399/000000&text>T");
    scene.load.image("crate", "https://dummyimage.com/16x16/fbbf24/000000&text>C");
    scene.load.image("chip", "https://dummyimage.com/12x12/a78bfa/000000&text>F");
}

export function makePlayer(scene: Phaser.Scene, x: number, y: number) {
    const bot = scene.physics.add.sprite(x, y, "bigBot");
    bot.setCollideWorldBounds(true);
    return bot;
}

export function spawnPeripheral(scene: Phaser.Scene, x: number, y: number) {
    const kid = scene.physics.add.sprite(x, y, "miniBot");
    return kid;
}