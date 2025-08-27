// File: src/components/Arcade/PhaserGame.tsx
import React, { useEffect, useRef } from "react";
import Phaser from "phaser";
import LobbyScene from "@/components/Arcade/scenes/LobbyScene";
import EmulatorRoomScene from "@/components/Arcade/scenes/EmulatorRoomScene";
import HardwareRoomScene from "@/components/Arcade/scenes/HardwareRoomScene";
import FirmwareRoomScene from "@/components/Arcade/scenes/FirmwareRoomScene";
import { ArcadeEventBus } from "@/components/Arcade/events/EventBus";

// Register pixel sprites once per game boot
import { registerPixelSprites } from "./utils/SpriteFactory";


const GAME_WIDTH = 960;
const GAME_HEIGHT = 540;

export default function PhaserGame() {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const gameRef = useRef<Phaser.Game | null>(null);

    useEffect(() => {
        if (!containerRef.current || gameRef.current) return;

        const config: Phaser.Types.Core.GameConfig = {
            type: Phaser.AUTO,
            width: GAME_WIDTH,
            height: GAME_HEIGHT,
            parent: containerRef.current,
            physics: { default: "arcade", arcade: { gravity: { y: 0 }, debug: false } },
            backgroundColor: "#111827",
            scene: [LobbyScene, EmulatorRoomScene, HardwareRoomScene, FirmwareRoomScene],
        };

        const game = new Phaser.Game(config);
        gameRef.current = game;

        // Cleanup
        return () => {
            ArcadeEventBus.removeAllListeners();
            game.destroy(true);
            gameRef.current = null;
        };
    }, []);

    return <div ref={containerRef} className="w-full h-full" />;
}
