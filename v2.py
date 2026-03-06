import sensor, image, time, pyb
from pyb import LED, Pin

# Initialisation du capteur de caméra
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor.skip_frames(time=200)

# Seuils LAB pour la balle rouge (inchangés)
thresholdsRedBall = (0, 100, 47, 87, 16, 68)

# Configuration des broches pour les moteurs
p4 = pyb.Pin('P4', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p5 = pyb.Pin('P5', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p7 = pyb.Pin('P7', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
p8 = pyb.Pin('P8', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

# capteur de fourche
Capt_fourche = Pin('P8', Pin.IN)   # Capteur de fourche

# Configuration des timers et canaux PWM
tim12 = pyb.Timer(2, freq=100)
tim2X = pyb.Timer(4, freq=100)

# Canaux PWM pour les moteurs
M11 = tim12.channel(3, pyb.Timer.PWM, pin=p5)  # Moteur droit avant
M12 = tim12.channel(4, pyb.Timer.PWM, pin=p4)  # Moteur droit arrière
M2X = tim2X.channel(1, pyb.Timer.PWM, pin=p7)  # Moteur de direction

tim12.freq(100)
tim2X.freq(100)

# Variables globales pour le balayage et l'état
scanning = False
etat = 0  # 0: recherche, 1: suivi, 2: balle dans fourche
scan_direction = 1
def cmd_moteur(rapport_av_ar, vit_droite, vit_gauche):
    """Commande les moteurs avec les vitesses spécifiées."""
    M2X.pulse_width_percent(rapport_av_ar)
    M11.pulse_width_percent(vit_droite)
    M12.pulse_width_percent(vit_gauche)

def follow_ball(blob_cx, blob_cy, img_width):
    """Suivre la balle en ajustant la vitesse des moteurs en fonction de la distance et de la position horizontale."""
    global scanning

    # Calcul de l'erreur horizontale (centre de l'image : img_width // 2)
    centre_x = img_width // 2
    delta_x = centre_x - blob_cx

    # Calcul de la distance verticale (plus blob_cy est grand, plus la balle est proche)
    distance_verticale = blob_cy

    # Ajustement de la vitesse en fonction de la distance verticale
    # Plus la balle est proche (blob_cy grand), plus la vitesse est réduite
    vitesse_base = 100 - (distance_verticale // 8)

    # Limiter la vitesse de base entre 20 et 100
    vitesse_base = min(max(20, vitesse_base), 100)

    # Ajustement de la vitesse en fonction de l'erreur horizontale (delta_x)
    # Si la balle est à droite (delta_x négatif), accélérer la roue gauche et ralentir la droite
    # Si la balle est à gauche (delta_x positif), accélérer la roue droite et ralentir la gauche
    ajustement_rotation = abs(delta_x) // 6

    if delta_x < 0:  # balle à droite
        vit_droite = max(20, vitesse_base - ajustement_rotation)
        vit_gauche = min(100, vitesse_base + ajustement_rotation)
    elif delta_x > 0:  # balle à gauche
        vit_droite = min(100, vitesse_base + ajustement_rotation)
        vit_gauche = max(20, vitesse_base - ajustement_rotation)
    else:  # balle centrée
        vit_droite = vit_gauche = vitesse_base

    # Envoyer les commandes aux moteurs
    cmd_moteur(0, vit_droite, vit_gauche)

    
def scan_for_ball():
    """Balayer l'environnement pour chercher la balle."""
    global scan_direction
    if scan_direction == 1:
        cmd_moteur(0, 40, 20)  # Tourner à droite
    else:
        cmd_moteur(0, 20, 40)  # Tourner à gauche


def scan_for_ball():    #cherche la balle
    if scanning:
        cmd_moteur(0, 60, 0)  # Tourner à droite

def stop_moteurs(): # arrét des moteur
    cmd_moteur(0, 0, 0)


clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    # Définir une zone d'intérêt (ROI) pour limiter la détection à une certaine partie de l'image
    roi = (0, 50, img.width(), 200)  # (x, y, width, height) - ajuste ces valeurs selon ton besoin

    # Vérifier si la balle est dans la fourche
    if Capt_fourche.value() == 1:
        etat = 2  # Balle dans la fourche
        print('Balle dans la fourche')
        stop_moteurs()
    else:

        print('Balle pas là')
        etat = 0  # Retour à l'état de recherche si aucune balle dans la fourche

    # Gestion des états
    if etat == 2:
        stop_moteurs()
    else:
        # Recherche des blobs correspondant à la balle rouge dans la ROI
        blobs = img.find_blobs([thresholdsRedBall], area_threshold=50, merge=False, roi=roi)

        if blobs:
            # Trouver le plus grand blob (balle)
            blobs.sort(key=lambda b: b.area(), reverse=True)
            largest_blob = blobs[0]
            img.draw_rectangle(largest_blob.rect(), color=(0, 255, 0))
            img.draw_cross(largest_blob.cx(), largest_blob.cy(), color=(0, 255, 0))
            etat = 1  # Suivi de la balle
            follow_ball(largest_blob.cx(), largest_blob.cy(), img.width())
        else:
            etat = 0  # Recherche de la balle
            # Activer le balayage si aucune balle n'est détectée
            if not scanning:
                scanning = True
                scan_direction *= -1  # Changer de direction

            scan_for_ball()

    pyb.delay(10)
    print(clock.fps())
