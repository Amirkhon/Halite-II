---
layout: doc_page
title: Game Rules Deep Dive
toc: false
sort_key: 1
description: Learn the details of the rules of the game to win the Halite AI Programming Challenge.
---

## Start of Game
All games are played with either 2 or 4 players. At the beginning of the game, for their first turn, all bots receive the initial game state, as well as their player ID, and have 1 minute to prepare and send back their bot name.

## Map
Maps are rectangular areas with 3:2 aspect ratio (e.g. 288 x 192 units), using 2D Cartesian, continuous, non-wrapping coordinates. Game entities can have floating-point positions.

The largest board is 384 x 256 units, the smallest is 240 x 160 units.  All distances are Euclidean (sqrt(dx^2 + dy^2)), and are between the centers of entities. If a ship goes off the map it is considered dead, since the map does not wrap.

Maps are generated with a random number of planets, distributed symmetrically across the board varying by game. Planets are perfectly circular, with a radius dependent on the map size (planets on a given map range in size, but the average size is determined by map size). The map generation algorithm aims to place more planets for 4-person games than 2-person games.

Specifically, a cluster of 4 planets is first placed in the center, with radius between one-third and one-half the square root of the shorter map side length. Thus, on the smallest competition map (240 by 160), these planets range from about 4.2 to 6.3 units radius, while on the largest, they range from 5.3 to 8 units. Other planets range from one-fourth to 1x the square root of the shorter map side length, but the minimum radius is always at least 4 units, and the maximum radius is always at least 5 units. Thus, on the smallest map, the radius of other planets ranges from 4 to 12.6 units, and on the largest, 4 to 16 units.

## Teams at Start of Game
Each player begins with three ships, arranged along the vertical axis with one unit of space between the centers of the ships, and no planets. In the four-player case, each player begins in the center of a quadrant of the map; in the two-player case, each player begins in the center of one of the halves of the map, mirrored either vertically or horizontally.

Each initial ship starts with the maximum 255 health points and 0 velocity.

## Turns
Halite II is a simultaneous turn-based game. The game proceeds until a bot wins, or until the turn limit is reached. The turn limit is calculated as 100 + sqrt(mapWidth * mapHeight).

At the beginning of each turn, all bots receive the current game state, and have a limited time (2000 milliseconds) to issue a command per ship (thrust, dock, or undock). Any bot that issues a malformed command or does not respond within the allotted time is ejected.

Turns are calculated using the following order of steps:
1.    The status of any docked ships is updated.
2.    Player commands are processed. For instance, a new thrust command will instantaneously update the ship velocity.
3.    Movement, collisions, and attacks are resolved simultaneously.
4.    Damage from combat is applied.
5.    Planet resources/ship creation is updated.

These steps may be referred to as ‘substeps’. There is no minimum time for a step, but times are rounded to four decimal places.
 
