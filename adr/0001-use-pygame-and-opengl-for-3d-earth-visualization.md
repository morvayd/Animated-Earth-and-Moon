# ADR 0001: Use Pygame and OpenGL for 3D Planet Visualization

## Status
Accepted

## Context
The project requires an interactive, real-time 3D planetary visualization. It should support Earth day, Earth night, and Moon map views, provide controls for rotation and mesh visibility, and use local texture files without requiring network access.

## Decision
We will use a combination of the following libraries to implement the visualization:

1.  **Pygame**: To manage the application lifecycle, window, keyboard input, display text, and frame-rate timing.
2.  **PyOpenGL**: To handle the 3D rendering pipeline, including:
    *   Creating and managing vertex and UV arrays for a sphere.
    *   Mapping textures to geometry.
    *   Managing the projection and model-view matrices for 3D perspective.
    *   Handling depth testing, blending, and the optional wireframe overlay.
3.  **NumPy**: To perform efficient mathematical calculations for generating the spherical mesh (converting spherical coordinates to Cartesian coordinates).
4.  **Pillow (PIL)**: To load and process the local textures and render the on-screen controls reminder.

The application loads three equirectangular maps stored beside `earth.py`:

* Daytime Earth: `earth_texture.jpg` (2048×1024 JPEG)
* Nighttime Earth city lights: `earth_lights.png` (2048×1024 PNG)
* Moon: `moon_texture.jpg` (1024×512 JPEG)

The textures are selected in sequence with **T**. The daytime map is brightened by a factor of 2 in memory; all three maps are converted to RGB and horizontally flipped before upload. The local image files are not modified. The app does not download textures or generate fallback maps, so all three files must be present and readable at startup.

Rotation is controlled by **W/S** (speed) and **A/D** (direction). **M** toggles the wireframe mesh, which is on by default. The wireframe alpha is 0.75 for Day, 0.25 for Night, and 1.00 for Moon. The control strip displays the current speed, direction, view, and mesh state; **ESC** exits.

## Consequences

### Pros
*   **Interactivity**: Pygame provides keyboard input for rotation, view selection, and mesh visibility.
*   **Rendering**: OpenGL renders the textured rotating sphere and supports an alpha-blended wireframe overlay.
*   **Offline use**: Bundled local textures avoid a network dependency at launch.
*   **Mathematical Precision**: NumPy ensures that the geometric mesh generation is efficient and accurate.

### Cons
*   **Dependency Management**: The application requires Pygame, PyOpenGL, NumPy, and Pillow, which must be installed in the environment.
*   **Complexity**: Combining multiple specialized libraries increases the complexity of the initialization and rendering logic compared to a single-library approach.
*   **Local asset requirement**: All three texture files must remain beside `earth.py`; missing or unreadable files prevent startup.
