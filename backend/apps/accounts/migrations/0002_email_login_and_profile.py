import apps.accounts.models
import apps.core.files
import apps.core.validators
import django.core.validators
from django.db import migrations, models


def prepare_existing_users(apps, schema_editor):
    """
    Avant de passer à la connexion par email et de supprimer `username` :
    - conserve le nom d'utilisateur dans le prénom s'il est vide ;
    - garantit un email unique et en minuscules (unicité ajoutée plus bas) ;
    - aligne rôle et is_staff sur la nouvelle règle (le rôle fait foi).
    """
    User = apps.get_model("accounts", "User")
    for user in User.objects.all():
        if not user.first_name:
            user.first_name = user.username
        user.email = (user.email or f"{user.username}@compte-a-completer.invalid").lower()
        if user.is_superuser:
            user.role = "SUPER_ADMIN"
        user.is_staff = user.role != "CLIENT"
        user.save(update_fields=["first_name", "email", "role", "is_staff"])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(prepare_existing_users, migrations.RunPython.noop),
        migrations.AlterModelOptions(
            name='user',
            options={'ordering': ['email'], 'verbose_name': 'utilisateur'},
        ),
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', apps.accounts.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name='user',
            name='username',
        ),
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, upload_to=apps.core.files.UploadTo(), validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']), apps.core.validators.MaxFileSizeValidator(5242880)]),
        ),
        migrations.AddField(
            model_name='user',
            name='country_code',
            field=models.CharField(blank=True, max_length=2, verbose_name='pays (ISO 3166-1)'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_verified',
            field=models.BooleanField(default=False, verbose_name='email vérifié'),
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=30, verbose_name='téléphone'),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_currency',
            field=models.CharField(choices=[('XOF', 'Franc CFA (FCFA)'), ('EUR', 'Euro'), ('USD', 'Dollar américain'), ('GBP', 'Livre sterling')], default='XOF', max_length=3, verbose_name='devise préférée'),
        ),
        migrations.AddField(
            model_name='user',
            name='preferred_language',
            field=models.CharField(default='fr', max_length=5, verbose_name='langue préférée'),
        ),
        migrations.AddField(
            model_name='user',
            name='whatsapp',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='adresse email'),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('SUPER_ADMIN', 'Super administrateur'), ('ADMIN', 'Administrateur'), ('AGENT', 'Agent'), ('COMMERCIAL', 'Commercial'), ('GESTIONNAIRE', 'Gestionnaire'), ('CLIENT', 'Client')], db_index=True, default='CLIENT', max_length=20, verbose_name='rôle'),
        ),
    ]
