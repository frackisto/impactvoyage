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

# Équipements : (nom FR, nom EN, icône Lucide) — « Climatisation » et « Internet illimité »
# existent déjà (studio de l'agence) et sont réutilisés.
AMENITIES = [
    ("Climatisation", "Air conditioning", "air-vent"),
    ("Internet illimité", "Unlimited internet", "wifi"),
    ("Piscine", "Swimming pool", "waves"),
    ("Restaurant", "Restaurant", "utensils"),
    ("Parking", "Parking", "square-parking"),
    ("Navette aéroport", "Airport shuttle", "bus"),
    ("Petit-déjeuner inclus", "Breakfast included", "coffee"),
    ("Vue sur mer", "Sea view", "sunset"),
    ("Cuisine équipée", "Equipped kitchen", "cooking-pot"),
]

# Chambres : (nom FR, nom EN, description FR, description EN, capacité, nombre, prix/nuit)
HOTELS = [
    {
        "slug": "hotel-lagune-plateau",
        "destination": "abidjan",
        "type": "HOTEL", "stars": 4,
        "name": "Hôtel Lagune Plateau",
        "short": ("Au cœur du Plateau, vue sur la lagune Ébrié et piscine sur le toit.",
                  "In the heart of the Plateau, Ébrié lagoon view and rooftop pool."),
        "description": (
            "Idéal pour un séjour d'affaires ou une escale à Abidjan : chambres climatisées, "
            "restaurant ivoirien et international, piscine sur le toit et navette aéroport.",
            "Ideal for a business trip or a stopover in Abidjan: air-conditioned rooms, Ivorian "
            "and international restaurant, rooftop pool and airport shuttle.",
        ),
        "address": "Boulevard de la République, Plateau, Abidjan",
        "amenities": ["Climatisation", "Internet illimité", "Piscine", "Restaurant", "Parking", "Navette aéroport"],
        "rooms": [
            ("Chambre standard", "Standard room", "Lit double, bureau, salle de douche.", "Double bed, desk, shower room.", 2, 5, "55000"),
            ("Chambre supérieure", "Superior room", "Vue sur la lagune, balcon.", "Lagoon view, balcony.", 2, 3, "75000"),
            ("Suite familiale", "Family suite", "Deux chambres communicantes et un salon.", "Two connecting rooms and a lounge.", 4, 2, "120000"),
        ],
        "cover": None, "gallery": [], "featured": True,
    },
    {
        "slug": "bassam-beach-hotel",
        "destination": "mondoukou",
        "type": "HOTEL", "stars": 3,
        "name": "Bassam Beach Hôtel",
        "short": ("Bungalows les pieds dans le sable, entre Grand-Bassam et Mondoukou.",
                  "Bungalows right on the sand, between Grand-Bassam and Mondoukou."),
        "description": (
            "Un hôtel simple et chaleureux au bord de l'océan, parfait pour un week-end : "
            "restaurant de poissons et fruits de mer, transats et paillotes.",
            "A simple and friendly hotel by the ocean, perfect for a weekend: fish and seafood "
            "restaurant, sunbeds and straw huts.",
        ),
        "address": "Route de Mondoukou, Grand-Bassam",
        "amenities": ["Climatisation", "Restaurant", "Parking", "Vue sur mer", "Petit-déjeuner inclus"],
        "rooms": [
            ("Bungalow vue mer", "Sea-view bungalow", "Terrasse privée face à l'océan.", "Private terrace facing the ocean.", 3, 6, "40000"),
        ],
        "cover": "mondoukou.jpg", "gallery": [], "featured": False,
    },
    {
        "slug": "marina-view-dubai",
        "destination": "dubai",
        "type": "HOTEL", "stars": 4,
        "name": "Marina View Hotel Dubaï",
        "short": ("Hôtel 4 étoiles face à la marina, à deux pas du métro.",
                  "4-star hotel facing the marina, a short walk from the metro."),
        "description": (
            "Chambres spacieuses avec vue sur la marina, piscine extérieure et petit-déjeuner "
            "buffet. L'hôtel de nos circuits à Dubaï.",
            "Spacious rooms overlooking the marina, outdoor pool and buffet breakfast. The hotel "
            "used for our Dubai tours.",
        ),
        "address": "Dubai Marina, Dubaï, Émirats arabes unis",
        "amenities": ["Climatisation", "Internet illimité", "Piscine", "Restaurant", "Petit-déjeuner inclus"],
        "rooms": [
            ("Chambre double", "Double room", "Vue sur la ville.", "City view.", 2, 10, "95000"),
            ("Chambre familiale", "Family room", "Vue sur la marina, deux grands lits.", "Marina view, two large beds.", 4, 4, "150000"),
        ],
        "cover": "hero-dubai-marina.jpg", "gallery": ["dubai-burj-al-arab.jpg", "dubai-mall.jpg"], "featured": True,
    },
    {
        "slug": "appartements-cocody",
        "destination": "abidjan",
        "type": "APARTMENT", "stars": None,
        "name": "Appartements Cocody Riviera",
        "short": ("Appartements meublés de 2 pièces, pour les séjours de plusieurs semaines.",
                  "Furnished 2-room apartments for stays of several weeks."),
        "description": (
            "Appartements indépendants avec cuisine équipée, dans un quartier calme de Cocody. "
            "Ménage hebdomadaire et gardiennage 24 h/24.",
            "Independent apartments with an equipped kitchen, in a quiet area of Cocody. Weekly "
            "cleaning and 24-hour security.",
        ),
        "address": "Riviera 3, Cocody, Abidjan",
        "amenities": ["Climatisation", "Internet illimité", "Cuisine équipée", "Parking"],
        "rooms": [
            ("Appartement 2 pièces", "2-room apartment", "Chambre, salon, cuisine.", "Bedroom, lounge, kitchen.", 3, 2, "50000"),
        ],
        "cover": None, "gallery": [], "featured": False,
    },
    {
        "slug": "campement-lagunaire-grand-lahou",
        "destination": "grand-lahou",
        "type": "PARTNER", "stars": None,
        "name": "Campement lagunaire de Grand-Lahou",
        "short": ("Hébergement partenaire en cases traditionnelles au bord de la lagune.",
                  "Partner accommodation in traditional huts by the lagoon."),
        "description": (
            "Notre partenaire pour les sorties de groupe à Grand-Lahou : cases rafraîchies, "
            "repas locaux et excursions en pirogue.",
            "Our partner for group outings to Grand-Lahou: cool huts, local meals and canoe trips.",
        ),
        "address": "Lagune Tagba, Grand-Lahou",
        "amenities": ["Restaurant", "Parking"],
        "rooms": [
            ("Case double", "Double hut", "Deux lits simples, ventilateur.", "Two single beds, fan.", 2, 8, "25000"),
        ],
        "cover": "grand-lahou-nuit.jpg", "gallery": [], "featured": False,
    },
]

