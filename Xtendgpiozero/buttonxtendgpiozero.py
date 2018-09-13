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
        self._event = False
        return status

    def when_pressed_(self):
        self._pressed_at = time.time()
        self._event = True

    def when_released_(self):
        self.event_time = time.time() - self._pressed_at

    def get_event_time(self):
        event_time = self.event_time
        self.event_time = None
        return event_time


