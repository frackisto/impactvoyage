from django.contrib.postgres.operations import (
    BtreeGistExtension,
    TrigramExtension,
    UnaccentExtension,
)
from django.db import migrations


class Migration(migrations.Migration):
    """
    Extensions PostgreSQL (architecture § 7.1) :
    - btree_gist : contrainte d'exclusion des locations de véhicules (bookings) ;
    - pg_trgm et unaccent : recherche globale tolérante aux fautes et aux accents.
    """

    operations = [
        BtreeGistExtension(),
        TrigramExtension(),
        UnaccentExtension(),
    ]
