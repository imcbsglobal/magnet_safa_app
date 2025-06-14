from django.db import models


class AccUsers(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    pass_field = models.CharField(db_column='pass', max_length=100)

    class Meta:
        db_table = 'acc_users'
        managed = False
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Personel(models.Model):
    admission = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=60)

    class Meta:
        db_table = 'personel'
        managed = False
        verbose_name = 'Personnel'
        verbose_name_plural = 'Personnel'


class MagSubject(models.Model):
    code = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'mag_subject'
        managed = False
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'


class CceAssessmentItems(models.Model):
    code = models.CharField(max_length=30, primary_key=True)
    name = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'cce_assessmentitems'
        managed = False
        verbose_name = 'Assessment Item'
        verbose_name_plural = 'Assessment Items'


class CceEntry(models.Model):
    slno = models.DecimalField(
        max_digits=12, decimal_places=0, primary_key=True)
    admission = models.CharField(max_length=20, null=True, blank=True)
    class_field = models.CharField(
        max_length=20, null=True, blank=True, db_column='class')
    division = models.CharField(max_length=20, null=True, blank=True)
    subject = models.CharField(max_length=30, null=True, blank=True)
    assessmentitem = models.CharField(max_length=30, null=True, blank=True)
    term = models.CharField(max_length=20, null=True, blank=True)
    part = models.CharField(max_length=20, null=True, blank=True)
    yearcode = models.CharField(max_length=30, null=True, blank=True)
    edate = models.DateField(null=True, blank=True)
    mark = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True)
    teacher = models.CharField(max_length=10, null=True, blank=True)
    sortorder = models.IntegerField(null=True, blank=True)
    maxmark = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True)
    subperiod = models.CharField(max_length=30, null=True, blank=True)
    indicator = models.CharField(max_length=200, null=True, blank=True)
    element = models.CharField(max_length=300, null=True, blank=True)
    grade = models.CharField(max_length=5, null=True, blank=True)
    groupmark = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True)
    groupper = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True)
    particulars = models.CharField(max_length=50, null=True, blank=True)
    elementgrade = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True)
    longdescription = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'cce_entry'
        managed = False
        verbose_name = 'CCE Entry'
        verbose_name_plural = 'CCE Entries'
