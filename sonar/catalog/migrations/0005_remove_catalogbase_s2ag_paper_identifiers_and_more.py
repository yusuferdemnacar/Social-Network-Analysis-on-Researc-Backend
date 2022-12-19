# Generated by Django 4.1.3 on 2022-12-19 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0003_articleidentifier_alter_article_options'),
        ('catalog', '0004_remove_catalogextension_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='catalogbase',
            name='s2ag_paper_identifiers',
        ),
        migrations.RemoveField(
            model_name='catalogextension',
            name='s2ag_paper_identifiers',
        ),
        migrations.AddField(
            model_name='catalogbase',
            name='article_identifiers',
            field=models.ManyToManyField(related_name='papers_%(class)s', to='article.articleidentifier'),
        ),
        migrations.AddField(
            model_name='catalogextension',
            name='article_identifiers',
            field=models.ManyToManyField(related_name='papers_%(class)s', to='article.articleidentifier'),
        ),
    ]