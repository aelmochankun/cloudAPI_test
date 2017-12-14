import numpy as np
import pygame.camera
from pygame.locals import *
import cv2
import os
import time
import requests
import base64
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

headers = {
    # Request headers.
    'Content-Type': 'application/octet-stream',

    # NOTE: Replace the "Ocp-Apim-Subscription-Key" value with a valid subscription key.
    'Ocp-Apim-Subscription-Key': '87443556668c4ad89ce30887acd834f6',
}

params = {
    # Request parameters. All of them are optional.
    'visualFeatures': 'Categories,Faces',
    #'details': 'Celebrities',
    'language': 'en'
}

class FaceDetection():
    dir = os.path.dirname(__file__)
    face_cascade = cv2.CascadeClassifier(dir+'/../git/opencv/opencv/data/haarcascades/haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(dir+'/../git/opencv/opencv/data/haarcascades/haarcascade_eye.xml')
    DEVICE = '/dev/video0'
    SIZE = (640, 480)


    def detect(self):
        pygame.init()
        pygame.camera.init()
        display = pygame.display.set_mode(self.SIZE, 0)
        #pygame.display.flip()
        camera = pygame.camera.Camera(self.DEVICE, self.SIZE)
        camera.start()
        font = cv2.FONT_HERSHEY_SIMPLEX
        capture = True
        judge_Loop = 0
        curr_faces_count = 0
        while capture:
            #pygame.display.get_surface()
            screen = pygame.surface.Surface(self.SIZE, 0, display)
            screen = camera.get_image(screen)
            screen = pygame.transform.flip(screen, True, False)
            #screen = pygame.transform.rotate(screen,90)
            screen = pygame.transform.flip(screen, True, False)
            screen = pygame.transform.rotate(screen,90)
            img = pygame.surfarray.array3d(screen)
            img = cv2.flip(img,1)

            pygame.surfarray.blit_array(screen, img)
            display.blit(screen, (0,0))
            pygame.display.update()
            for event in pygame.event.get():
                    if event.type == KEYDOWN:
                            capture = False
        camera.stop()
        pygame.quit()