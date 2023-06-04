# Generated by Django 4.0.8 on 2023-01-06 19:30

from django.db import migrations, models
import django.db.models.deletion
import djangocms_text_ckeditor.fields


class Migration(migrations.Migration):
    replaces = [
        ("cms_plugins", "0002_auto_20200215_1336"),
        ("cms_plugins", "0003_delete_thumbnailpluginmodel"),
        ("cms_plugins", "0004_alertpluginmodel"),
        ("cms_plugins", "0005_quicklinkspluginmodel_rowpluginmodel"),
        ("cms_plugins", "0006_alter_alertpluginmodel_cmsplugin_ptr_and_more"),
    ]

    dependencies = [
        ("cms_plugins", "0001_squashed_0008_upcomingeventsandcoursespluginmodel"),
        ("cms", "0022_auto_20180620_1551"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thumbnailpluginmodel",
            name="crop",
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text="If this thumbnail should be cropped to fit given size.",
            ),
        ),
        migrations.AlterField(
            model_name="thumbnailpluginmodel",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Image to show thumbnail for.",
                null=True,
                upload_to="",
            ),
        ),
        migrations.DeleteModel(
            name="ThumbnailPluginModel",
        ),
        migrations.CreateModel(
            name="AlertPluginModel",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="%(app_label)s_%(class)s",
                        serialize=False,
                        to="cms.cmsplugin",
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=100, null=True)),
                ("content", djangocms_text_ckeditor.fields.HTMLField()),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("primary", "Primary"),
                            ("secondary", "Secondary"),
                            ("success", "Success"),
                            ("danger", "Danger"),
                            ("warning", "Warning"),
                            ("info", "Info"),
                            ("light", "Light"),
                            ("dark", "Dark"),
                        ],
                        max_length=20,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("cms.cmsplugin",),
        ),
        migrations.AlterField(
            model_name="countdownpluginmodel",
            name="cmsplugin_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                related_name="%(app_label)s_%(class)s",
                serialize=False,
                to="cms.cmsplugin",
            ),
        ),
        migrations.AlterField(
            model_name="pagetitlepluginmodel",
            name="cmsplugin_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                related_name="%(app_label)s_%(class)s",
                serialize=False,
                to="cms.cmsplugin",
            ),
        ),
        migrations.CreateModel(
            name="QuickLinksPluginModel",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="%(app_label)s_%(class)s",
                        serialize=False,
                        to="cms.cmsplugin",
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=100, null=True)),
                ("text", models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                "abstract": False,
            },
            bases=("cms.cmsplugin",),
        ),
        migrations.CreateModel(
            name="RowPluginModel",
            fields=[
                (
                    "cmsplugin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        related_name="%(app_label)s_%(class)s",
                        serialize=False,
                        to="cms.cmsplugin",
                    ),
                ),
                (
                    "column_classes",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("cms.cmsplugin",),
        ),
        migrations.AlterField(
            model_name="upcomingeventsandcoursespluginmodel",
            name="cmsplugin_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                related_name="%(app_label)s_%(class)s",
                serialize=False,
                to="cms.cmsplugin",
            ),
        ),
    ]
