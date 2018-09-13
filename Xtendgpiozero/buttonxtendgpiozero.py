import gpiozero
import time


class Button(gpiozero.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = False
        self.event_time = None
        self._pressed_at = None

    def check_status(self):
        status = self._event
        # print("status: {}".format(status))
        self.reset_event()
        return status

    def when_pressed_(self):
        self.starte_event_time()
        self.setze_event()

    def when_released_(self):
        self.stoppe_event_time()

    def get_event_time(self):
        event_time = self.event_time
        self.event_time = None
        return event_time

    def starte_event_time(self):
        self._pressed_at = time.time()

    def stoppe_event_time(self):
        self.event_time = time.time() - self._pressed_at

    def setze_event(self):
        self._event = True

    def reset_event(self):
        self._event = False


