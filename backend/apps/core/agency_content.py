"""
Contenu réel de l'agence, repris de l'ancien site https://impact-voyage.com
(septembre 2026) et chargé par `python manage.py load_agency_content`.

Seules les informations publiées par l'agence sont reprises ; le contenu de
démonstration du thème WordPress (destinations « Cox's Bazar », hôtels de
Dhaka, articles en anglais...) a été écarté. Les champs inconnus sont marqués
« À COMPLÉTER » et les fiches incomplètes restent non publiées.

Les descriptions de Chine, Abidjan, Grand-Lahou et Mondoukou (absentes de l'ancien
site) ont été rédigées pour démarrer : à relire par l'agence.

Les photos sont dans apps/core/fixtures/agency/.
"""
from datetime import date
from decimal import Decimal

SITE_SETTINGS: dict[str, object] = {
    "agency_name": "Impact Voyage et Logistique SARLP",
    "slogan_fr": "Voyagez, Rêvez, Explorez.",
    "slogan_en": "Travel, Dream, Explore.",
    "hero_subtitle_fr": (
        "Agence de voyage, de tourisme et d'événementiel à Abidjan : billetterie, "
        "circuits, hébergements, visas et location de véhicules."
    ),
    "hero_subtitle_en": (
        "Travel, tourism and events agency in Abidjan: air tickets, tours, "
        "accommodation, visas and car rental."
    ),
    "hero_image": "hero-dubai-marina.jpg",
    "phone": "+225 27 23 22 88 57",
    "whatsapp": "+225 01 52 15 35 91",
    "email": "informations@impact-voyage.com",
    "address": (
        "Yopougon Maroc, Immeuble Djakounda, près du marché de l'Antenne, "
        "Abidjan, Côte d'Ivoire — BP V 34 Abidjan"
    ),
    "opening_hours_fr": "Lundi – vendredi : 8 h 00 – 18 h 00\nSamedi – dimanche : fermé",
    "opening_hours_en": "Monday – Friday: 8:00 am – 6:00 pm\nSaturday – Sunday: closed",
    # Les liens du site actuel pointaient vers la racine des réseaux (facebook.com...) :
    # à renseigner avec les vraies pages de l'agence.
    "social_links": {},
    "latitude": None,
    "longitude": None,
    "about_content_fr": (
        "IMPACT VOYAGE ET LOGISTIQUE SARLP est une agence de voyage, de tourisme et "
        "d'événementiel gérée par une équipe de jeunes professionnels qualifiés, encadrés "
        "par des cadres expérimentés.\n\n"
        "Nous transformons vos rêves d'évasion en réalité : vacances en famille, voyages "
        "d'affaires ou aventures exotiques, nous concevons des itinéraires personnalisés "
        "qui répondent à vos attentes et à votre budget."
    ),
    "about_content_en": (
        "IMPACT VOYAGE ET LOGISTIQUE SARLP is a travel, tourism and events agency run by a "
        "team of young qualified professionals, supervised by experienced managers.\n\n"
        "We turn your travel dreams into reality: family holidays, business trips or exotic "
        "adventures, we design tailor-made itineraries that match your expectations and budget."
    ),
}

TOUR_THEMES = [
    ("voyages-groupes", "Voyages groupés", "Group trips"),
    ("voyage-de-luxe", "Voyage de luxe", "Luxury travel"),
    ("voyages-culturels", "Voyages culturels", "Cultural trips"),
    ("voyage-de-noce", "Voyage de noce", "Honeymoon"),
    ("voyages-historiques", "Voyages historiques", "Historical trips"),
    ("vie-sauvage-et-safari", "Vie sauvage & safari", "Wildlife & safari"),
    ("voyages-d-aventure", "Voyages d'aventure", "Adventure trips"),
]

