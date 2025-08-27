// File: src/components/Arcade/utils/Sprites.ts
import Phaser from "phaser";

export function makePlayer(scene: Phaser.Scene, x: number, y: number) {
    const p = scene.physics.add.sprite(x, y, "player");
    p.setCollideWorldBounds(true);
    return p;
}

export function loadCommonAssets(scene: Phaser.Scene) {
    // Placeholder textures. Replace with real assets later.
    scene.load.image("player", "https://dummyimage.com/16x16/ffffff/000000&text=P");
    scene.load.image("door", "https://dummyimage.com/24x32/93c5fd/000000&text>D");
    scene.load.image("terminal", "https://dummyimage.com/24x16/34d399/000000&text>T");
    scene.load.image("crate", "https://dummyimage.com/16x16/fbbf24/000000&text>C");
    scene.load.image("chip", "https://dummyimage.com/12x12/a78bfa/000000&text>F");
    scene.load.image("perk", "https://dummyimage.com/12x12/f87171/000000&text>+");
}
