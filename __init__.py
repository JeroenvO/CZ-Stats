from time import sleep

import buttons
import defines
import rgb
import system
import uinterface
import urequests
import wifi
from default_icons import icon_no_wifi

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


def draw_text():
    global l, color
    rgb.clear()
    if len(l) == 3:
        rgb.text(l[0], colors[color][0], (0, 0))
        rgb.text(l[1], colors[color][1], (11, 0))
        rgb.text(l[2], colors[color][2], (22, 0))
    elif len(l) == 2:
        rgb.text(l[0], colors[color][0], (0, 0))
        rgb.text(l[1], colors[color][1], (16, 0))
    else:
        rgb.text('error')


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
rgb.pixel((0, 255, 0), (REFRESH_RATE, 7))  # final refresh pixel

# wifi connect
if not wifi.status():
    if not uinterface.connect_wifi():
        system.reboot()
rgb.text('Hi!')
rgb.pixel((255, 255, 0), (0, 7))

# main loop
count = 0
while True:
    if not wifi.status():
        if not uinterface.connect_wifi():
            system.reboot()

    if count < REFRESH_RATE and stat == old_stat:
        sleep(0.1)
        rgb.pixel((255, 255, 0), (count, 7))  # refresh counter
        count += 1
        continue
    else:
        count = 0
    # rgb.clear()
    # draw_text()  # draw after last refresh, so slower but kinda async.
    old_stat = stat
    if stat == 0:  # generator
        r = urequests.post("https://dashboard.eventinfra.org/api/datasources/proxy/1/render",
                           data='target=infra.ACT_PWR_1_generator_tot_kva&target=infra.ACT_PWR_2_generator_tot_kva&target=infra.ACT_PWR_3_generator_tot_kva&from=-3min&until=now&format=json&maxDataPoints=768')
        if r.status_code == 200:
            # rgb.clear()
            rgb.pixel((0, 255, 0), (REFRESH_RATE, 7))  # green for new data
            try:
                l = [str(int(i['datapoints'][-1][0])) for i in r.json()]
            except:
                rgb.pixel((255, 0, 0), (REFRESH_RATE, 7))  # red for error
                continue
            draw_text()
        else:
            rgb.pixel((255, 0, 0), (REFRESH_RATE, 7))  # red for error
            rgb.text('E {}'.format(r.status_code))
    elif stat == 1:  # up/down link
        r = urequests.post("https://dashboard.eventinfra.org/api/datasources/proxy/1/render",
                           data='target=scale(scaleToSeconds(nonNegativeDerivative(net.kvm2.snmp.if_octets-eth3_300.tx),1),8)&target=scale(scaleToSeconds(nonNegativeDerivative(net.kvm2.snmp.if_octets-eth3_300.rx),1),8)&from=-5min&until=now&format=json&maxDataPoints=768')
        if r.status_code == 200:
            rgb.pixel((0, 255, 0), (REFRESH_RATE, 7))  # green for new data
            try:
                l = [str(int(i['datapoints'][-1][0] / 1e6)) for i in r.json()]
            except:
                rgb.pixel((255, 0, 0), (REFRESH_RATE, 7))  # red for error
                continue
            draw_text()
        else:
            rgb.pixel((255, 0, 0), (REFRESH_RATE, 7))  # red for error
            rgb.text('E {}'.format(r.status_code))