# (slug, titre FR, titre EN, description FR, description EN, icône Lucide, prestation du devis, tarifs)
# Tarif : (libellé FR, libellé EN, prix FCFA, unité FR, unité EN)
SERVICES = [
    ("conseil-et-planification", "Conseil et planification de voyages", "Travel advice and planning",
     "Nous vous conseillons pour choisir votre destination, votre itinéraire et votre hébergement "
     "en fonction de vos envies et de votre budget.",
     "We help you choose your destination, itinerary and accommodation according to your wishes "
     "and budget.", "compass", "CONSEIL", []),
    ("billets-d-avion", "Réservation de billets d'avion", "Flight booking",
     "Billets d'avion, de train, de bus et de croisière : nous recherchons pour vous les meilleures "
     "options de prix et d'horaires.",
     "Plane, train, bus and cruise tickets: we find the best fares and schedules for you.",
     "plane", "VOL", []),
    ("hebergement", "Réservation d'hébergement", "Accommodation booking",
     "Hôtels, villas, appartements et autres hébergements, y compris des séjours tout inclus.",
     "Hotels, villas, apartments and other accommodation, including all-inclusive stays.",
     "hotel", "HEBERGEMENT", []),
    ("circuits-et-excursions", "Organisation de circuits et excursions", "Tours and excursions",
     "Circuits touristiques, excursions guidées et activités locales, en individuel ou en groupe.",
     "Sightseeing tours, guided excursions and local activities, for individuals or groups.",
     "map", "CIRCUIT", []),
    ("services-personnalises", "Services personnalisés", "Tailor-made services",
     "Voyages d'affaires, séjours de luxe ou besoins particuliers : des voyages sur mesure.",
     "Business trips, luxury stays or special requirements: tailor-made travel.",
     "sparkles", "CONSEIL", []),
    ("assurance-voyage", "Assurance voyage", "Travel insurance",
     "Une assurance pour couvrir les imprévus : annulation, interruption de voyage et urgences "
     "médicales. Couverture Afrique, Asie et espace Schengen.",
     "Insurance covering the unexpected: cancellation, trip interruption and medical emergencies. "
     "Coverage for Africa, Asia and the Schengen area.",
     "shield-check", "ASSURANCE", [
         ("1 semaine", "1 week", "14000", "", ""),
         ("2 semaines", "2 weeks", "18000", "", ""),
         ("1 mois", "1 month", "26000", "", ""),
     ]),
    ("visa-et-formalites", "Services de visa et formalités", "Visa and travel formalities",
     "Nous préparons avec vous les documents nécessaires aux voyages internationaux : demandes de "
     "visa, prise de rendez-vous et autres formalités administratives.",
     "We prepare the documents required for international travel with you: visa applications, "
     "appointments and other paperwork.",
     "stamp", "VISA", [
         ("Prise de rendez-vous — France", "Appointment booking — France", "20000", "", ""),
         ("Prise de rendez-vous — Belgique", "Appointment booking — Belgium", "26000", "", ""),
         ("Prise de rendez-vous — Allemagne", "Appointment booking — Germany", "5000", "", ""),
         ("Prise de rendez-vous — Espagne", "Appointment booking — Spain", "5000", "", ""),
         ("Remplissage du formulaire en ligne", "Online form filling", "10000", "", ""),
         ("Réservation d'hôtel (dossier visa)", "Hotel reservation (visa file)", "15000", "", ""),
         ("Attestation de réservation de billet", "Flight reservation certificate", "10000", "", ""),
     ]),
    ("location-de-voitures", "Location de voitures", "Car rental",
     "Des véhicules confortables pour vous déplacer librement, avec ou sans chauffeur.",
     "Comfortable vehicles to get around freely, with or without a driver.",
     "car", "LOCATION_VEHICULE", []),
    ("residences-meublees", "Location de résidences meublées", "Furnished apartments",
     "Des studios meublés confortables et sécurisés à Abidjan, avec réduction pour les longs séjours.",
     "Comfortable, secure furnished studios in Abidjan, with discounts for long stays.",
     "house", "HEBERGEMENT", [
         ("Studio meublé — Yopougon Maroc", "Furnished studio — Yopougon Maroc", "20000",
          "par nuit", "per night"),
     ]),
    ("changements-et-annulations", "Gestion des changements et annulations", "Changes and cancellations",
     "Nous gérons les changements d'itinéraire et les annulations de réservation, avec les "
     "politiques de remboursement ou de modification applicables.",
     "We handle itinerary changes and booking cancellations, with the applicable refund or "
     "change policies.", "refresh-ccw", "CONSEIL", []),
    ("conseils-pratiques-et-culturels", "Conseils pratiques et culturels", "Practical and cultural advice",
     "Coutumes locales, conseils de sécurité, monnaie, climat : tout pour profiter pleinement de "
     "votre destination.",
     "Local customs, safety tips, currency, climate: everything to make the most of your destination.",
     "book-open", "CONSEIL", []),
    ("evenementiel", "Organisation d'événements", "Event planning",
     "Sorties, voyages de groupe, voyages d'immersion et événements professionnels ou privés.",
     "Outings, group trips, immersion trips and corporate or private events.",
     "party-popper", "EVENEMENT", []),
]

