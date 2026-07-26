from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0012_remove_wardenprofile_assigned_blocks'),
        ('hms', '0006_remove_dutyassignment_block_and_more'),
        ('room', '0010_hostelbuilding_code_hostelbuilding_is_archived_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BedAllocation',
        ),
        migrations.DeleteModel(
            name='Bed',
        ),
        migrations.DeleteModel(
            name='Room',
        ),
        migrations.DeleteModel(
            name='Floor',
        ),
        migrations.DeleteModel(
            name='HostelBlock',
        ),
        migrations.DeleteModel(
            name='HostelBuilding',
        ),
        migrations.DeleteModel(
            name='RoomCategoryPricing',
        ),
        migrations.DeleteModel(
            name='RoomTypePricing',
        ),
    ]
