import threading
import time
import logging
import base64
import pygame.camera
import queue as Queue
from PIL import Image
from io import BytesIO
import requests
import cv2
import json
from pygame.locals import *
import re
import matplotlib.pyplot as plt
import base64

face_cascade = cv2.CascadeClassifier('./git/opencv/opencv/data/haarcascades/haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('./git/opencv/opencv/data/haarcascades/haarcascade_eye.xml')
font = cv2.FONT_HERSHEY_SIMPLEX

DEVICE = '/dev/video0'
SIZE = (640, 480)

GC_PROB_ENUM = {'VERY_UNLIKELY':0,'UNLIKELY':1,'POSSIBLE':2,'LIKELY':3,'VERY_LIKELY':4}

headers = {
    # Request headers.
    'Content-Type': 'application/octet-stream',

    # NOTE: Replace the "Ocp-Apim-Subscription-Key" value with a valid subscription key.
    #Yong's key:'Ocp-Apim-Subscription-Key': '87443556668c4ad89ce30887acd834f6',
    'Ocp-Apim-Subscription-Key': '5938ac171ad44c6f9efa52129bd61330',
}
params = {
    # Request parameters. All of them are optional.
    #'visualFeatures': 'Faces',
    'returnFaceId': 'true',
    'returnFaceLandmarks': 'false',
    'returnFaceAttributes': 'age,gender,smile,facialHair,glasses,emotion,hair,makeup,accessories,exposure',
    #'details': 'Celebrities',
    'language': 'en'
}

GCKEY = "AIzaSyBqYTaCgDknkriXIhlFqkmERcVqk7M0yAc"

gCloud_Vision_Req = {
  "requests":[
    {
      "image":{
        "content": ""
      },
      "features": [
        {
          "type":"FACE_DETECTION",
          "maxResults":5
        },
        {
          "type":"LABEL_DETECTION",
          "maxResults":5
        },
        {
          "type":"WEB_DETECTION",
          "maxResults":5
        }
      ]
    }
  ]
}

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-9s) %(message)s', )

BUF_SIZE = 100
FPS = 25
az_q_frame = Queue.Queue(BUF_SIZE)
gc_q_frame = Queue.Queue(BUF_SIZE)
az_q_result = Queue.Queue(BUF_SIZE)
gc_q_result = Queue.Queue(BUF_SIZE)
label_q = Queue.Queue(BUF_SIZE)
label_q_result = Queue.Queue(BUF_SIZE)

def putAzFrame(frame):
    if not az_q_frame.full():
        az_q_frame.put(frame)
        #logging.debug('Putting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    return 0

def popAzFrame():
    frame = None
    if not az_q_frame.empty():
        frame = az_q_frame.get()
        #logging.debug('Getting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    else:
        frame = az_q_frame.get(block=True)

    return frame

def putGcFrame(frame):
    if not gc_q_frame.full():
        gc_q_frame.put(frame)
        #logging.debug('Putting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    return 0

def popGcFrame():
    frame = None
    if not gc_q_frame.empty():
        frame = gc_q_frame.get()
        #logging.debug('Getting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    else:
        frame = gc_q_frame.get(block=True)

    return frame

def putLabels(labels):
    if not label_q.full():
        label_q.put(labels)
        #logging.debug('Putting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    return 0

def popLabelsResult():
    frame = None
    if not label_q.empty():
        result = label_q.get()
        #logging.debug('Getting ' + str(frame)
        #              + ' : ' + str(q_frame.qsize()) + ' items in q_frame')
    else:
        result = label_q.get(block=True)

    return result

class labelProducerThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(labelProducerThread, self).__init__()
        self.target = target
        self.name = name

    def run(self):
        alert = False
        while True:
            try:
                message = '{"Alert":0}'
                tag = popLabelsResult()
                labelList = tag["labelAnnotations"]
                webList = tag["webDetection"]["webEntities"]
                if not label_q_result.full():
                    tagsList = [web["description"] for web in webList]
                    headWearsList = list(filter(lambda x: re.match(r".*cap.*|.*hat.*|.*helmet.*|.*head.*", x, re.IGNORECASE), tagsList))
                    eyeWearsList = list(filter(lambda x: re.match(r".*glasses.*", x, re.IGNORECASE), tagsList))
                    coversList = list(filter(lambda x: re.match(r".*cover.*|.*mask.*|.*protective.*", x, re.IGNORECASE), tagsList))
                    riskList = list(filter(lambda x: re.match(r".*robbery.*|.*mask.*|.*burglary.*|.*theft.*|.*crime.*|.*sword.*|.*knife.*|.*gun.*|.*rifle.*|.*pistol.*|.*firearm.*|.*revolver.*", x, re.IGNORECASE), tagsList))

                    if len(riskList) > 0:
                        if alert == False:
                            alert = True
                            frame = popGcFrame()
                            image = str(frame,"utf-8")
                            message = {"Alert":1,"Image":image,"Risk":str(riskList)}
                        else:
                            message = {"Alert": 0}
                    else:
                        alert = False
                        message = {"Alert":0}
                    messageJson = json.dumps(message)
                    requests.post(
                        url='https://dd2c252e.ngrok.io/robberyDetection/api/v1.0/notify',
                        headers={'Content-Type': 'application/json'},
                        data=messageJson)
                    result = [headWearsList, eyeWearsList, coversList, riskList, tagsList]
                    label_q_result.put(result)
            except Exception as e:
                print(e)
                continue
        return

class azProducerThread(threading.Thread):
    isFirst = True

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(azProducerThread, self).__init__()
        self.target = target
        self.name = name

    def defFirst(self,val):
       self.isFirst = val

    def run(self):
        while True:
            frame = popAzFrame()
            if not az_q_result.full():
                try:
                    response = requests.post(
                        #url='https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/analyze',
                        url='https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect',
                        headers=headers,
                        params=params,
                        data=frame)
                    data = response.json()
                except Exception as e:
                    print("[Errno {0}] {1}".format(e.errno, e.strerror))
                if not self.isFirst:
                    az_q_result.put(data)
                    logging.debug('Putting ' + str(data)
                                  + ' : ' + str(az_q_result.qsize()) + ' items in q_result')
                else:
                    #print("First Message ignored")
                    self.isFirst = False
                    #print(az_q_result.qsize())
                #time.sleep(random.random())
        return


class gcProducerThread(threading.Thread):
    isFirst = True

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(gcProducerThread, self).__init__()
        self.target = target
        self.name = name

    def defFirst(self,val):
       self.isFirst = val

    def run(self):
        while True:
            frame = popGcFrame()
            if not gc_q_result.full():
                try:
                    gCloud_Vision_Req["requests"][0]["image"]["content"] = str(frame,'utf-8')
                    json_dump = json.dumps(gCloud_Vision_Req)
                    response = requests.post(
                        url='https://vision.googleapis.com/v1/images:annotate?key='+GCKEY,
                        headers={'Content-Type': 'application/json'},
                        data=json_dump)
                    data = response.json()
                    #print(data['responses'][0]['faceAnnotations'][0])
                except Exception as e:
                    print("[Errno {0}] {1}".format(e.errno, e.strerror))
                if not self.isFirst:
                    gc_q_result.put(data)
                else:
                    #print("First Message ignored")
                    self.isFirst = False
                    #print(gc_q_result.qsize())
                #logging.debug('Putting ' + str(data)
                #              + ' : ' + str(q_result.qsize()) + ' items in q_result')
                #time.sleep(random.random())
        return