# (slug, nom FR, nom EN, continent, pays ISO, ville FR, ville EN, accroche FR, accroche EN,
#  description FR, description EN, image principale, galerie, mise en avant)
DESTINATIONS = [
    ("dubai", "Dubaï", "Dubai", "MOYEN_ORIENT", "AE", "Dubaï", "Dubai",
     "Shopping de luxe, architecture ultramoderne et vie nocturne animée.",
     "Luxury shopping, ultramodern architecture and lively nightlife.",
     "Dubaï est une ville et un émirat des Émirats arabes unis réputé pour son shopping de luxe, "
     "son architecture ultramoderne et sa vie nocturne animée. La Burj Khalifa, tour de 830 mètres "
     "de haut, domine le paysage urbain parsemé de gratte-ciel. À son pied, la fontaine de Dubaï "
     "présente des jets et des lumières synchronisés avec de la musique.\n\n"
     "Sans être la capitale des Émirats arabes unis, Dubaï en est devenue la ville la plus connue, "
     "grâce à ses projets touristiques comme l'hôtel Burj-al-Arab, les Palm Islands, l'archipel "
     "The World, la Dubaï Marina ou encore la Burj Khalifa, l'immeuble le plus haut du monde.",
     "Dubai is a city and emirate in the United Arab Emirates known for luxury shopping, "
     "ultramodern architecture and a lively nightlife scene. Burj Khalifa, an 830-metre tower, "
     "dominates the skyscraper-filled skyline. At its foot, the Dubai Fountain features jets and "
     "lights choreographed to music.\n\n"
     "Although not the capital of the UAE, Dubai has become its best-known city thanks to "
     "landmark projects such as the Burj Al Arab hotel, the Palm Islands, The World archipelago, "
     "Dubai Marina and Burj Khalifa, the tallest building in the world.",
     "hero-dubai-marina.jpg", ["dubai-burj-khalifa.jpg", "dubai-burj-al-arab.jpg", "dubai-mall.jpg"],
     True),
    ("france", "France", "France", "EUROPE", "FR", "Paris", "Paris",
     "Villes médiévales, villages alpins, plages et gastronomie raffinée.",
     "Medieval towns, Alpine villages, beaches and fine cuisine.",
     "La France, pays de l'Europe occidentale, compte des villes médiévales, des villages alpins et "
     "des plages. Paris, sa capitale, est célèbre pour ses maisons de mode, ses musées d'art "
     "classique, dont le Louvre, et ses monuments comme la tour Eiffel. Le pays est également "
     "réputé pour ses vins et sa cuisine raffinée. Les grottes de Lascaux, le théâtre romain de "
     "Lyon et l'immense château de Versailles témoignent de sa riche histoire.",
     "France, in Western Europe, has medieval cities, Alpine villages and beaches. Paris, its "
     "capital, is famous for its fashion houses, classical art museums including the Louvre, and "
     "monuments like the Eiffel Tower. The country is also renowned for its wines and fine "
     "cuisine. The Lascaux caves, Lyon's Roman theatre and the vast Palace of Versailles bear "
     "witness to its rich history.",
     None, [], True),
    ("chine", "Chine", "China", "ASIE", "CN", "", "",
     "Des métropoles futuristes aux temples millénaires.",
     "From futuristic cities to ancient temples.",
     "Pays aux mille facettes, la Chine associe métropoles futuristes comme Shanghai, sites "
     "millénaires comme la Grande Muraille et la Cité interdite de Pékin, et paysages "
     "spectaculaires. L'agence vous accompagne pour l'obtention de votre e-visa.",
     "A country of many facets, China combines futuristic cities such as Shanghai, ancient sites "
     "such as the Great Wall and Beijing's Forbidden City, and spectacular landscapes. The agency "
     "helps you obtain your e-visa.",
     "chine.jpg", [], True),
    ("abidjan", "Abidjan", "Abidjan", "AFRIQUE", "CI", "Abidjan", "Abidjan",
     "La capitale économique de la Côte d'Ivoire, siège de l'agence.",
     "Côte d'Ivoire's economic capital, home of the agency.",
     "Capitale économique de la Côte d'Ivoire, Abidjan s'étend autour de la lagune Ébrié : "
     "quartier d'affaires du Plateau, parc national du Banco, plages et vie nocturne animée.",
     "Côte d'Ivoire's economic capital, Abidjan stretches around the Ébrié lagoon: the Plateau "
     "business district, Banco National Park, beaches and a lively nightlife.",
     None, [], False),
    ("grand-lahou", "Grand-Lahou", "Grand-Lahou", "AFRIQUE", "CI", "Grand-Lahou", "Grand-Lahou",
     "Destination de nos sorties de groupe sur le littoral ivoirien.",
     "Destination of our group outings on the Ivorian coast.",
     "Ville côtière située à environ 150 km à l'ouest d'Abidjan, à l'embouchure du fleuve "
     "Bandama, Grand-Lahou séduit par ses plages, sa lagune et le parc national d'Azagny tout proche.",
     "A coastal town about 150 km west of Abidjan at the mouth of the Bandama River, Grand-Lahou "
     "charms visitors with its beaches, its lagoon and the nearby Azagny National Park.",
     "grand-lahou-groupe.jpg", ["grand-lahou-visite.jpg"], True),
    ("mondoukou", "Mondoukou", "Mondoukou", "AFRIQUE", "CI", "Grand-Bassam", "Grand-Bassam",
     "Plages de sable fin et cocotiers près de Grand-Bassam.",
     "Fine sandy beaches and coconut palms near Grand-Bassam.",
     "Village balnéaire proche de Grand-Bassam, ville historique inscrite au patrimoine mondial "
     "de l'UNESCO, Mondoukou offre des plages bordées de cocotiers à une heure d'Abidjan.",
     "A seaside village near Grand-Bassam, a historic town listed as a UNESCO World Heritage "
     "Site, Mondoukou offers palm-fringed beaches an hour from Abidjan.",
     "mondoukou.jpg", [], False),
]

