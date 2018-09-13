import gpiozero
import datetime


class Button(gpiozero.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = False
        self.event_time = 0

    def set_event(self):
        start = datetime.datetime.now()
        ende = datetime.datetime.now()
        while self.is_pressed:
           ende = datetime.datetime.now()
        self.event_time = (ende - start).total_seconds()
        # print(self.event_time)
        self._event = True

    def check_status(self):
        status = self._event
        # print("status: {}".format(status))
        self._event = False
        return status
