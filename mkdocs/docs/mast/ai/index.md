# AI Overview

AI in {{ab.m}} is about giving non-player entities clear, repeatable decision logic.

At a high level, AI scripts decide:

- what an agent should target
- where it should move
- what action it should take next
- what to do if the preferred action is not possible

The system is designed to be practical for mission authors:

- behavior is split into small labels with focused responsibilities
- data is stored in agent inventory (a simple blackboard pattern)
- decisions can be composed with selectors and sequences
- logic runs incrementally with the engine tick model


## Core AI building blocks

Most mission AI uses a combination of these pieces:

1. Route labels
	Route labels (such as spawn-related routes) are commonly used to initialize AI when objects appear.
2. Tasks
	Tasks run behavior logic over time, yielding when waiting for conditions or time.
3. Brains
	Brains provide behavior-tree style composition so you can build fallback and ordered logic.
4. Inventory blackboard
	AI labels share state through inventory keys like target, target_position, threat, cooldowns, and role-based data.


## Typical AI workflow

For most NPC or fleet behaviors, authoring follows this pattern:

1. Initialize context
	Collect local data (lead ship, nearby entities, zones, constraints).
2. Choose intent
	Decide what to do next (chase, defend, retreat, idle).
3. Compute output
	Produce movement/action outputs (target, throttle, destination, action flags).
4. Execute command
	Apply movement/combat commands to controlled entities.
5. Repeat each tick
	Re-evaluate based on changing world state.


## Why brains are useful

As behavior gets more complex, plain single-label logic becomes hard to maintain.
Brains help by making intent explicit:

- Sequence (SEQ) for required ordered steps
- Selector (SEL) for fallback options
- Reusable leaf labels with metadata defaults and per-node overrides

This keeps AI easier to read, debug, and extend over time.


## Design goals for mission AI

Good mission AI is usually:

- understandable: each label does one job
- resilient: has fallback behavior when data is missing
- data-driven: tunables come from metadata and node data
- inspectable: active behavior and blackboard values can be observed


## Next step

For the full behavior-tree tutorial and concrete examples, see the brains guide:

- [Brains Tutorial](brains.md)
