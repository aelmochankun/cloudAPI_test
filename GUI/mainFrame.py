import tkinter
from tkinter import *

class mainFrame(Frame):

    top = tkinter.Tk()

    def __init__(self,detectionCallBack):
        super().__init__()
        self.initUI(detectionCallBack)


    def initUI(self,detectionCallBack):
        self.top.geometry("300x80+300+300")
        self.master.title("Realtime eKYC Demo")
        self.pack(fill=BOTH, expand=1)
        startDetectionButton = Button(self, text="Start", command=detectionCallBack)
        startDetectionButton.place(x=50, y=25)
        quitButton = Button(self, text="Quit", command=self.quit)
        quitButton.place(x=200, y=25)

    def run(self):
        self.top.mainloop()