# E-visas proposés (nationalité : Côte d'Ivoire). Tarifs du site actuel, en FCFA.
# (code pays, slug pays, type FR, type EN, frais)
VISAS = [
    ("AE", "dubai", "E-visa (électronique)", "E-visa (electronic)", "100000"),
    ("CN", "chine", "E-visa (électronique)", "E-visa (electronic)", "240000"),
    ("FR", "france", "E-visa (électronique)", "E-visa (electronic)", "20000"),
    ("DE", "allemagne", "E-visa (électronique)", "E-visa (electronic)", "20000"),
    ("BE", "belgique", "E-visa (électronique)", "E-visa (electronic)", "5000"),
    ("ES", "espagne", "E-visa (électronique)", "E-visa (electronic)", None),  # tarif non publié
]
VISA_DESCRIPTION = (
    "Accompagnement de votre demande : constitution du dossier, remplissage du formulaire en "
    "ligne, prise de rendez-vous et suivi. Tarif indiqué : frais de service de l'agence.",
    "Assistance with your application: file preparation, online form filling, appointment "
    "booking and follow-up. Price shown: agency service fee.",
)

RESIDENCE = {
    "slug": "studio-meuble-yopougon-maroc",
    "name": "Studio meublé — Yopougon Maroc",
    "destination": "abidjan",
    "address": "Yopougon Maroc, Abidjan",
    "rooms_count": 1,
    "capacity": 2,
    "base_price": Decimal("20000"),
    "short_description_fr": "Confort, sécurité et propreté garantis.",
    "short_description_en": "Comfort, security and cleanliness guaranteed.",
    "description_fr": (
        "Studio meublé climatisé avec connexion internet illimitée, IPTV (plus de 10 000 chaînes) "
        "et lit deux places avec matelas orthopédique. Confort, sécurité et propreté garantis."
    ),
    "description_en": (
        "Air-conditioned furnished studio with unlimited internet, IPTV (over 10,000 channels) "
        "and a double bed with an orthopaedic mattress. Comfort, security and cleanliness guaranteed."
    ),
    "conditions_fr": "Réduction pour les longs séjours. Réservation : 07 47 20 43 00 – 01 43 20 44 01.",
    "conditions_en": "Discount for long stays. Booking: +225 07 47 20 43 00 – +225 01 43 20 44 01.",
    "amenities": [("Climatisation", "Air conditioning", "air-vent"),
                  ("Internet illimité", "Unlimited internet", "wifi"),
                  ("IPTV", "IPTV", "tv"),
                  ("Lit deux places", "Double bed", "bed-double")],
    "cover": "studio-salon.jpg",
    "gallery": ["studio-chambre.jpg", "studio-cuisine.jpg", "studio-douche.jpg", "studio-sanitaires.jpg"],
}

