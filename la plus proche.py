import pyb
import sensor
import image
import time

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor.skip_frames(time=2000)

# Seuils pour la balle rouge
Ball_rouge = (0, 100, 47, 87, 16, 68)

led_bleu = pyb.LED(3)
led_vert = pyb.LED(2)
horloge = time.clock()

while True:
    horloge.tick()
    img = sensor.snapshot()

    # Recherche des blobs correspondant à la balle rouge
    blobs = img.find_blobs([Ball_rouge], area_threshold=50, merge=False)

    # trouver la balle la plus proche
    if blobs:
        # Trier les blobs par taille
        blobs.sort(key=lambda b: b.area(), reverse=True)
        # Sélectionner le blob le plus grand (le plus proche)
        largest_blob = blobs[0]
        img.draw_rectangle(largest_blob.rect(), color=(0, 255, 0))
        img.draw_cross(largest_blob.cx(), largest_blob.cy(), color=(0, 255, 0))

    # Allume la LED verte si une balle rouge est détectée
    if blobs:
        led_vert.on()
        led_bleu.off()
    else:
        led_vert.off()
        led_bleu.on()

    pyb.delay(60)
    print(horloge.fps())
