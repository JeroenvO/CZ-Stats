import gc
from time import sleep
from math import ceil
import buttons
import defines
import rgb
import system
import uinterface
import urequests
import wifi

# globals
stat = 0
old_stat = 0
l = None
# colors
colors = [
    # cmy
    [(0, 255, 255), (255, 0, 255), (255, 255, 0)],
    [(255, 255, 0), (0, 255, 255), (255, 0, 255)],
    [(255, 0, 255), (255, 255, 0), (0, 255, 255)],
    # rgb
    [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
    [(0, 0, 255), (255, 0, 0), (0, 255, 0)],
    [(0, 255, 0), (0, 0, 255), (255, 0, 0)],
    # white
    [(255, 255, 255), (255, 255, 255), (255, 255, 255)],
]
color = 0
# buttons
UP, DOWN, LEFT, RIGHT = defines.BTN_UP, defines.BTN_DOWN, defines.BTN_LEFT, defines.BTN_RIGHT
A, B = defines.BTN_A, defines.BTN_B


def input_up(pressed):
    if pressed:
        global color
        color = (color + 1) % (len(colors))
        draw_text()


def input_down(pressed):
    if pressed:
        global color
        color = (color - 1) % (len(colors))
        draw_text()


def input_left(pressed):
    if pressed:
        global stat
        stat = 1 - stat


def input_right(pressed):
    if pressed:
        global stat
        stat = 1 - stat


def input_B(pressed):
    if pressed:
        rgb.clear()
        rgb.text("Bye!")
        sleep(0.5)
        system.reboot()


def input_A(pressed):
    if pressed:
        rgb.background((255, 100, 100))
    else:
        rgb.background((0, 0, 0))


def draw_error(e):
    rgb.clear()
    rgb.pixel((255, 0, 0), (REFRESH_RATE, 7))  # red for error
    rgb.text('E {}'.format(e))


def draw_text():
    global l, color
    rgb.clear()
    if l:
        rgb.pixel((0, 150, 0), (REFRESH_RATE, 7))  # green for new data
        for i, d in enumerate(l):
            rgb.text(d, colors[color][i], (ceil(31/len(l))*i, 0))
    else:
        rgb.text('E Data')


# init
buttons.register(UP, input_up)
buttons.register(DOWN, input_down)
buttons.register(LEFT, input_left)
buttons.register(RIGHT, input_right)
buttons.register(B, input_B)
buttons.register(A, input_A)

rgb.setfont(rgb.FONT_6x3)
rgb.framerate(10)  # second updates
REFRESH_RATE = 31  # times framerate updates.

# wifi connect
if not wifi.status():
    if not uinterface.connect_wifi():
        system.reboot()
rgb.text('Hi!')

# main loop
count = REFRESH_RATE - 1  # start fast
while True:
    if not wifi.status():
        if not uinterface.connect_wifi():
            system.reboot()

    if count < REFRESH_RATE and stat == old_stat:
        gc.collect()
        sleep(0.1)
        rgb.pixel((150, 150, 0), (count, 7))  # refresh counter
        count += 1
        continue
    else:
        count = 0
    old_stat = stat
    if stat == 0:  # generator
        try:
            r = urequests.post("https://dashboard.eventinfra.org/api/datasources/proxy/1/render",
                               data='target=infra.ACT_PWR_1_generator_tot_kva&target=infra.ACT_PWR_2_generator_tot_kva&target=infra.ACT_PWR_3_generator_tot_kva&from=-3min&until=now&format=json&maxDataPoints=768')
        except:
            draw_error('req')
            continue
        if r.status_code == 200:
            # rgb.clear()
            try:
                l = [str(int(i['datapoints'][-1][0])) for i in r.json()]
            except:
                draw_error('json')
                continue
            draw_text()
        else:
            draw_error(r.status_code)
    elif stat == 1:  # up/down link
        try:
            r = urequests.post("https://dashboard.eventinfra.org/api/datasources/proxy/1/render",
                               data='target=scale(scaleToSeconds(nonNegativeDerivative(net.kvm2.snmp.if_octets-eth3_300.tx),1),8)&target=scale(scaleToSeconds(nonNegativeDerivative(net.kvm2.snmp.if_octets-eth3_300.rx),1),8)&from=-5min&until=now&format=json&maxDataPoints=768')
        except:
            rgb.text("E req")
            continue
        if r.status_code == 200:
            try:
                l = [str(int(i['datapoints'][-1][0] / 1e6)) for i in r.json()]
            except:
                draw_error('json')
                continue
            draw_text()

        else:  # non 200 status code
            draw_error(str(r.status_code))