This calculation is most relevant to battles and other events that happen simultaneously. See relevant sections below for more details how these calculations impact [battles](#ship-planet-collision), [docking](#docking-and-mining), and [collision](#ship-planet-collision).

## Entities and Game Mechanics
The entities in Halite II are ships and planets. The key mechanics are movement, docking/mining, collision and combat.

### Ships
Each ship occupies a perfectly circular area with radius 0.5 units. Ships have:
* Health, ranging from 0 to 255 integral points, and starting at 255 points.
* Velocity, ranging from 0 to 7 integral units/turn in any direction. (The velocity is stored as two floating-point components, representing the x and y directions; the magnitude of the resulting velocity vector is scaled as to not exceed 7.)
* A weapon, with a reach of 5 units in all directions, dealing 64 damage/turn.

### Movement
A thrust command will set a direction and a velocity for a ship by specifying an angle in degrees (integers) and a velocity (integer ranging 0 to 7). Ships must be given a thrust command every turn to continue to move (stateless, no inertia).

Beyond basic thrust, the APIs available in the starting packages provide some additional helper methods for pathfinding.
1. obstacles_between: determines whether there are obstacles between two designated entities (ships/planets/positions).
2. nearby_entities_by_distance: a list of entities on the map with their distance to source object
3. calculate_distance_between: given two entities, calculate distance between them
4. calculate_angle_between: given two entities, return the angle (in degrees) between them
5. closest_point_to: returns a point near a given entity closest to the source entity
6. navigate: given a position, will navigate a user towards a given location using other pathfinding methods. Navigate is a stateless method, you must continue to call it each turn until you arrive at your destination, and can always choose not to call it, being able to easily change directions between turns. If avoid_obstacles is set to True (default) will avoid obstacles on the way, with up to max_corrections corrections

In order be successful at Halite II, players will need sophisticated pathfinding algorithms, but new players are encouraged to try out our navigate helper function as an easier starting point.

### Planets
Each planet occupies a perfectly circular area. Planets have:
* Radius, which determines their size
* Health, with the maximum value depending on their radius
* Unlimited resources used to create new ships
* An owner (start the game without an owner)
* A list of docked ships
* No velocity, no weapons

### Docking and Mining
To take control of a planet, a player must dock a ship to the planet. Only one team can dock on a planet at a time.

**Docking:** Once a ship moves within 4 units of a planet (ie. 4 + radius distance from center of planet), it can be commanded to dock, which will cause the ship to begin the docking process. The planet must be unoccupied or owned by the player intending to dock. The ship must also be stationary. If the ship is too far away or not stationary or the planet is occupied, the dock command does nothing. In order for a planet to be considered in the __2nd winning condition of all planets owned__ , the docking operation must complete.

If two ships from different teams both issue docking commands on an unoccupied planet during the same turn, they will battle. If they both continue to issue docking commands, they will continue to battle. During these turns, the ships are not yet docking and therefore maintain their defenses (described under docking section below) until they start to successfully dock.

Once a player starts to dock, that player is considered the owner of the planet. The owning player may continue to dock ships to the planet until the limit of ships per that planet has been reached. The maximum number of ships that can be docked to a planet is a function of the radius: larger planets have more docking spots.

It takes 5 complete turns for the ship to dock. After these 5 turns the ship is considered fully docked. During this time, a docking ship may be attacked and the ship has no defenses (i.e. if attacked, the ship is dealt damage but does not fire). A docking ship cannot be commanded.  A docked ship and an undocking ship also have no defenses (see more below).
 
**Mining:** Once docked, a ship automatically starts mining a planet, and the planet starts producing new ships. The rate of production is dependent on the number of ships docked to a planet: each docked ship contributes 6 units per turn to ship production and it takes 72 units to produce a ship. E.g. a planet with 12 ships docked would make a ship every turn, with 6 ships docked every two turns.

Newly created ships will appear within 2 units from the surface of the planet (i.e. within 2 + radius units of the center of the planet), in the unoccupied space closest to the center of the map. The ship will start with full health and zero velocity. If there is not adequate space anywhere near the planet, the ship will not spawn.

**Undocking:** A fully docked ship may be undocked from the planet, by issuing another command to ‘undock’. The ship will begin the undocking process, which takes 5 complete turns, after which the player will have full control over the ship again. An undocking ship will remain defenseless as it was while docked or docking. A ship will not move while undocking, so once undocked the ship will be in the same location it was in while docked.

### Ship-Planet Collision
Ships can do combat with planets by crashing into them (occupying locations on the perimeter of planets).

Like ships, planets also have health points. Planets start with a number of health points proportional to their radius: 255 points per unit of radius (thus, a radius 3 planet has 765 health). A ship can damage or destroy a planet by colliding with it; the planet takes 1 point of damage for each point of health the ship had. Since ships have up to 255 health, this means a planet can absorb one collision with a full-health ship per unit of radius it has. For instance, a radius 3 planet will explode if 3 full-health ships collide with it.

When a planet dies, it explodes, dealing damage to any ships or planets within a distance from the planet surface equal to the planet's radius (or within 4 units of the surface if the planet radius is less than 4). The damage scales linearly with distance from the surface, beginning at 1275 damage when adjacent to the planet and ending at 127 damage if 5 units away.

### Ship-Ship Combat & Collision
Ships automatically fight each other when they come into close distances. (5 units from the center of the ship, represented on the board by the aura around the ship) When ships come into combat, they do up to 64 units of damage per turn to each other (see below).

Ships that touch each other will both explode. I.e. if the ships are moving at a high velocity towards each other, ships will start to fight but will collide before getting to zero strength. Ship collisions do no damage to any ships or planets other than the two ships themselves. (A very rare edge case is when two ships collide with each other at the same time that they collide with a planet. In this case, they would collide with the planet and destroy each other at the same time).

If multiple enemy ships are within range simultaneously for a turn, the damage is evenly spread between all ships. (During processing, each ship accumulates damage in floating-point precision, which is then rounded down and applied at the end of each substep).  

For example, if two ships from bot A are within the range of one ship from bot B for a given turn, each ship with full strength, then each of the bot A ships will receive 32 units of damage, while bot B’s ship will receive 128 units of damage. Bot B’s attack will be split between the bot A ships, while bot B’s ship takes the full brunt of both of the attacks from bot A.

```
...A.A....
....B.....
..........
```

Once a ship fires its weapon, it may not attack again for the rest of the turn. Because ships attack immediately as soon as a ship comes into range, the direction of approach is crucial. 

Consider ships A, B, and C arranged like so, where A is owned by player 1 and B and C are owned by player 2:
```
..........
A......B.C
..........
```

Within one turn, if A moves five units to the right, on the substep where it has moved 2 units to the right, reaching firing distance of the B ship, those two ships will attack each other, dealing full damage (64 each).
```
..........
..a....b.C
..........
```
Within this turn, A will continue moving, and as it approaches ship C, then ship C will fire, dealing an additional 64 damage. A will not fire again because it can only fire once per turn. On the next turn, if A is still within range of B and C, A will split its damage between B and C as described above.
 
However, consider this arrangement:
```
.......B..
A.........
.......C..
```

If A moves as before, it will reach a point where it enters range of B and C simultaneously. Then both B and C will take 32 damage (half of A’s attack), but A will take 128 damage (the sum of B and C’s attacks).




