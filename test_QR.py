from pyzbar.pyzbar import decode
import pygame.camera
from PIL import Image
from pygame.locals import *

DEVICE = '/dev/video0'
SIZE = (640, 480)

pygame.init()
pygame.camera.init()
display = pygame.display.set_mode(SIZE, 0)
camera = pygame.camera.Camera(DEVICE, SIZE)

camera.start()
capture = True
while capture:
    screen = pygame.surface.Surface(SIZE, 0, display)
    screen = camera.get_image(screen)
    screen_save = pygame.transform.rotate(screen, 90)
    screen_save = pygame.transform.flip(screen_save, False, True)

    screen = pygame.transform.flip(screen, True, False)
    screen = pygame.transform.rotate(screen, 90)
    img = pygame.surfarray.array3d(screen)
    test = Image.fromarray(img)
    dec = decode(test)
    print(dec)
    pygame.surfarray.blit_array(screen, img)
    screen = pygame.transform.flip(screen, False, True)
    screen = pygame.transform.rotate(screen, -90)
    display.blit(screen, (0, 0))
    pygame.display.update()
    for event in pygame.event.get():
        if event.type == KEYDOWN:
            capture = False