RESIDENCES = [
    {
        "slug": "villa-familiale-grand-bassam",
        "destination": "mondoukou",
        "name": "Villa familiale à Grand-Bassam",
        "short": ("Villa de 3 chambres avec jardin, à 5 minutes de la plage.",
                  "3-bedroom villa with a garden, 5 minutes from the beach."),
        "description": (
            "Grande villa meublée pour les familles et les groupes d'amis : trois chambres "
            "climatisées, salon, cuisine équipée, jardin et parking.",
            "Large furnished villa for families and groups of friends: three air-conditioned "
            "bedrooms, lounge, equipped kitchen, garden and parking.",
        ),
        "address": "Quartier France, Grand-Bassam",
        "rooms": 3, "capacity": 6, "price": "85000",
        "amenities": ["Climatisation", "Internet illimité", "Cuisine équipée", "Parking"],
        "services": ("Ménage à l'arrivée\nLinge de maison fourni\nGardien",
                     "Cleaning on arrival\nBed linen provided\nCaretaker"),
        "conditions": ("Caution de 100 000 F CFA. Arrivée à partir de 14 h, départ avant 12 h.",
                       "Deposit of 100,000 CFA francs. Check-in from 2 pm, check-out before noon."),
    },
]

# Véhicules de démonstration (les 4 véhicules réels de l'agence restent non publiés tant que
# leurs fiches ne sont pas complétées). Plaques fictives « DEMO-… », jamais affichées.
VEHICLES = [
    {
        "slug": "demo-suzuki-vitara", "brand": "Suzuki", "model": "Vitara", "category": "SUV",
        "year": 2023, "seats": 5, "transmission": "AUTOMATIQUE", "fuel": "ESSENCE", "price": "35000",
        "features": ["GPS", "Bluetooth", "Caméra de recul", "Régulateur de vitesse"],
        "description": (
            "SUV compact, confortable en ville comme sur les routes de l'intérieur du pays. "
            "Kilométrage illimité à Abidjan.",
            "Compact SUV, comfortable in town and on inland roads. Unlimited mileage in Abidjan.",
        ),
        "cover": "suzuki-vitara.jpg", "gallery": ["suzuki-vitara-avant.jpg"], "featured": True,
    },
    {
        "slug": "demo-suzuki-ertiga", "brand": "Suzuki", "model": "Ertiga", "category": "MINIBUS",
        "year": 2022, "seats": 7, "transmission": "MANUELLE", "fuel": "ESSENCE", "price": "40000",
        "features": ["7 places", "Grand coffre", "Bluetooth"],
        "description": (
            "Monospace 7 places, idéal pour les familles et les transferts aéroport.",
            "7-seater MPV, ideal for families and airport transfers.",
        ),
        "cover": "suzuki-ertiga.jpg", "gallery": [], "featured": False,
    },
    {
        "slug": "demo-suzuki-grand-vitara", "brand": "Suzuki", "model": "Grand Vitara", "category": "4X4",
        "year": 2021, "seats": 5, "transmission": "MANUELLE", "fuel": "ESSENCE", "price": "45000",
        "features": ["4 roues motrices", "Bluetooth"],
        "description": (
            "4x4 robuste pour les pistes et les excursions hors des grands axes.",
            "Sturdy 4x4 for dirt roads and trips off the main routes.",
        ),
        "cover": "suzuki-grand-vitara.jpg", "gallery": [], "featured": False,
    },
    {
        "slug": "demo-changan-cs35", "brand": "Changan", "model": "CS35 Plus", "category": "SUV",
        "year": 2023, "seats": 5, "transmission": "AUTOMATIQUE", "fuel": "ESSENCE", "price": "30000",
        "features": ["Écran tactile", "Caméra de recul", "Bluetooth"],
        "description": (
            "SUV récent et économique, parfait pour les déplacements professionnels.",
            "Recent and economical SUV, perfect for business trips.",
        ),
        "cover": "changan-avant.jpg", "gallery": ["changan-arriere.jpg"], "featured": True,
    },
    {
        "slug": "demo-toyota-hiace", "brand": "Toyota", "model": "Hiace", "category": "MINIBUS",
        "year": 2020, "seats": 15, "transmission": "MANUELLE", "fuel": "DIESEL", "price": "90000",
        "features": ["15 places", "Climatisation arrière"],
        "description": (
            "Minibus 15 places avec chauffeur sur demande, pour les sorties de groupe et les séminaires.",
            "15-seat minibus, driver available on request, for group outings and seminars.",
        ),
        "cover": None, "gallery": [], "featured": False,
    },
    {
        "slug": "demo-toyota-land-cruiser", "brand": "Toyota", "model": "Land Cruiser Prado", "category": "LUXE",
        "year": 2022, "seats": 7, "transmission": "AUTOMATIQUE", "fuel": "DIESEL", "price": "120000",
        "features": ["Sièges cuir", "GPS", "4 roues motrices", "Toit ouvrant"],
        "description": (
            "4x4 haut de gamme pour vos déplacements VIP et vos événements.",
            "Premium 4x4 for VIP transport and events.",
        ),
        "cover": None, "gallery": [], "featured": False,
    },
]

