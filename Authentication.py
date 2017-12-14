import GUI.mainFrame as mf
import GUI.FaceDetection as fd

if __name__ == "__main__":
    detectionCallback = fd.FaceDetection().detect
    top = mf.mainFrame(detectionCallback)
    top.run()
