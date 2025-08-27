// File: src/components/Arcade/PhaserGame.tsx
import React, { useEffect, useRef } from "react";
import Phaser from "phaser";
import LobbyScene from "./scenes/LobbyScene";
import EmulatorRoomScene from "./scenes/EmulatorRoomScene";
import HardwareRoomScene from "./scenes/HardwareRoomScene";
import FirmwareRoomScene from "./scenes/FirmwareRoomScene";
import { ArcadeEventBus } from "./events/EventBus";

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
