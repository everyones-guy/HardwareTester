// File: src/components/Arcade/scenes/BaseRoom.ts
import Phaser from "phaser";
import { makePlayer } from "../utils/Sprites";

export default class BaseRoom extends Phaser.Scene {
    cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
    player!: Phaser.Types.Physics.Arcade.SpriteWithDynamicBody;

    createRoom(bounds: { w: number; h: number }) {
        this.cursors = this.input.keyboard.createCursorKeys();
        this.player = makePlayer(this, bounds.w / 2, bounds.h - 40);
        this.cameras.main.setBackgroundColor("#0B1220");
        this.physics.world.setBounds(0, 0, bounds.w, bounds.h);
        this.player.body.setMaxSpeed(200);
    }

    handleMovement() {
        const speed = 140;
        const body = this.player.body as Phaser.Physics.Arcade.Body;
        body.setVelocity(0);

        if (this.cursors.left?.isDown) body.setVelocityX(-speed);
        else if (this.cursors.right?.isDown) body.setVelocityX(speed);

        if (this.cursors.up?.isDown) body.setVelocityY(-speed);
        else if (this.cursors.down?.isDown) body.setVelocityY(speed);
    }

    update() {
        this.handleMovement();
    }
}