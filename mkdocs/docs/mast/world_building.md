# World Building in MAST

MAST gives you a few practical ways to build the world around a mission:

- Spawn and shape objects with terrain helpers and prefab labels.
- Add custom mission systems through roles, inventory values, and data-set values.
- Drive behavior with routes such as spawn, damage, comms, and signal handlers.
- Extend player and station loadouts with custom equipment, like torpedoes.

The general pattern is to define reusable prefab or helper labels, then wire them into spawn and event routes so the mission can set itself up dynamically.

If you want one concrete example, see [Torpedoes](world_building/torpedoes.md) for how to define custom weapons, give them to ships, and add station production.