# Véhicules du site actuel : prix, année, immatriculation, places, boîte et carburant
# n'étaient pas publiés → fiches non publiées, à compléter avant mise en ligne.
# (slug, marque, modèle, catégorie, places, image principale, galerie)
VEHICLES = [
    ("changan-blanc", "Changan", "SUV blanc", "SUV", 5, "changan-avant.jpg", ["changan-arriere.jpg"]),
    ("suzuki-ertiga", "Suzuki", "Ertiga", "MINIBUS", 7, "suzuki-ertiga.jpg", []),
    ("suzuki-vitara", "Suzuki", "Vitara", "SUV", 5, "suzuki-vitara.jpg", ["suzuki-vitara-avant.jpg"]),
    ("suzuki-grand-vitara", "Suzuki", "Grand Vitara", "SUV", 5, "suzuki-grand-vitara.jpg", []),
]

# Activités événementielles publiées sur le site actuel (dates = dates de publication).
EVENTS = [
    ("sortie-a-grand-lahou", "Sortie à Grand-Lahou", "Outing to Grand-Lahou", "EXCURSION",
     date(2025, 2, 16), "Grand-Lahou, Côte d'Ivoire", "grand-lahou",
     "Sortie de groupe organisée par Impact Voyage à Grand-Lahou.",
     "Group outing organised by Impact Voyage in Grand-Lahou.",
     "grand-lahou-groupe.jpg", ["grand-lahou-visite.jpg", "grand-lahou-nuit.jpg"]),
    ("voyage-d-immersion", "Voyage d'immersion", "Immersion trip", "VOYAGE_GROUPE",
     date(2026, 5, 11), "À COMPLÉTER", None,
     "Voyage d'immersion organisé par Impact Voyage. À COMPLÉTER : destination et programme.",
     "Immersion trip organised by Impact Voyage. TO COMPLETE: destination and programme.",
     None, []),
]