ACTIVITY_CATEGORIES = [
    ("excursions", "Excursions", "Excursions"),
    ("visites-culturelles", "Visites culturelles", "Cultural visits"),
    ("loisirs-nautiques", "Loisirs nautiques", "Water activities"),
    ("aventure", "Aventure", "Adventure"),
]

ACTIVITIES = [
    {
        "slug": "balade-pirogue-lagune-tagba", "destination": "grand-lahou", "category": "loisirs-nautiques",
        "title": ("Balade en pirogue sur la lagune Tagba", "Canoe ride on the Tagba lagoon"),
        "short": ("Deux heures au fil de l'eau jusqu'à l'embouchure du Bandama.",
                  "Two hours on the water to the mouth of the Bandama river."),
        "description": (
            "Un piroguier du village vous emmène à travers la mangrove jusqu'à l'embouchure du "
            "Bandama, où la lagune rencontre l'océan. Gilets de sauvetage fournis.",
            "A village boatman takes you through the mangrove to the mouth of the Bandama, where "
            "the lagoon meets the ocean. Life jackets provided.",
        ),
        "hours": "2", "price": "10000", "max": 12, "cover": "grand-lahou-visite.jpg",
    },
    {
        "slug": "visite-guidee-grand-bassam", "destination": "mondoukou", "category": "visites-culturelles",
        "title": ("Visite guidée de Grand-Bassam historique", "Guided tour of historic Grand-Bassam"),
        "short": ("Le quartier France, patrimoine mondial de l'UNESCO, avec un guide local.",
                  "The Quartier France, a UNESCO World Heritage site, with a local guide."),
        "description": (
            "Découvrez la première capitale de la Côte d'Ivoire : maisons coloniales, musée "
            "national du costume, phare et village artisanal.",
            "Discover the first capital of Côte d'Ivoire: colonial houses, national costume "
            "museum, lighthouse and craft village.",
        ),
        "hours": "3", "price": "15000", "max": 20, "cover": None,
    },
    {
        "slug": "tour-abidjan-a-velo", "destination": "abidjan", "category": "excursions",
        "title": ("Abidjan à vélo", "Abidjan by bike"),
        "short": ("Le Plateau et les berges de la lagune à vélo, tôt le matin.",
                  "The Plateau and the lagoon shores by bike, early in the morning."),
        "description": (
            "Une balade à vélo encadrée, de la cathédrale Saint-Paul aux berges de la lagune "
            "Ébrié, avant la chaleur. Vélos et casques fournis.",
            "A guided bike ride from St Paul's Cathedral to the shores of the Ébrié lagoon, "
            "before the heat. Bikes and helmets provided.",
        ),
        "hours": "3", "price": "12000", "max": 10, "cover": None,
    },
    {
        "slug": "safari-desert-dubai", "destination": "dubai", "category": "aventure",
        "title": ("Safari dans le désert en 4x4", "4x4 desert safari"),
        "short": ("Dunes en 4x4, coucher de soleil et dîner-spectacle dans un camp bédouin.",
                  "Dunes by 4x4, sunset and dinner show in a Bedouin camp."),
        "description": (
            "Départ de votre hôtel en milieu d'après-midi, descente des dunes en 4x4, balade à "
            "dos de chameau, puis dîner barbecue et spectacle sous les étoiles.",
            "Hotel pick-up mid-afternoon, 4x4 dune bashing, camel ride, then barbecue dinner and "
            "show under the stars.",
        ),
        "hours": "6", "price": "65000", "max": 30, "cover": None,
    },
    {
        "slug": "burj-khalifa-niveau-124", "destination": "dubai", "category": "visites-culturelles",
        "title": ("Burj Khalifa, niveau 124", "Burj Khalifa, level 124"),
        "short": ("La vue depuis la plus haute tour du monde, billet coupe-file.",
                  "The view from the world's tallest tower, skip-the-line ticket."),
        "description": (
            "Montée en ascenseur ultra-rapide jusqu'aux terrasses d'observation du 124e étage, "
            "avec une vue à 360° sur Dubaï.",
            "Ultra-fast lift up to the observation decks on the 124th floor, with a 360° view "
            "over Dubai.",
        ),
        "hours": "1.5", "price": "45000", "max": None, "cover": "dubai-burj-khalifa.jpg",
    },
    {
        "slug": "diner-croisiere-marina-dubai", "destination": "dubai", "category": "loisirs-nautiques",
        "title": ("Dîner-croisière dans la marina", "Marina dinner cruise"),
        "short": ("Deux heures en dhow traditionnel, buffet international.",
                  "Two hours on a traditional dhow, international buffet."),
        "description": (
            "Embarquez sur un dhow illuminé pour découvrir les gratte-ciel de la marina de nuit, "
            "autour d'un buffet international.",
            "Board an illuminated dhow to see the marina skyscrapers by night, with an "
            "international buffet.",
        ),
        "hours": "2.5", "price": "55000", "max": 40, "cover": "hero-dubai-marina.jpg",
    },
]