class ConsumerThread(threading.Thread):
    DEVICE = '/dev/video0'
    SIZE = (640, 480)
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ConsumerThread, self).__init__()
        self.target = target
        self.name = name
        pygame.init()
        pygame.camera.init()
        self.display = pygame.display.set_mode(self.SIZE, 0)
        self.camera = pygame.camera.Camera(self.DEVICE, self.SIZE)
        return

    def run(self):
        self.camera.start()
        self.capture = True
        frameCount = 1
        azItem = None
        gcItem = None
        label = "Identifying...."
        eyeWearsList = []
        labels = []
        while self.capture:
            time.sleep(1. / FPS)
            try:
                screen = pygame.surface.Surface(self.SIZE, 0, self.display)
                screen = self.camera.get_image(screen)
                screen_save = pygame.transform.rotate(screen,90)
                screen_save = pygame.transform.flip(screen_save, False, True)

                screen = pygame.transform.flip(screen, True, False)
                screen = pygame.transform.rotate(screen,90)
                img = pygame.surfarray.array3d(screen)
                img = cv2.flip(img,1)

                if (frameCount % FPS) == 0:
                    img_save = pygame.surfarray.array3d(screen_save)
                    saver = Image.fromarray(img_save)
                    #byteTest = saver.tobytes()
                    #sizeTest = saver.size
                    #modeTest = saver.mode
                    #testImageLoad = Image.frombytes(modeTest, sizeTest, byteTest)
                    #testImageLoad.save("./test.png")
                    az_byte_io = BytesIO()
                    gc_byte_io = BytesIO()
                    saver.save(az_byte_io, "PNG")
                    az_byte_io.seek(0)
                    putAzFrame(az_byte_io)
                    # test = image = open('./dataset/Nattawat_/25.jpg','rb').read()
                    # putGcFrame(base64.b64encode(test))
                    saver.save(gc_byte_io, "PNG")
                    gc_byte_io.seek(0)
                    #testRead = gc_byte_io.read()
                    #testRead64 = base64.b64encode(testRead)
                    #testDec64 = base64.b64decode(testRead64)
                    #testImageBytesIO = BytesIO(testDec64)
                    #testImageLoad = Image.open(testImageBytesIO)
                    #testImageLoad.save("./test2.png")
                    putGcFrame(base64.b64encode(gc_byte_io.read()))

                if not az_q_result.empty():
                    # print("count:"+str(q_result.qsize()))
                    azItem = az_q_result.get()
                    logging.debug('Getting ' + str(azItem)
                                  + ' : ' + str(az_q_result.qsize()) + ' items in az_q_result')

                if not gc_q_result.empty():
                    # print("count:"+str(q_result.qsize()))
                    gcItem = gc_q_result.get()
                    logging.debug('Getting ' + str(gcItem)
                                  + ' : ' + str(gc_q_result.qsize()) + ' items in gc_q_result')
                    #Context
                    labelList = gcItem["responses"][0]
                    putLabels(labelList)
                if not label_q_result.empty():
                    labels = label_q_result.get()
                headWear = "Headwear : " + str(labels[0]) if len(labels) > 0 else "Headwear:"
                eyeWear = "Eyewear : " + str(labels[1]) if len(labels) > 0 else "Eyewear:"
                cover = "Cover : " + str(labels[2]) if len(labels) > 0 else "Cover:"
                weapon = "Risk : " + str(labels[3]) if len(labels) > 0 else "Risk:"
                tag = "Tag : " + str(labels[4]) if len(labels) > 0 else "Tag : "
                cv2.putText(img, headWear, (10, 20), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(img, eyeWear, (10, 35), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(img, cover, (10, 50), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(img, weapon, (10, 65), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                cv2.putText(img, tag, (10, SIZE[1] - 25), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
                #Face
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                faces = sorted(faces, key=lambda x: x[0])
                curr_faces_count = len(faces)
                if curr_faces_count != 0:

                    loc = []
                    for (x, y, w, h) in faces:
                        loc.append({'x':x,'y':y,'w':w,'h':h})
                        roi_gray = gray[y:y + h, x:x + w]
                        roi_color = img[y:y + h, x:x + w]
                        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        eyes = eye_cascade.detectMultiScale(roi_gray)
                        for (ex,ey,ew,eh) in eyes:
                            cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)
                    if azItem != None and not ("code" in azItem):# and ("faces" in azItem):
                        if len(azItem) != 0:
                            itemSort = sorted(azItem, key=lambda x: x["faceRectangle"]["left"], reverse=True)
                            index = 0
                            if len(itemSort) == len(loc):# and q_result.qsize() != 0:
                                for facesItem in itemSort:
                                    faceAtrib = facesItem["faceAttributes"]
                                    gender = "Gender: %s" % (faceAtrib['gender'])
                                    age = "Age: %s" % (faceAtrib['age'])
                                    cv2.putText(img, gender, (loc[index]['x'] - 1, loc[index]['y'] - 20), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                                    cv2.putText(img, age, (loc[index]['x'] - 1, loc[index]['y'] - 1), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                                    index += 1
                            else:
                                for l in loc:
                                    cv2.putText(img, str(label), (l['x'] - 1, l['y'] - 1), font, 0.5, (255, 255, 255), 1,cv2.LINE_AA)
                    else:
                        for l in loc:
                            cv2.putText(img, str(label), (l['x'] - 1, l['y'] - 1), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

                    if gcItem != None and ("faceAnnotations" in gcItem["responses"][0]):
                        if len(gcItem['responses'][0]['faceAnnotations']) != 0:
                            itemSort = sorted(gcItem['responses'][0]['faceAnnotations'], key=lambda x: x["boundingPoly"]["vertices"][0]["x"], reverse=True)
                            index = 0
                            if len(itemSort) == len(loc):# and q_result.qsize() != 0:
                                for faces in itemSort:
                                    emoLabel = "Emotion : neutral"
                                    headLabel = "IsHeadWear : false"
                                    ExposeLabel = "IsExposed : True"
                                    emoProbMax = 0
                                    for key in faces:
                                        if(isinstance(faces[key], str)):
                                            if key in ['angerLikelihood','joyLikelihood','sorrowLikelihood','surpriseLikelihood']:
                                                (emoLabel,emoProbMax) = ("Emotion : "+key[0:-10],GC_PROB_ENUM[faces[key]]) if (GC_PROB_ENUM[faces[key]] > emoProbMax and GC_PROB_ENUM[faces[key]] >= 3) else (emoLabel,emoProbMax)
                                            if key in ['headwearLikelihood']:
                                                headLabel = "IsHeadWear : True" if GC_PROB_ENUM[faces[key]] >= 3 else headLabel
                                            if key in ['underExposedLikelihood']:
                                                ExposeLabel = "IsExposed : False" if GC_PROB_ENUM[faces[key]] >= 3 else ExposeLabel
                                    cv2.putText(img, emoLabel, (loc[index]['x'] + loc[index]['w'], loc[index]['y'] + 25), font, 0.5, (255,0, 0), 1, cv2.LINE_AA)
                                    cv2.putText(img, headLabel, (loc[index]['x'] + loc[index]['w'], loc[index]['y'] + 40), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                                    cv2.putText(img, ExposeLabel, (loc[index]['x'] + loc[index]['w'], loc[index]['y'] + 55), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
                                    if ("x" in faces["boundingPoly"]["vertices"][0]) and ("y" in faces["boundingPoly"]["vertices"][0]):
                                        (x,y) = (SIZE[0] - faces["boundingPoly"]["vertices"][0]["x"],faces["boundingPoly"]["vertices"][0]["y"])
                                        (w,h) = ((faces["boundingPoly"]["vertices"][2]["x"] - faces["boundingPoly"]["vertices"][0]["x"]),
                                                (faces["boundingPoly"]["vertices"][2]["y"] - faces["boundingPoly"]["vertices"][0]["y"]))
                                        cv2.rectangle(img, (x-w, y), (x, y + h), (255, 0, 255), 2)
                                    index += 1

                    if frameCount <= FPS:
                        frameCount += 1
                    else:
                        frameCount = 1
                else:
                    label = "Identifying...."
                    with az_q_frame.mutex:
                        az_q_frame.queue.clear()
                    with gc_q_frame.mutex:
                        gc_q_frame.queue.clear()
                    with az_q_result.mutex:
                        az_q_result.queue.clear()
                    with gc_q_result.mutex:
                        gc_q_result.queue.clear()
                    azP.defFirst(True)
                    azItem = None
                    gcItem = None
                    frameCount = 0
                pygame.surfarray.blit_array(screen, img)
                screen = pygame.transform.flip(screen, False, True)
                screen = pygame.transform.rotate(screen,-90)
                self.display.blit(screen, (0,0))
                pygame.display.update()
                for event in pygame.event.get():
                        if event.type == KEYDOWN:
                                capture = False
            except Exception as e:
                print(e)
                continue
        return


if __name__ == '__main__':
    azP = azProducerThread(name='Azure_producer')
    gcP = gcProducerThread(name='Gcloud_producer')
    lP = labelProducerThread(name='Label_producer')
    c = ConsumerThread(name='consumer')

    azP.start()
    time.sleep(2)
    gcP.start()
    time.sleep(2)
    lP.start()
    time.sleep(2)
    c.start()
    time.sleep(2)