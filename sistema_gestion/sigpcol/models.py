from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.core.files.storage import FileSystemStorage
from django.utils import timezone

# Definición de los niveles de acceso
NIVELES_USUARIO = [
    ('NIVEL1', 'Usuarios Finales'),
    ('NIVEL2', 'Administradores Contables'),
    ('NIVEL3', 'Usuarios Administrativos'),
    ('NIVEL4', 'Super Administrador General'),
]

class Role(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
# Modelo User actualizado
class User(AbstractUser):
    role = models.CharField(max_length=10, choices=NIVELES_USUARIO, default='NIVEL1')
    numero_de_telefono = models.CharField(max_length=15, blank=True)
    factura_tipo = models.CharField(max_length=1, choices=[('J', 'Jurídica'), ('N', 'Natural')], blank=True)

    def __str__(self):
        return self.username   
 

    @property
    def is_nivel1(self):
        return self.role == 'NIVEL1'

    @property
    def is_nivel2(self):
        return self.role == 'NIVEL2'

    @property
    def is_nivel3(self):
        return self.role == 'NIVEL3'

    @property
    def is_nivel4(self):
        return self.role == 'NIVEL4'

# Academic Year Model
class AcademicYear(models.Model):
    nombre = models.CharField(max_length=20, unique=True)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    tarifa_mensual = models.DecimalField(max_digits=10, decimal_places=2)  # USD
    descuento_pago_anticipado = models.DecimalField(max_digits=5, decimal_places=2)  # %
    tasa_moneda = models.DecimalField(max_digits=10, decimal_places=4)  # BS/USD
    numero_pagos = models.IntegerField()

    def __str__(self):
        return self.nombre

# Grade Model
class Grade(models.Model):
    SECTIONS = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D' ,'D'),
        ('E' ,'E'),
    ]

    nombre = models.CharField(max_length=20)
    seccion = models.CharField(max_length=1, choices=SECTIONS)

    def __str__(self):
        return f"{self.nombre} - Sección {self.seccion}"

class Representative(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    usuario = models.CharField(max_length=100)
    telefono_principal = models.CharField(max_length=20)
    telefono_secundario = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField()
    email = models.EmailField(max_length=254, blank=True)  # Nuevo campo
    informacion_facturacion = models.TextField()

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Student(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    grado = models.ForeignKey(Grade, on_delete=models.CASCADE)
    anio_academico = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    descuento_personalizado = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    representante = models.ForeignKey(Representative, on_delete=models.CASCADE, related_name='estudiantes')

    def __str__(self):
        return f"{self.nombre} {self.apellido}" 
     

class Payment(models.Model):
    PENDIENTE = 'PENDIENTE'
    APROBADO = 'APROBADO'
    RECHAZADO = 'RECHAZADO'
    OPCIONES_ESTADO = [
        (PENDIENTE, 'Pendiente'),
        (APROBADO, 'Aprobado'),
        (RECHAZADO, 'Rechazado'),
    ]

    representante = models.ForeignKey(Representative, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Student, on_delete=models.CASCADE)
    año_académico = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    mes = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        default=1
    )
    monto_bs = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])  # BS
    monto_usd = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])  # USD
    abono_usd = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # Monto abonado
    fecha_pago = models.DateTimeField()
    fecha_reportada = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=OPCIONES_ESTADO, default=PENDIENTE)
    imagen_pago = models.ImageField(upload_to='imagenes_pagos/', null=True, blank=True)  # Imagen del comprobante
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    numero_transaccion = models.CharField(max_length=100)  # Nuevo campo para el número de transacción
    banco_emisor = models.CharField(max_length=100)  # Nuevo campo para el banco emisor
    documento_identidad = models.CharField(max_length=20, default='') # Nuevo campo para el documento de identidad

    def __str__(self):
        return f"Pago de {self.monto_usd} USD por {self.estudiante} ({self.representante})"

    def aplicar_descuento(self):
        if self.fecha_pago.day <= 5:
            descuento = self.monto_usd * (self.año_académico.descuento_pago_anticipado / 100)
            self.monto_usd -= descuento
            self.save()

    def abonar_pago(self, abono):
        """Función para abonar un pago, aplica el abono al monto pendiente."""
        if self.estado != self.PENDIENTE:
            raise ValueError("No se puede abonar a un pago que no está pendiente.")

        if abono <= 0:
            raise ValueError("El abono debe ser mayor que 0.")

        self.abono_usd += abono
        if self.abono_usd >= self.monto_usd:
            self.abono_usd = self.monto_usd
            self.estado = self.APROBADO
        self.save()

    @property
    def monto_pendiente(self):
        """Calcula el monto pendiente después de aplicar abonos."""
        return self.monto_usd - self.abono_usd

    def emitir_factura(self):
        """Emitir factura digital al completar el pago."""
        if self.estado == self.APROBADO:
            # Lógica para emitir factura
            pass
        else:
            raise ValueError("No se puede emitir factura para un pago no aprobado.")
    
# Almacenamiento para las imágenes de pago
fs = FileSystemStorage(location='/media/payments/')

class Receipt(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    fecha_abono = models.DateField()
    monto_abono = models.DecimalField(max_digits=10, decimal_places=2)
    recibo_imagen = models.ImageField(upload_to='receipts/', blank=True, null=True)
    
    def __str__(self):
        return f'Recibo de {self.payment.representante} por {self.monto_abono}'        

class Discount(models.Model):
    nombre = models.CharField(max_length=100, default='Descuento general')
    descripcion = models.TextField(default='Sin descripción')  # Valor predeterminado
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    #fecha_creacion = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.nombre

# Report Model
class Report(models.Model):
    MOROSOS = 'MOROSOS'
    GENERAL = 'GENERAL'
    OPCIONES_TIPO_REPORTE = [
        (MOROSOS, 'Morosos'),
        (GENERAL, 'General'),
    ]

    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    fecha_generado = models.DateTimeField(auto_now_add=True)
    tipo_reporte = models.CharField(max_length=100, default='Default Type')
    año_académico = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    datos = models.JSONField()  # Almacena datos del reporte

    def __str__(self):
        return f"Reporte: {self.nombre} ({self.tipo_reporte})"
    
class BillingInfo(models.Model):
    representative = models.ForeignKey(Representative, related_name='billing_infos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=[('J', 'Jurídica'), ('N', 'Natural')])
    informacion = models.TextField()

    def __str__(self):
        return f"{self.tipo} - {self.informacion}"    

#from .run_task import update_exchange_rate_task

#update_exchange_rate_task(repeat=60)