# Activités incluses dans un circuit : (circuit, [activités]).
TOUR_ACTIVITIES = [
    ("dubai-ville-des-records", ["burj-khalifa-niveau-124", "safari-desert-dubai", "diner-croisiere-marina-dubai"]),
]

# Inscriptions confirmées fictives : (activité, dans N jours, participants).
ACTIVITY_BOOKINGS = [("visite-guidee-grand-bassam", 10, 18)]

# Événements passés de démonstration (le contenu réel de l'agence en compte déjà un).
EVENTS = [
    {
        "slug": "voyage-de-groupe-dubai-2026", "category": "VOYAGE_GROUPE", "destination": "dubai",
        "title": ("Voyage de groupe à Dubaï", "Group trip to Dubai"),
        "short": ("25 voyageurs à la découverte de Dubaï, du désert à la marina.",
                  "25 travellers discovering Dubai, from the desert to the marina."),
        "description": (
            "Une semaine à Dubaï pour un groupe de 25 voyageurs : Burj Khalifa, safari dans le "
            "désert, souks et croisière dans la marina. Vols, visas et hôtel organisés par l'agence.",
            "A week in Dubai for a group of 25 travellers: Burj Khalifa, desert safari, souks and "
            "marina cruise. Flights, visas and hotel arranged by the agency.",
        ),
        "date": (2026, 3, 14), "end": (2026, 3, 20), "location": "Dubaï, Émirats arabes unis",
        "participants": 25, "cover": "dubai-burj-al-arab.jpg", "gallery": ["dubai-mall.jpg", "hero-dubai-marina.jpg"],
    },
    {
        "slug": "journee-culturelle-grand-bassam", "category": "CULTUREL", "destination": "mondoukou",
        "title": ("Journée culturelle à Grand-Bassam", "Cultural day in Grand-Bassam"),
        "short": ("Visite du quartier France et déjeuner au bord de l'océan.",
                  "Visit of the Quartier France and lunch by the ocean."),
        "description": (
            "Une journée pour 40 participants : visite guidée du quartier historique, musée du "
            "costume, puis détente et déjeuner à Mondoukou.",
            "A day for 40 participants: guided tour of the historic district, costume museum, then "
            "relaxation and lunch in Mondoukou.",
        ),
        "date": (2025, 11, 22), "end": None, "location": "Grand-Bassam, Côte d'Ivoire",
        "participants": 40, "cover": "mondoukou.jpg", "gallery": [],
    },
]

