# sigpcol/forms.py
from django import forms
from .models import AcademicYear, Grade, Student, Representative, Payment, Discount, Receipt, Report, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['descuento_pago_anticipado', 'tarifa_mensual','fecha_inicio' ,'fecha_final', 'numero_pagos', 'tasa_moneda']

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['nombre', 'seccion']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['nombre', 'apellido', 'grado', 'anio_academico', 'descuento_personalizado', 'representante']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grado'].queryset = Grade.objects.all()
        self.fields['anio_academico'].queryset = AcademicYear.objects.all()
        self.fields['representante'].queryset = Representative.objects.all()
        
        
class RepresentativeForm(forms.ModelForm):
    class Meta:
        model = Representative
        fields = ['nombre', 'apellido', 'usuario', 'telefono_principal', 'telefono_secundario', 'direccion', 'informacion_facturacion']

'''class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['representante', 'estudiante', 'año_académico', 'monto_bs', 'monto_usd','abono_usd' , 'fecha_pago', 'estado']'''

class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['nombre', 'descripcion', 'porcentaje']

from django import forms

class StudentSearchForm(forms.Form):
    search_query = forms.CharField(required=False, label='Search')
    
class ReportFilterForm(forms.Form):
    student_name = forms.CharField(required=False, label="Nombre del Estudiante")
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=False, label="Año Académico")
    grade = forms.ModelChoiceField(queryset=Grade.objects.all(), required=False, label="Grado")
    section = forms.ChoiceField(choices=[('', 'Seleccionar')] + Grade.SECTIONS, required=False, label="Sección")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade'].queryset = Grade.objects.all()
        self.fields['section'].choices = [('', 'Seleccionar')] + Grade.SECTIONS



class PaymentForm(forms.ModelForm):
    # Definir las opciones de los meses
    MONTH_CHOICES = [
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ]

    mes = forms.ChoiceField(choices=MONTH_CHOICES, label="Mes")

    class Meta:
        model = Payment
        fields = ['representante', 'estudiante', 'año_académico', 'mes', 'monto_bs', 'abono_usd', 'monto_usd', 'fecha_pago', 'imagen_pago', 'numero_transaccion', 'banco_emisor', 'documento_identidad']
        widgets = {
            'fecha_pago': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        abono_usd = cleaned_data.get('abono_usd')
        monto_usd = cleaned_data.get('monto_usd')

        if abono_usd and abono_usd > monto_usd:
            raise forms.ValidationError("El abono no puede ser mayor que el monto total.")
        
        return cleaned_data


class ReportReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['payment', 'fecha_abono', 'monto_abono', 'recibo_imagen']
        widgets = {
            'fecha_abono': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_abono'].widget.attrs.update({'class': 'form-control'})
        self.fields['monto_abono'].widget.attrs.update({'class': 'form-control'})
        self.fields['recibo_imagen'].widget.attrs.update({'class': 'form-control-file'})
        
class ReportForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label="Estudiante")

    class Meta:
        model = Report
        fields = ['nombre', 'descripcion', 'tipo_reporte', 'student']  # Añadir campo student si no está

class RepresentativeFilterForm(forms.Form):
    representante = forms.ModelChoiceField(queryset=Representative.objects.all(), required=True, label="Representante")
    payment = forms.ModelChoiceField(queryset=Payment.objects.none(), required=False, label="Pago")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'representante' in self.data:
            try:
                representante_id = int(self.data.get('representante'))
                self.fields['payment'].queryset = Payment.objects.filter(representante_id=representante_id, estado=Payment.APROBADO)
            except (ValueError, TypeError):
                self.fields['payment'].queryset = Payment.objects.none()                
                
class UploadFileForm(forms.Form):
    file = forms.FileField()    
    
    
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password1', 'password2',
            'role', 'numero_de_telefono', 'factura_tipo'
        ]    
    
    
