# Generated by Django 4.1.3 on 2022-12-19 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0002_remove_article_field_of_studies_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleIdentifier',
            fields=[
                ('DOI', models.CharField(max_length=255, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name_plural': 'Article Identifiers',
            },
        ),
        migrations.AlterModelOptions(
            name='article',
            options={'verbose_name_plural': 'Articles'},
        ),
    ]