# Réservation confirmée fictive (calendrier de disponibilité) : (véhicule, dans N jours, durée).
VEHICLE_BOOKINGS = [("demo-suzuki-vitara", 5, 4)]

# Demandes de devis fictives, avec référence et jeton fixes : la page de suivi
# /devis/{reference}?token=… est ainsi consultable (et testée) après chaque chargement.
QUOTES = [
    {
        "reference": "DV-DEMO-000001",
        "token": "7e57d3a0-0000-4000-8000-000000000001",
        "status": "DEVIS_ENVOYE",
        "first_name": "Awa", "last_name": "Koné", "phone": "+2250700000001",
        "destination": "dubai", "tour": "dubai-ville-des-records",
        "departure_in_days": 42, "nights": 5, "adults": 2, "children": 1,
        "services": ["CIRCUIT", "VOL", "VISA"],
        "comments": "Voyage en famille, première fois à Dubaï.",
        "proposal": {
            "amount": "2350000",
            "message": (
                "Bonjour Awa,\n\nVoici notre proposition pour votre séjour en famille à Dubaï : "
                "vols aller-retour depuis Abidjan, visas, 5 nuits en hôtel 4 étoiles avec "
                "petit-déjeuner, safari dans le désert et montée à la Burj Khalifa.\n\n"
                "Le tarif enfant est appliqué pour votre fils."
            ),
            "valid_in_days": 14,
        },
    },
    {
        "reference": "DV-DEMO-000002",
        "token": "7e57d3a0-0000-4000-8000-000000000002",
        "status": "EN_COURS",
        "first_name": "Serge", "last_name": "Traoré", "phone": "+2250700000002",
        "destination": "chine", "tour": None,
        "departure_in_days": 90, "nights": 10, "adults": 4, "children": 0,
        "services": ["VOL", "HEBERGEMENT", "VISA"],
        "comments": "Voyage d'affaires à Canton pour la foire.",
        "proposal": None,
    },
]

HOTEL_REVIEWS = [
    ("marina-view-dubai", "Fatou B.", 5, "Chambre impeccable et vue magnifique sur la marina."),
    ("hotel-lagune-plateau", "Jean-Marc A.", 4, "Très bien situé pour mes rendez-vous au Plateau."),
]


def price(value):
    return Decimal(value) if value is not None else None
