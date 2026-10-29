# Liste des composants à souder à la main (Hand-Soldering Guide)

Toutes les petites pièces CMS délicates (93 composants dont DAC PCM5122 TSSOP-28, Buck TPS54302, Switch vidéo TS5A3159, ampli PAM8406, transistors et 70+ résistances/condensateurs 0603/0805) sont assemblées par JLCPCB.

Voici les composants restants à commander et souder vous-même avec fer basique + flux :

---

## 1. Connecteurs (Traversants / THT - Très facile)
| Repère | Description | Empreinte / Pas | Référence recommandée |
| :--- | :--- | :--- | :--- |
| **J1** | Connecteur femelle 40 broches Raspberry Pi | 2x20 broches, pas 2.54 mm, hauteur standard HAT | Embase femelle 2x20 pin GPIO Pi |
| **J_CAR_3P** | Connecteur Alim / I-Bus E39 (GND, 12V, IBUS) | TE MQS 3 broches ou bornier à vis 2.54/3.5mm ou fils directs | TE 953442-1 ou soudure directe des 3 fils CD-Changer |
| **J_CAR_6P** | Connecteur Audio E39 (L+, L-, R+, R-) | TE MQS 6 broches ou fils directs blindés | TE 966871-1 ou soudure directe du câble audio CD |
| **J_DVR, J_REV** | Borniers à vis 2 broches (Caméra DVR 12V + Signal Recul 12V) | Bornier Phoenix Contact pas 5.08 mm (MKDS 1,5/2-5.08) | Bornier à vis 2P 5.08mm standard (bleu ou vert) |
| **J_FAN** | Connecteur Ventilateur 5V | JST-XH 2 broches pas 2.50 mm mâle | JST B2B-XH-A |
| **J_MIC, J_TV_TRIG** | Entrée micro + Déclencheur TV broche 17 | Barrette sécable mâle 2 broches, pas 2.54 mm | Pin header 1x2 2.54mm |
| **J_TEL** | Port I/O Téléphonie TCU (DB25) | Barrette sécable mâle 6 broches, pas 2.54 mm | Pin header 1x6 2.54mm |
| **J_PI_VID** | Entrée Vidéo composite Pi (TRRS) | Barrette sécable mâle 4 broches, pas 2.54 mm | Pin header 1x4 2.54mm |
| **J_RCA_CAM, J_RCA_TV**| Prises RCA Caméra de recul + Sortie TV Tuner | Embase RCA femelle horizontale PCB ou connecteur SMA | Connecteur RCA PCB jaune/blanc |

---

## 2. Composants Puissance & Protection (Gros CMS 2 pattes - Très facile)
| Repère | Valeur / Fonction | Boîtier | Référence / MPN |
| :--- | :--- | :--- | :--- |
| **F1** | Fusible rapide 5A | 1206 (3216) | Littelfuse 0468005.WR ou fusible CMS 1206 5A |
| **D1** | Diode TVS protection 18V (Surtension auto) | SMB (DO-214AA) | SMBJ18A (2 grosses pattes larges) |
| **D2** | Diode Schottky anti-inversion 40V 3A | SMC (DO-214AB) | SS34 (2 grosses pattes larges) |
| **L1** | Inductance de puissance 10 µH (Buck 5V) | 7.3 x 7.3 mm (Würth WE-PD 7345) | Inductance blindée 10µH > 3A (2 larges pads) |
| **K1** | Relais DPDT commutation audio 5V | CMS Gull-Wing Omron G6K | Omron G6K-2F-Y-5VDC |
| **FL1** | Choke mode commun alim (Optionnel) | ACM7060 | ACM70V-701-2PL *(ou 2 ponts de soudure si omis)* |

---

## 3. Interrupteurs (Très facile)
| Repère | Fonction | Boîtier | Référence |
| :--- | :--- | :--- | :--- |
| **SW_BENCH** | Switch Mode Banc (simulation contact 12V) | Switch à glissière SPST pas 2.54 mm | Slide switch SPST 2.54 mm |
| **SW_DVR_CFG**| DIP-switch 3 positions (seuil coupure dashcam) | DIP-3 switch pas 2.54 mm | DIP switch 3P standard |

---

## 4. Circuits Intégrés & Petits Passifs (Avec flux + panne fine)
| Repère | Valeur / Description | Boîtier | Méthode & Astuce |
| :--- | :--- | :--- | :--- |
| **U2** | TH3122.4 (Transceiver I-Bus) | SOIC-16 (pas 1.27 mm) | Pas standard espacé. Poser du flux, pointer 1 patte, puis souder les rangées. |
| **U6** | TLV3012 (Comparateur alerte batterie dashcam) | SOT-23-6 | Petit boîtier 6 pattes. Du flux sur les pistes, fer propre. |
| **D12** | Diode Zener 4.7V | SOT-23 | BZX84C4V7 |
| **R4** | Résistance 13.3 kΩ 1% (Réglage 5.1V Buck) | 0603 | R_0603 13.3k 1% (ou 13k + 300R) |
| **R31, R32, R33** | 118kΩ, 115kΩ, 113kΩ (Seuils DIP dashcam) | 0603 | R_0603 1% (permettent de régler 11.8V, 12.0V, 12.2V) |

---

## Astuce de soudure au fer basique :
1. **Flux indispensable** : déposer une goutte de flux liquide ou gel sur l'empreinte avant d'approcher le fer.
2. **Soudure au tirage** : pour U2 (SOIC-16), charger légèrement la panne d'étain et glisser le long des broches. Le flux évite tout pont.
3. **Connecteurs en dernier** : souder d'abord U2, U6 et les passives, puis L1/K1/diodes, et terminer par les connecteurs THT hauts.
