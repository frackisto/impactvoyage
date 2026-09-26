"""
Données de DÉMONSTRATION (fictives mais cohérentes : villes réelles, prix en FCFA),
chargées par `python manage.py seed_demo` — architecture § 14.

Elles s'ajoutent au contenu réel de l'agence (agency_content.py) pour montrer et
tester les pages du site. Interdites en production (réglage DEMO_DATA_ALLOWED) ;
`seed_demo --reset` les supprime.

Les dates de départ sont relatives au jour du chargement (en semaines).
"""
from decimal import Decimal

# Programme : (titre FR, titre EN, description FR, description EN)
# Départs : (dans N semaines, places, places déjà réservées, prix spécifique ou None)
TOURS = [
    {
        "slug": "escapade-lagunaire-grand-lahou",
        "destination": "grand-lahou",
        "scope": "NATIONAL",
        "theme": "voyages-groupes",
        "title": ("Escapade lagunaire à Grand-Lahou", "Lagoon getaway in Grand-Lahou"),
        "short": (
            "Deux jours entre lagune, embouchure du Bandama et plages sauvages.",
            "Two days between lagoon, Bandama river mouth and wild beaches.",
        ),
        "description": (
            "Au départ d'Abidjan, cap sur Grand-Lahou, ancienne cité coloniale posée entre la "
            "lagune Tagba et l'océan. Balade en pirogue, visite des vestiges de la vieille ville "
            "et après-midi de détente sur la plage.\n\n"
            "Un week-end convivial, idéal entre amis, en famille ou en groupe d'entreprise.",
            "Leaving from Abidjan, head to Grand-Lahou, a former colonial town between the "
            "Tagba lagoon and the ocean. Canoe ride, visit of the old town ruins and a relaxing "
            "afternoon on the beach.\n\n"
            "A friendly weekend, ideal with friends, family or a company group.",
        ),
        "duration": 2, "price": "45000", "min": 10, "max": 40,
        "departure_points": ("Abidjan, Yopougon (agence)\nAbidjan, Plateau", "Abidjan, Yopougon (agency)\nAbidjan, Plateau"),
        "transport": ("Car climatisé aller-retour.", "Air-conditioned coach, return trip."),
        "accommodation": ("1 nuit en hôtel au bord de la lagune (chambre double).", "1 night in a lagoon-side hotel (double room)."),
        "inclusions": (
            "Transport aller-retour\nHébergement 1 nuit\nPetit-déjeuner et déjeuners\nBalade en pirogue\nGuide accompagnateur",
            "Return transport\n1 night accommodation\nBreakfast and lunches\nCanoe ride\nAccompanying guide",
        ),
        "exclusions": ("Dîner du samedi\nBoissons\nDépenses personnelles", "Saturday dinner\nDrinks\nPersonal expenses"),
        "conditions": (
            "Acompte de 50 % à la réservation, solde 7 jours avant le départ. Départ garanti à partir de 10 voyageurs.",
            "50% deposit when booking, balance 7 days before departure. Departure guaranteed from 10 travellers.",
        ),
        "days": [
            ("Abidjan – Grand-Lahou", "Abidjan – Grand-Lahou",
             "Départ à 6 h 30, arrivée en fin de matinée. Déjeuner de poisson braisé, balade en pirogue jusqu'à l'embouchure du Bandama.",
             "Departure at 6:30 am, arrival late morning. Grilled fish lunch, canoe ride to the Bandama river mouth."),
            ("Vieille ville et retour", "Old town and return",
             "Visite des vestiges de l'ancien Grand-Lahou, temps libre à la plage, retour à Abidjan en fin d'après-midi.",
             "Visit of the old Grand-Lahou ruins, free time on the beach, return to Abidjan in the late afternoon."),
        ],
        "cover": "grand-lahou-visite.jpg", "gallery": ["grand-lahou-groupe.jpg", "grand-lahou-nuit.jpg"],
        "departures": [(3, 40, 12, None), (7, 40, 0, None)],
        "featured": True,
    },
    {
        "slug": "week-end-balneaire-mondoukou",
        "destination": "mondoukou",
        "scope": "NATIONAL",
        "theme": "voyages-d-aventure",
        "title": ("Week-end balnéaire à Mondoukou", "Beach weekend in Mondoukou"),
        "short": (
            "Sable fin, cocotiers et fruits de mer à deux pas de Grand-Bassam.",
            "Fine sand, coconut trees and seafood near Grand-Bassam.",
        ),
        "description": (
            "Mondoukou, petit village de pêcheurs près de Grand-Bassam, offre des plages "
            "préservées. Au programme : baignade, jeux de plage, visite du quartier historique "
            "de Grand-Bassam (patrimoine mondial de l'UNESCO) et soirée autour d'un feu.",
            "Mondoukou, a small fishing village near Grand-Bassam, has unspoilt beaches. On the "
            "programme: swimming, beach games, a visit of Grand-Bassam's historic quarter "
            "(UNESCO World Heritage) and an evening around a bonfire.",
        ),
        "duration": 2, "price": "35000", "min": 8, "max": 30,
        "departure_points": ("Abidjan, Yopougon (agence)", "Abidjan, Yopougon (agency)"),
        "transport": ("Minicar climatisé.", "Air-conditioned minibus."),
        "accommodation": ("1 nuit en bungalow en bord de mer.", "1 night in a beachfront bungalow."),
        "inclusions": (
            "Transport\nBungalow 1 nuit\nPension complète\nVisite guidée de Grand-Bassam",
            "Transport\n1 night in a bungalow\nFull board\nGuided tour of Grand-Bassam",
        ),
        "exclusions": ("Boissons\nActivités nautiques", "Drinks\nWater sports"),
        "conditions": ("Acompte de 50 % à la réservation.", "50% deposit when booking."),
        "days": [
            ("Grand-Bassam historique", "Historic Grand-Bassam",
             "Visite du quartier France et du musée national du costume, puis installation à Mondoukou.",
             "Visit of the Quartier France and the national costume museum, then check-in in Mondoukou."),
            ("Journée plage", "Beach day",
             "Matinée libre, déjeuner de fruits de mer, retour à Abidjan vers 17 h.",
             "Free morning, seafood lunch, return to Abidjan around 5 pm."),
        ],
        "cover": "mondoukou.jpg", "gallery": [],
        "departures": [(5, 30, 0, None)],
        "featured": False,
    },
    {
        "slug": "abidjan-culture-et-saveurs",
        "destination": "abidjan",
        "scope": "NATIONAL",
        "theme": "voyages-culturels",
        "title": ("Abidjan, culture et saveurs", "Abidjan, culture and flavours"),
        "short": (
            "Une journée pour découvrir le Plateau, la cathédrale Saint-Paul et les maquis de Treichville.",
            "One day to discover the Plateau, St Paul's Cathedral and the maquis of Treichville.",
        ),
        "description": (
            "Découvrez la « Perle des lagunes » avec un guide local : les tours du Plateau, la "
            "cathédrale Saint-Paul, le marché de Treichville et un déjeuner dans un maquis réputé.",
            "Discover the 'Pearl of the Lagoons' with a local guide: the Plateau towers, St Paul's "
            "Cathedral, the Treichville market and lunch in a renowned maquis.",
        ),
        "duration": 1, "price": "25000", "min": 2, "max": 15,
        "departure_points": ("Abidjan, Plateau", "Abidjan, Plateau"),
        "transport": ("Véhicule climatisé avec chauffeur.", "Air-conditioned vehicle with driver."),
        "accommodation": ("", ""),
        "inclusions": ("Transport\nGuide\nDéjeuner", "Transport\nGuide\nLunch"),
        "exclusions": ("Boissons", "Drinks"),
        "conditions": ("Paiement à la réservation.", "Payment when booking."),
        "days": [
            ("Abidjan en une journée", "Abidjan in a day",
             "Plateau et cathédrale le matin, déjeuner à Treichville, marché et galerie d'art l'après-midi.",
             "Plateau and cathedral in the morning, lunch in Treichville, market and art gallery in the afternoon."),
        ],
        "cover": None, "gallery": [],
        # Presque complet : affiche « plus que 3 places ».
        "departures": [(2, 15, 12, None), (4, 15, 0, "22000")],
        "featured": False,
    },
    {
        "slug": "dubai-ville-des-records",
        "destination": "dubai",
        "scope": "INTERNATIONAL",
        "theme": "voyage-de-luxe",
        "title": ("Dubaï, la ville de tous les records", "Dubai, the city of records"),
        "short": (
            "6 jours entre Burj Khalifa, désert et marina, vols depuis Abidjan inclus.",
            "6 days between Burj Khalifa, desert and marina, flights from Abidjan included.",
        ),
        "description": (
            "Montez au sommet de la Burj Khalifa, flânez dans le Dubai Mall et les souks de l'or "
            "et des épices, vivez un safari en 4x4 dans le désert avec dîner sous les étoiles, "
            "puis profitez d'une croisière en dhow dans la marina.\n\n"
            "Vols, visa et transferts sont organisés par l'agence.",
            "Go to the top of the Burj Khalifa, stroll through the Dubai Mall and the gold and "
            "spice souks, enjoy a 4x4 desert safari with dinner under the stars, then a dhow "
            "cruise in the marina.\n\n"
            "Flights, visa and transfers are arranged by the agency.",
        ),
        "duration": 6, "price": "850000", "min": 2, "max": 20,
        "departure_points": ("Abidjan, aéroport Félix-Houphouët-Boigny", "Abidjan, Félix-Houphouët-Boigny airport"),
        "transport": ("Vols aller-retour Abidjan – Dubaï en classe économique, transferts en minibus.",
                      "Return flights Abidjan – Dubai in economy class, minibus transfers."),
        "accommodation": ("5 nuits en hôtel 4 étoiles, quartier de la marina.", "5 nights in a 4-star hotel, marina district."),
        "inclusions": (
            "Vols aller-retour\nVisa touristique\nHôtel 4 étoiles 5 nuits avec petit-déjeuner\nSafari dans le désert avec dîner\nEntrée Burj Khalifa (niveau 124)\nCroisière en dhow",
            "Return flights\nTourist visa\n4-star hotel, 5 nights with breakfast\nDesert safari with dinner\nBurj Khalifa ticket (level 124)\nDhow cruise",
        ),
        "exclusions": ("Déjeuners et dîners libres\nAssurance voyage (en option)\nTaxe touristique locale",
                       "Free lunches and dinners\nTravel insurance (optional)\nLocal tourism tax"),
        "conditions": (
            "Passeport valide 6 mois après le retour. Acompte de 40 % à la réservation, solde 30 jours avant le départ.",
            "Passport valid 6 months after return. 40% deposit when booking, balance 30 days before departure.",
        ),
        "days": [
            ("Envol pour Dubaï", "Flight to Dubai",
             "Vol de nuit depuis Abidjan, accueil à l'aéroport et transfert à l'hôtel.",
             "Overnight flight from Abidjan, airport welcome and hotel transfer."),
            ("Downtown et Burj Khalifa", "Downtown and Burj Khalifa",
             "Dubai Mall, montée à la Burj Khalifa au coucher du soleil, spectacle de la fontaine.",
             "Dubai Mall, Burj Khalifa at sunset, fountain show."),
            ("Vieux Dubaï et souks", "Old Dubai and souks",
             "Quartier Al Fahidi, traversée de la crique en abra, souks de l'or et des épices.",
             "Al Fahidi district, creek crossing by abra, gold and spice souks."),
            ("Safari dans le désert", "Desert safari",
             "Matinée libre, safari en 4x4 l'après-midi, dîner-spectacle dans un camp bédouin.",
             "Free morning, 4x4 safari in the afternoon, dinner show in a Bedouin camp."),
            ("Marina et Palm Jumeirah", "Marina and Palm Jumeirah",
             "Vue sur le Burj Al Arab, Palm Jumeirah, croisière en dhow le soir.",
             "View of the Burj Al Arab, Palm Jumeirah, dhow cruise in the evening."),
            ("Retour", "Return",
             "Temps libre pour les derniers achats, transfert à l'aéroport et vol retour.",
             "Free time for last purchases, airport transfer and return flight."),
        ],
        "cover": "dubai-burj-khalifa.jpg", "gallery": ["dubai-burj-al-arab.jpg", "dubai-mall.jpg", "hero-dubai-marina.jpg"],
        "departures": [(6, 20, 5, None), (10, 20, 0, "895000"), (16, 20, 0, None)],
        "featured": True,
    },
    {
        "slug": "chine-imperiale-pekin-shanghai",
        "destination": "chine",
        "scope": "INTERNATIONAL",
        "theme": "voyages-culturels",
        "title": ("Chine impériale : Pékin et Shanghai", "Imperial China: Beijing and Shanghai"),
        "short": (
            "10 jours de la Cité interdite à la Grande Muraille, puis Shanghai en train rapide.",
            "10 days from the Forbidden City to the Great Wall, then Shanghai by high-speed train.",
        ),
        "description": (
            "Un grand voyage culturel : la Cité interdite, le temple du Ciel, la Grande Muraille à "
            "Mutianyu, puis le train à grande vitesse vers Shanghai, entre le Bund, la vieille "
            "ville et les jardins Yuyuan.",
            "A great cultural journey: the Forbidden City, the Temple of Heaven, the Great Wall at "
            "Mutianyu, then the high-speed train to Shanghai, between the Bund, the old town and "
            "the Yuyuan gardens.",
        ),
        "duration": 10, "price": "1950000", "min": 4, "max": 16,
        "departure_points": ("Abidjan, aéroport Félix-Houphouët-Boigny", "Abidjan, Félix-Houphouët-Boigny airport"),
        "transport": ("Vols internationaux avec escale, train rapide Pékin – Shanghai.",
                      "International flights with a stopover, Beijing – Shanghai high-speed train."),
        "accommodation": ("8 nuits en hôtels 4 étoiles.", "8 nights in 4-star hotels."),
        "inclusions": (
            "Vols internationaux\nAssistance visa\nHôtels 4 étoiles avec petit-déjeuner\nGuide francophone\nEntrées des sites",
            "International flights\nVisa assistance\n4-star hotels with breakfast\nFrench-speaking guide\nSite tickets",
        ),
        "exclusions": ("Frais de visa consulaires\nDîners", "Consular visa fees\nDinners"),
        "conditions": ("Acompte de 40 % à la réservation.", "40% deposit when booking."),
        "days": [
            ("Départ d'Abidjan", "Departure from Abidjan", "Vol avec escale vers Pékin.", "Flight with a stopover to Beijing."),
            ("Arrivée à Pékin", "Arrival in Beijing", "Accueil, transfert et repos.", "Welcome, transfer and rest."),
            ("Cité interdite", "Forbidden City", "Place Tian'anmen et Cité interdite.", "Tiananmen Square and the Forbidden City."),
            ("Grande Muraille", "Great Wall", "Randonnée sur la muraille à Mutianyu.", "Walk on the wall at Mutianyu."),
            ("Temple du Ciel", "Temple of Heaven", "Temple du Ciel et hutongs en cyclo-pousse.", "Temple of Heaven and hutongs by rickshaw."),
            ("Train pour Shanghai", "Train to Shanghai", "Train à grande vitesse, soirée sur le Bund.", "High-speed train, evening on the Bund."),
            ("Shanghai", "Shanghai", "Vieille ville et jardins Yuyuan.", "Old town and Yuyuan gardens."),
            ("Zhujiajiao", "Zhujiajiao", "Village sur l'eau aux portes de Shanghai.", "Water village near Shanghai."),
            ("Journée libre", "Free day", "Shopping sur Nanjing Road.", "Shopping on Nanjing Road."),
            ("Retour", "Return", "Vol retour vers Abidjan.", "Return flight to Abidjan."),
        ],
        "cover": "chine.jpg", "gallery": [],
        "departures": [(12, 16, 3, None)],
        "featured": False,
    },
    {
        "slug": "lune-de-miel-a-dubai",
        "destination": "dubai",
        "scope": "INTERNATIONAL",
        "theme": "voyage-de-noce",
        "is_custom": True,
        "title": ("Lune de miel à Dubaï", "Honeymoon in Dubai"),
        "short": (
            "Un séjour sur mesure pour deux, aux dates de votre choix.",
            "A tailor-made stay for two, on the dates of your choice.",
        ),
        "description": (
            "Hôtel de luxe, dîner en bateau, spa et désert : nous composons votre voyage de noces "
            "selon vos envies et votre budget.",
            "Luxury hotel, dinner cruise, spa and desert: we design your honeymoon according to "
            "your wishes and budget.",
        ),
        "duration": 7, "price": "1400000", "min": 2, "max": 2,
        "departure_points": ("Abidjan", "Abidjan"),
        "transport": ("Vols et transferts privés.", "Flights and private transfers."),
        "accommodation": ("Hôtel 5 étoiles, chambre avec vue.", "5-star hotel, room with a view."),
        "inclusions": ("Vols\nHôtel 5 étoiles\nDîner-croisière\nSoin au spa", "Flights\n5-star hotel\nDinner cruise\nSpa treatment"),
        "exclusions": ("Assurance voyage", "Travel insurance"),
        "conditions": ("Devis personnalisé.", "Personalised quote."),
        "days": [],
        "cover": "hero-dubai-marina.jpg", "gallery": [],
        "departures": [],
        "featured": False,
    },
]

# Avis validés : (circuit, auteur, note, commentaire)
TOUR_REVIEWS = [
    ("dubai-ville-des-records", "Aïcha K.", 5, "Organisation parfaite du visa jusqu'au retour. Le safari était inoubliable !"),
    ("dubai-ville-des-records", "Serge T.", 4, "Très bon séjour, hôtel bien situé. Un peu fatigant avec le vol de nuit."),
    ("escapade-lagunaire-grand-lahou", "Mariam D.", 5, "Super ambiance de groupe et guide très sympathique."),
]

DEMO_EMAIL = "demo@example.com"


def price(value):
    return Decimal(value) if value is not None else None
