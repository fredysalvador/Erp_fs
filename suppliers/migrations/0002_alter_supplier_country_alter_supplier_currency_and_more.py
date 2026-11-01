
import django.db.models.deletion
from django.db import migrations, models


def convert_supplier_data(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    Country = apps.get_model("core", "Country")
    Currency = apps.get_model("core", "Currency")
    Status = apps.get_model("core", "Status")

    db = schema_editor.connection.alias

    countries_data = {
        "honduras": ("Honduras", "HN"),
        "united states": ("United States", "US"),
    }

    countries = {}

    for key, (name, code) in countries_data.items():
        country, _ = Country.objects.using(db).get_or_create(
            code=code,
            defaults={"name": name, "is_active": True}
        )
        countries[key] = country

    currencies_data = {
        "hnl": ("Honduran Lempira", "HNL", "L"),
        "usd": ("US Dollar", "USD", "$"),
    }

    currencies = {}

    for key, (name, code, symbol) in currencies_data.items():
        currency, _ = Currency.objects.using(db).get_or_create(
            code=code,
            defaults={
                "name": name,
                "symbol": symbol,
                "is_active": True
            }
        )
        currencies[key] = currency

    for supplier in Supplier.objects.using(db).all():
        country_key = supplier.country.strip().lower()
        currency_key = supplier.currency.strip().lower()
        status_name = supplier.status.strip()

        if country_key not in countries:
            raise ValueError(f"Unknown country: {supplier.country}")

        if currency_key not in currencies:
            raise ValueError(f"Unknown currency: {supplier.currency}")

        status = Status.objects.using(db).get(name__iexact=status_name)

        supplier.country = str(countries[country_key].pk)
        supplier.currency = str(currencies[currency_key].pk)
        supplier.status = str(status.pk)

        supplier.save(
            using=db,
            update_fields=["country", "currency", "status"]
        )


def reverse_supplier_data(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    Country = apps.get_model("core", "Country")
    Currency = apps.get_model("core", "Currency")
    Status = apps.get_model("core", "Status")

    db = schema_editor.connection.alias

    for supplier in Supplier.objects.using(db).all():
        supplier.country = Country.objects.using(db).get(
            pk=int(supplier.country)
        ).name

        supplier.currency = Currency.objects.using(db).get(
            pk=int(supplier.currency)
        ).code

        supplier.status = Status.objects.using(db).get(
            pk=int(supplier.status)
        ).name

        supplier.save(
            using=db,
            update_fields=["country", "currency", "status"]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_country_currency'),
        ('suppliers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            convert_supplier_data,
            reverse_supplier_data
        ),

        migrations.AlterField(
            model_name='supplier',
            name='country',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.country',
                verbose_name='Country'
            ),
        ),

        migrations.AlterField(
            model_name='supplier',
            name='currency',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.currency',
                verbose_name='Currency'
            ),
        ),

        migrations.AlterField(
            model_name='supplier',
            name='status',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.status',
                verbose_name='Status'
            ),
        ),
    ]
