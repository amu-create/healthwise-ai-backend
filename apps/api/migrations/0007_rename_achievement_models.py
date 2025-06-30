# Generated manually on 2025-01-24

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('api', '0006_notification_userprofile_workoutpost_postcomment_and_more'),
    ]

    operations = [
        # Rename models
        migrations.RenameModel(
            old_name='Achievement',
            new_name='WorkoutAchievement',
        ),
        migrations.RenameModel(
            old_name='UserAchievement',
            new_name='UserWorkoutAchievement',
        ),
        migrations.RenameModel(
            old_name='UserLevel',
            new_name='UserWorkoutLevel',
        ),
    ]
