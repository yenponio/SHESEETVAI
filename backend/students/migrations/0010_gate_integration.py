from django.db import migrations, models
import django.db.models.deletion


def seed_controller(apps, schema_editor):
    apps.get_model("students", "GateController").objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("students", "0009_aiinspection_recorded")]
    operations = [
        migrations.CreateModel(
            name="GateCycle",
            fields=[
                ("attempt", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, related_name="gate_cycle", serialize=False, to="students.accessattempt")),
                ("phase", models.CharField(default="QUEUED", max_length=20)),
                ("outcome", models.CharField(default="PENDING", max_length=20)),
                ("bridge_id", models.CharField(blank=True, max_length=64)),
                ("message", models.CharField(blank=True, max_length=160)),
            ],
        ),
        migrations.CreateModel(
            name="GateController",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, primary_key=True, serialize=False)),
                ("enabled", models.BooleanField(default=False)),
                ("connected", models.BooleanField(default=False)),
                ("ready", models.BooleanField(default=False)),
                ("bridge_id", models.CharField(blank=True, max_length=64)),
                ("process_id", models.PositiveIntegerField(default=0)),
                ("revision", models.PositiveBigIntegerField(default=0)),
                ("active_cycle", models.OneToOneField(blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="students.gatecycle")),
            ],
        ),
        migrations.CreateModel(
            name="GateEvent",
            fields=[
                ("key", models.CharField(max_length=100, primary_key=True, serialize=False)),
                ("event", models.CharField(max_length=32)),
                ("cycle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="students.gatecycle")),
            ],
        ),
        migrations.RunPython(seed_controller, migrations.RunPython.noop),
    ]
