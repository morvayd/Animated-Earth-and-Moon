import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance

IMAGE_PATH_BASE = Path(__file__).with_name("earth_texture.jpg")
IMAGE_PATH_LIGHTS = Path(__file__).with_name("earth_lights.png")
IMAGE_PATH_MOON = Path(__file__).with_name("moon_texture.jpg")
WINDOW_SIZE = (700, 700)

class EarthApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Earth: Wireframe + Texture")

        # Enable depth testing for 3D rendering
        glEnable(GL_DEPTH_TEST)
        
        self.base_texture = self._load_texture(IMAGE_PATH_BASE, brighten=True)
        self.lights_texture = self._load_texture(IMAGE_PATH_LIGHTS)
        self.moon_texture = self._load_texture(IMAGE_PATH_MOON)
        
        self.rotation_angle = 0.0
        self.rotation_speed = 0.1  # Degrees per frame
        self.direction = 1         # 1 for forward, -1 for backward
        self.view_mode = "Day"
        self.mesh_overlay_enabled = True

        # Generate sphere geometry
        self.sphere_data = self._generate_sphere(32, 32)
        self.controls_font = pygame.font.Font(None, 18)
        self.controls_texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.controls_texture_id)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, 700, 30, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        self.clock = pygame.time.Clock()

    def _render_controls_overlay(self, speed, direction_text):
        """Draws the dynamic controls reminder centered above the sphere."""
        width, height = 700, 30
        x = (WINDOW_SIZE[0] - width) // 2
        y = 18
        
        # Create the text surface
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (0, 0, 0, 255), surface.get_rect(), border_radius=6)
        text = (
            f"W/S: Speed {speed:.2f}     A/D: Direction {direction_text}     "
            f"T: Cycle view ({self.view_mode})     "
            f"M: Mesh {'On' if self.mesh_overlay_enabled else 'Off'}     ESC: Exit"
        )
        rendered = self.controls_font.render(text, True, (220, 232, 245))
        surface.blit(rendered, rendered.get_rect(center=(width // 2, height // 2)))

        # Update the texture with the new text
        glBindTexture(GL_TEXTURE_2D, self.controls_texture_id)
        glTexSubImage2D(
            GL_TEXTURE_2D, 0, 0, 0, width, height,
            GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(surface, "RGBA", True)
        )

        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_SIZE[0], WINDOW_SIZE[1], 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.controls_texture_id)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(x, y)
        glTexCoord2f(1, 1)
        glVertex2f(x + width, y)
        glTexCoord2f(1, 0)
        glVertex2f(x + width, y + height)
        glTexCoord2f(0, 0)
        glVertex2f(x, y + height)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def _toggle_view(self):
        """Cycles between daytime Earth, nighttime Earth, and the Moon."""
        modes = ("Day", "Night", "Moon")
        self.view_mode = modes[(modes.index(self.view_mode) + 1) % len(modes)]

    def _toggle_mesh_overlay(self):
        """Toggles the wireframe mesh overlay."""
        self.mesh_overlay_enabled = not self.mesh_overlay_enabled

    def _load_texture(self, image_path, brighten=False):
        """Loads a local image and uploads it as an OpenGL texture."""
        with Image.open(image_path) as image:
            img = image.convert("RGB")
        if brighten:
            img = ImageEnhance.Brightness(img).enhance(2.0)
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        img_data = img.tobytes()
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.size[0], img.size[1], 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tex_id

    def _generate_sphere(self, rows, cols):
        """Generates vertices, UV coordinates, and indices for a sphere mesh."""
        vertices = []
        uvs = []
        indices = []

        for r in range(rows + 1):
            phi = np.pi * r / rows
            for c in range(cols + 1):
                theta = 2 * np.pi * c / cols

                # Spherical to Cartesian conversion
                x = np.sin(phi) * np.cos(theta)
                y = np.cos(phi)
                z = np.sin(phi) * np.sin(theta)

                vertices.extend([x, y, z])
                uvs.extend([c / cols, r / rows])

        for r in range(rows):
            for c in range(cols):
                first = r * (cols + 1) + c
                second = first + cols + 1
                indices.extend([first, second, first + 1])
                indices.extend([second, second + 1, first + 1])

        return {
            'vertices': np.array(vertices, dtype=np.float32),
            'uvs': np.array(uvs, dtype=np.float32),
            'indices': np.array(indices, dtype=np.uint32)
        }

    def _render_scene(self):
        """Renders the textured sphere and the wireframe overlay."""
        vertices = self.sphere_data['vertices']
        uvs = self.sphere_data['uvs']
        indices = self.sphere_data['indices']

        # 1. Render Textured Sphere
        glColor3f(1.0, 1.0, 1.0)
        textures = {
            "Day": self.base_texture,
            "Night": self.lights_texture,
            "Moon": self.moon_texture,
        }
        texture = textures[self.view_mode]
        if texture:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, texture)
        
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glTexCoordPointer(2, GL_FLOAT, 0, uvs)
        
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

        if self.mesh_overlay_enabled:
            self._render_mesh_overlay(indices)

        glEnableClientState(GL_VERTEX_ARRAY)

    def _render_mesh_overlay(self, indices):
        """Renders the semi-transparent wireframe over the sphere."""
        glDisable(GL_TEXTURE_2D)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        wireframe_alpha = {
            "Day": 0.75,
            "Night": 0.25,
            "Moon": 1.00,
        }[self.view_mode]
        glColor4f(0.2, 0.5, 1.0, wireframe_alpha)
        glDrawElements(GL_LINES, len(indices), GL_UNSIGNED_INT, indices)
        glPopAttrib()

    def run(self):
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, WINDOW_SIZE[0]/WINDOW_SIZE[1], 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        print("\n--- Controls ---")
        print("W: Increase Speed")
        print("S: Decrease Speed")
        print("A: Rotate Backward")
        print("D: Rotate Forward")
        print("T: Cycle Day/Night/Moon view")
        print("M: Toggle wireframe mesh")
        print("ESC: Exit")

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    running = False
                elif event.type == KEYDOWN and event.key == K_t:
                    self._toggle_view()
                elif event.type == KEYDOWN and event.key == K_m:
                    self._toggle_mesh_overlay()

            # Handle Input
            keys = pygame.key.get_pressed()
            if keys[K_w]: self.rotation_speed += 0.02
            if keys[K_s]: self.rotation_speed -= 0.02
            if keys[K_a]: self.direction = -1
            if keys[K_d]: self.direction = 1
            
            self.rotation_speed = max(0.01, min(self.rotation_speed, 5.0))
            self.rotation_angle += self.rotation_speed * self.direction

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            gluLookAt(0, 0, 3, 0, 0, 0, 0, 1, 0)
            glRotatef(self.rotation_angle, 0, 1, 0)
            self._render_scene()
            
            direction_text = "Forward" if self.direction == 1 else "Backward"
            self._render_controls_overlay(self.rotation_speed, direction_text)
            
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    app = EarthApp()
    app.run()
