import buttonxtendgpiozero
import time


def main():
    with buttonxtendgpiozero.Button(20) as taster:
        taster.when_pressed = taster.when_pressed_
        taster.when_released = taster.when_released_
        while True:
            if taster.check_status():
                print("Taster wurde gedrückt")
            elif taster.is_pressed:
                print("Taster wird gehalten")
            else:
                print("Keine Betätigung")

            if taster.event_time is not None:
                print("Taster wurde gedrückt für {} Sekunden".format(taster.get_event_time()))

            time.sleep(0.5)


if __name__ == "__main__":
    main()
