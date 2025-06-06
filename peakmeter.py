import wx
import random

import wx.lib.agw.peakmeter as PM

class MyFrame(wx.Frame):

    def __init__(self, parent):

        wx.Frame.__init__(self, parent, -1, "PeakMeterCtrl Demo")

        panel = wx.Panel(self)

        # Initialize Peak Meter control 1
#        self.vertPeak = PM.PeakMeterCtrl(panel, -1, style=wx.SIMPLE_BORDER, agwStyle=PM.PM_VERTICAL)
        # Initialize Peak Meter control 2
        self.horzPeak = PM.PeakMeterCtrl(panel, -1, agwStyle=PM.PM_HORIZONTAL, size=(200,20))

#        self.vertPeak.SetMeterBands(1, 100)
        self.horzPeak.SetMeterBands(1, 50)

        # Layout the two PeakMeterCtrl
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
#        mainSizer.Add(self.vertPeak, 0, wx.EXPAND | wx.ALL, 4)
        mainSizer.Add(self.horzPeak, 0, wx.ALL, 1)

        panel.SetSizer(mainSizer)
        mainSizer.Layout()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        wx.CallLater(500, self.Start)


    def Start(self):
        ''' Starts the PeakMeterCtrl. '''

        self.timer.Start(1000//100)            # 2 fps

#        self.vertPeak.Start(1000//18)        # 18 fps
        self.horzPeak.Start(1000//1000)        # 20 fps


    def OnTimer(self, event):
        '''
        Handles the ``wx.EVT_TIMER`` event for :class:`PeakMeterCtrl`.

        :param `event`: a :class:`TimerEvent` event to be processed.
        '''

        # Generate 15 random number and set them as data for the meter
        nElements = 1
        arrayData = []

        for i in range(nElements):
            nRandom = random.randint(0, 100)
            arrayData.append(nRandom)

#        self.vertPeak.SetData(arrayData, 0, nElements)
        self.horzPeak.SetData(arrayData, 0, nElements)


# our normal wxApp-derived class, as usual

app = wx.App(0)

frame = MyFrame(None)
app.SetTopWindow(frame)
frame.Show()

app.MainLoop()
