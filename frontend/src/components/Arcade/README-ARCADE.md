// File: README-ARCADE.md
# UHT Arcade(Phaser Layer)

## What this is
A lightweight Phaser mini - world embedded in the UHT frontend. Move a bot through rooms:
- ** Emulator Room **: build controller profiles; emits MQTT commands.
- ** Hardware Lab **: device discovery & selection via hardwareService.
- ** Firmware Bay **: flash firmware via firmwareService.

## Controls
    - Move: Arrows or WASD
        - Interact: E
            - Minimap: (future)

## How to add to your app
1. 'npm i phaser mitt'
2. Copy the 'src/components/Arcade' folder, 'src/pages/ArcadePage.tsx', and wire '/arcade' route in 'AppRoutes.tsx'.
3. Ensure these services exist and are exported:
- 'mqttService.publish(topic, payload)'
    - 'hardwareService.discoverDevices()' -> Promise < Device[] >
        - 'hardwareService.selectDevice(deviceId)'
        - 'firmwareService.flashFirmware(deviceId, firmwareId)' -> Promise < boolean >
            - 'notificationService.toast(message)'
4. Navigate to '/arcade' using an <a href="/arcade">link</a> anywhere in your UI.

## Next steps
    - Replace placeholder sprites with real pixel art.
- Add inventory UI panel(React) synchronized with game state.
- Boss door to ** Tests ** room: trigger BVT sequence and show real - time metrics.
- Add quest log tied to backend job queue.