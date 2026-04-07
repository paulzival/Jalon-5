import pyb
import sensor
import image
import time

# Initialisation du capteur de caméra
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor.skip_frames(time=2000)

# Définir une fenêtre de capture (x, y, width, height)
sensor.set_windowing((0, 50, 320,190 ))  # Garde une bande centrale de 140 pixels de haut


# Seuils LAB pour la balle rouge
thresholdsGreenBall = ((0, 100, -128, -19, -119, 127))

# Configuration des broches et timers pour les moteurs
p4 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p5 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p7 = pyb.Pin('P7', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p8 = pyb.Pin('P8', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

tim12 = pyb.Timer(2, freq=1000)
tim2X = pyb.Timer(4, freq=1000)

# Configuration des canaux PWM pour les moteurs
M11 = tim12.channel(3, pyb.Timer.PWM, pin=pyb.Pin('P5'), pulse_width_percent=0)
M12 = tim12.channel(4, pyb.Timer.PWM, pin=pyb.Pin('P4'), pulse_width_percent=0)
M2X = tim2X.channel(1, pyb.Timer.PWM, pin=pyb.Pin('P7'), pulse_width_percent=0)

tim12.freq(100)
tim2X.freq(100)

def cmd_moteur(Rapport_AV_AR, Vit_R_Dr, Vit_R_Ga):
    M2X.pulse_width_percent(Rapport_AV_AR)
    M11.pulse_width_percent(Vit_R_Dr)
    M12.pulse_width_percent(Vit_R_Ga)

def follow_ball(blob_cx, blob_cy, img_width):
    # Calcul de delta pour la position horizontale
    delta = 160 - blob_cx

    # Ajustement de la vitesse en fonction de la distance verticale (Cy)
    speed_adjust_cy = 60 - (blob_cy // 12)

    # Ajustement de la vitesse en fonction de delta (position horizontale)
    speed_adjust_delta_right = 60 + (delta // 4)
    speed_adjust_delta_left = 60 - (delta // 4)

    # Limiter les vitesses pour éviter les valeurs extrêmes
    Vit_R_Dr = min(max(0, speed_adjust_delta_right + speed_adjust_cy), 100)
    Vit_R_Ga = min(max(0, speed_adjust_delta_left + speed_adjust_cy), 100)

    cmd_moteur(0, Vit_R_Dr, Vit_R_Ga)

ledRed = pyb.LED(3)
ledGreen = pyb.LED(2)

clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    # Recherche des blobs correspondant à la balle rouge
    blobs = img.find_blobs([thresholdsGreenBall], area_threshold=40, merge=False)

    if blobs:
        blobs.sort(key=lambda b: b.area(), reverse=True)
        largest_blob = blobs[0]
        img.draw_rectangle(largest_blob.rect(), color=(0, 255, 0))
        img.draw_cross(largest_blob.cx(), largest_blob.cy(), color=(0, 255, 0))

        # Suivre la balle avec ajustement de vitesse
        follow_ball(largest_blob.cx(), largest_blob.cy(), img.width())
    else:
        # Arrêter les moteurs si la balle n'est plus détectée
        cmd_moteur(0, 0, 50)

    # Allumer la LED verte si une balle rouge est détectée


    pyb.delay(10)  # Réduction du délai pour une réactivité maximale
    print(clock.fps())
