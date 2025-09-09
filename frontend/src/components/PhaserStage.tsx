import { useEffect, useRef } from "react";
import Phaser from "phaser";
import ControllerScene from "@/phaser/ControllerScene";

const PhaserStage = () => {
    const gameRef = useRef<Phaser.Game | null>(null);
    const mountRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (gameRef.current) return;

        const config: Phaser.Types.Core.GameConfig = {
            type: Phaser.AUTO,
            width: 1280,
            height: 720,
            parent: mountRef.current || undefined,
            backgroundColor: "#0b1220",
            physics: { default: "arcade", arcade: { debug: false } },
            scene: [ControllerScene],
        };

        const game = new Phaser.Game(config);
        gameRef.current = game;

        // Expose helpers so React or devtools can add bots from elsewhere:
        (window as any).phaserAddPeripheral = () => {
            const scene = game.scene.keys["ControllerScene"] as ControllerScene;
            scene?.addPeripheral();
        };

        return () => {
            (window as any).phaserAddPeripheral = undefined;
            game.destroy(true);
            gameRef.current = null;
        };
    }, []);

    return (
        <div style={{ width: "100%", display: "flex", justifyContent: "center" }}>
            <div ref={mountRef} />
        </div>
    );
};

export default PhaserStage;
