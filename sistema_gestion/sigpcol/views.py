# sigpcol/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import AcademicYear, Grade, Student, Representative, Payment, Discount, Report, Role, User
from .forms import AcademicYearForm, GradeForm, StudentForm, RepresentativeForm, PaymentForm, DiscountForm, StudentSearchForm, ReportForm, ReportFilterForm, RepresentativeFilterForm
from django.db.models import Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.conf import settings
import os
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.core.mail import send_mail
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
import subprocess 
from .forms import UploadFileForm
import csv
import io
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from .forms import CustomUserCreationForm
from django.contrib import messages
import pandas as pd
from django.db.models import Q
from decimal import Decimal
import json
from .models import Report, Student, Payment, Representative



class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

# Funciones de ayuda para verificar roles
def es_nivel4(user):
    return user.is_nivel4

# Funciones de vista
@user_passes_test(es_nivel4)
def administrar_cuentas(request):
    users = User.objects.all()
    return render(request, 'admin_user_accounts.html', {'users': users})

class MyPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'

class MyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'    
 
'''Funcion para manejar la logoica de respaldos de datos'''
@user_passes_test(es_nivel4)
def backup_database(request):
    try:
        # Ruta donde se guardará el backup
        backup_path = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_path, exist_ok=True)
        
        # Nombre del archivo de backup
        filename = 'backup_{}.sql'.format(settings.DATABASES['default']['NAME'])
        filepath = os.path.join(backup_path, filename)
        
        # Comando de backup para PostgreSQL
        command = f"pg_dump -U {settings.DATABASES['default']['USER']} -h {settings.DATABASES['default']['HOST']} {settings.DATABASES['default']['NAME']} > {filepath}"
        
        # Ejecutar el comando
        subprocess.run(command, shell=True, check=True)
        
        return HttpResponse(f"Backup realizado correctamente en {filepath}")
    
    except Exception as e:
        return HttpResponse(f"Error al realizar el backup: {str(e)}")

'''Logica para restaurar los bakup de la base de datos'''
@user_passes_test(es_nivel4)
def restore_database(request):
    # Lógica para restaurar la base de datos desde un archivo de backup
    # Este ejemplo asume que usas SQLite. Ajusta según tu motor de BD.
    backup_path = os.path.join(settings.MEDIA_ROOT, 'db_backup.sqlite3')
    db_path = settings.DATABASES['default']['NAME']
    try:
        import shutil
        shutil.copyfile(backup_path, db_path)
        return HttpResponse("Base de datos restaurada exitosamente.")
    except Exception as e:
        return HttpResponse(f"Error al restaurar la base de datos: {e}", status=500)

def enviar_resumen_estado_cuenta(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    email_subject = "Resumen de Estado de Cuenta"
    email_body = f"Aquí está su resumen de estado de cuenta para el estudiante {student.nombre} {student.apellido}."
    send_mail(
        email_subject,
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        [student.representante.email],
    )
    return HttpResponse("Correo enviado")

@user_passes_test(es_nivel4)
def upload_users(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Asumimos que el archivo es CSV. Ajusta según el formato.
            decoded_file = file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string, delimiter=',', quotechar='"')
            for row in reader:
                # Asume que el CSV tiene campos: username, email, password, role, etc.
                username, email, password, role_name = row[:4]
                role, created = Role.objects.get_or_create(nombre=role_name)
                User.objects.create_user(username=username, email=email, password=password, role=role)
            return HttpResponse("Usuarios cargados exitosamente.")
    else:
        form = UploadFileForm()
    return render(request, 'upload_users.html', {'form': form})


@user_passes_test(lambda u: u.is_superuser)  # Solo el superusuario o nivel 4 puede crear usuarios
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_list')  # Redirigir a una lista de usuarios o donde prefieras
    else:
        form = CustomUserCreationForm()
    return render(request, 'create_user.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

def create_academic_year(request):
    if request.method == 'POST':
        form = AcademicYearForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academic_year_list')
    else:
        form = AcademicYearForm()
    return render(request, 'create_academic_year.html', {'form': form})

def create_grade(request):
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('grade_list')
    else:
        form = GradeForm()
    return render(request, 'create_grade.html', {'form': form})

def create_student(request):
    form = None
    if request.method == 'POST':
        errors = []
        if 'upload_csv' in request.POST:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'No se ha seleccionado ningún archivo CSV.')
            elif not csv_file.name.endswith('.csv'):
                messages.error(request, 'El archivo no es un CSV válido.')
            else:
                data_set = csv_file.read().decode('UTF-8')
                io_string = csv.reader(data_set.splitlines())
                for row in io_string:
                    representante_id = row[6].strip()
                    try:
                        representante = Representative.objects.get(id=representante_id)
                    except Representative.DoesNotExist:
                        errors.append(f"Representante con ID '{representante_id}' no encontrado. Verifica los datos.")
                        representante = None  # Set to None if not found

                    Student.objects.update_or_create(
                        nombre=row[1].strip(),
                        apellido=row[2].strip(),
                        descuento_personalizado=row[3] if row[3] else None,
                        anio_academico_id=row[4].strip(),
                        grado_id=row[5].strip(),
                        representante=representante
                    )
                if errors:
                    for error in errors:
                        messages.error(request, error)
                messages.success(request, 'Carga de estudiantes finalizada con posibles errores.')

        elif 'upload_excel' in request.POST:
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                messages.error(request, 'No se ha seleccionado ningún archivo Excel.')
            elif not excel_file.name.endswith(('.xls', '.xlsx')):
                messages.error(request, 'El archivo no es un Excel válido.')
            else:
                df = pd.read_excel(excel_file)
                for index, row in df.iterrows():
                    representante_id = row['representante_id']
                    try:
                        representante = Representative.objects.get(id=representante_id)
                    except Representative.DoesNotExist:
                        errors.append(f"Representante con ID '{representante_id}' no encontrado. Verifica los datos.")
                        representante = None  # Set to None if not found

                    Student.objects.update_or_create(
                        nombre=row['nombre'].strip(),
                        apellido=row['apellido'].strip(),
                        descuento_personalizado=row['descuento_personalizado'] if not pd.isna(row['descuento_personalizado']) else None,
                        anio_academico_id=row['anio_academico_id'],
                        grado_id=row['grado_id'],
                        representante=representante
                    )
                if errors:
                    for error in errors:
                        messages.error(request, error)
                messages.success(request, 'Carga de estudiantes finalizada con posibles errores.')

        else:
            form = StudentForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('student_list', academic_year_id=form.cleaned_data['anio_academico'].id)
    else:
        form = StudentForm()
    
    if form is None:
        form = StudentForm()

    return render(request, 'create_student.html', {'form': form})

def create_representative(request):
    form = RepresentativeForm()  # Define el formulario inicialmente
    
    if request.method == 'POST':
        if 'upload_csv' in request.POST:
            if 'csv_file' in request.FILES:
                csv_file = request.FILES['csv_file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'El archivo no es un CSV válido.')
                else:
                    data_set = csv_file.read().decode('UTF-8')
                    io_string = csv.reader(data_set.splitlines())
                    for row in io_string:
                        _, created = Representative.objects.update_or_create(
                            nombre=row[0],
                            apellido=row[1],
                            telefono_principal=row[2],
                            telefono_secundario=row[3],
                            direccion=row[4],
                            email=row[5],
                            informacion_facturacion=row[6]
                        )
                    messages.success(request, 'Representantes cargados exitosamente.')
                    return redirect('representative_list')
            else:
                messages.error(request, 'No se seleccionó ningún archivo CSV.')

        elif 'upload_excel' in request.POST:
            if 'excel_file' in request.FILES:
                excel_file = request.FILES['excel_file']
                if not excel_file.name.endswith(('.xls', '.xlsx')):
                    messages.error(request, 'El archivo no es un Excel válido.')
                else:
                      df = pd.read_excel(excel_file)
                      for index, row in df.iterrows():
                         Representative.objects.update_or_create(
                        nombre=row['nombre'],
                        apellido=row['apellido'],
                        telefono_principal=row['telefono_principal'],
                        telefono_secundario=row['telefono_secundario'],
                        direccion=row['direccion'],
                        email=row['email'],
                        informacion_facturacion=row['informacion_facturacion']
                        )

                messages.success(request, 'Representantes cargados exitosamente.')
                return redirect('representative_list')
            else:
                messages.error(request, 'No se seleccionó ningún archivo Excel.')

        else:
            form = RepresentativeForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('representative_list')

    return render(request, 'create_representative.html', {'form': form})

def create_payment(request):
    exchange_rate = get_current_exchange_rate()  # Obtener la tasa de cambio actual

    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)  # Asegúrate de incluir request.FILES
        if form.is_valid():
            form.save()
            return redirect('payment_list')
    else:
        form = PaymentForm()

    context = {
        'form': form,
        'exchange_rate': exchange_rate,  # Tasa de cambio actual
    }

    return render(request, 'create_payment.html', context)

def create_discount(request):
    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('discount_list')
    else:
        form = DiscountForm()
    return render(request, 'create_discount.html', {'form': form})

def discount_list(request):
    discounts = Discount.objects.all()  # Obtén todos los descuentos de la base de datos
    return render(request, 'discount_list.html', {'discounts': discounts})

# sigpcol/views.py
from django.shortcuts import render, get_object_or_404
from .models import AcademicYear, Student
from .forms import ReportFilterForm
from django.core.paginator import Paginator

def student_list(request, academic_year_id):
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
    form = ReportFilterForm(request.GET or None)
    
    students = Student.objects.filter(anio_academico=academic_year)
    
    if form.is_valid():
        if form.cleaned_data.get('student_name'):
            students = students.filter(nombre__icontains=form.cleaned_data['student_name'])
        if form.cleaned_data.get('grade'):
            students = students.filter(grado=form.cleaned_data['grade'])
        if form.cleaned_data.get('section'):
            students = students.filter(grado__seccion=form.cleaned_data['section'])
    
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'student_list.html', {
        'form': form,
        'page_obj': page_obj,
        'academic_year_id': academic_year_id,
    })
from django.shortcuts import render, redirect
from .models import AcademicYear
from django import forms

# Formulario para seleccionar el año académico
class SelectAcademicYearForm(forms.Form):
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))

# Vista para seleccionar el año académico
def select_academic_year(request):
    if request.method == 'POST':
        form = SelectAcademicYearForm(request.POST)
        if form.is_valid():
            # Redirigir al listado de estudiantes para el año académico seleccionado
            academic_year_id = form.cleaned_data['academic_year'].id
            return redirect('student_list', academic_year_id=academic_year_id)
    else:
        form = SelectAcademicYearForm()

    return render(request, 'select_academic_year.html', {'form': form})


'''def student_list(request, academic_year_id):
    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
    students = Student.objects.filter(anio_academico=academic_year)
    return render(request, 'student_list.html', {
        'students': students,
        'academic_year_id': academic_year_id  # Asegúrate de pasar academic_year_id aquí
    })'''

def payment_list(request):
    payments = Payment.objects.all()

    # Filtro por representante
    representante_query = request.GET.get('representante')
    if representante_query:
        payments = payments.filter(
            Q(representante__nombre__icontains=representante_query) |
            Q(representante__apellido__icontains=representante_query)
        )

    return render(request, 'payment_list.html', {'payments': payments})

def get_current_exchange_rate():
    # Obtén la tasa de cambio actual
    academic_year = AcademicYear.objects.latest('fecha_inicio')
    return academic_year.tasa_moneda

'''Pagina de inicio'''
def index(request):
    selected_year_id = request.GET.get('chart_academic_year')
    academic_year = None

    if selected_year_id:
        try:
            academic_year = AcademicYear.objects.get(id=selected_year_id)
        except AcademicYear.DoesNotExist:
            academic_year = None
    
    students = Student.objects.all()

    total_due = 0
    total_paid = 0

    if academic_year:  # Verifica si se seleccionó un ciclo académico válido
        for student in students:
            payments = Payment.objects.filter(estudiante=student, año_académico=academic_year)
            total_paid_by_student = payments.aggregate(total_paid=Sum('monto_usd'))['total_paid'] or Decimal('0.00')

            # Calcula el total que el estudiante debe pagar
            total_due_by_student = academic_year.tarifa_mensual * academic_year.numero_pagos

            total_due += total_due_by_student
            total_paid += total_paid_by_student
    else:
        # Si no hay un ciclo académico seleccionado o válido, maneja el caso
        total_paid_by_student = Decimal('0.00')
        total_due_by_student = Decimal('0.00')

    # Añade la tasa de cambio al contexto
    exchange_rate = get_current_exchange_rate()

    context = {
        'total_paid': total_paid,
        'total_due': total_due - total_paid,  # Esto refleja lo que queda pendiente de pago
        'academic_years': AcademicYear.objects.all(),
        'exchange_rate': exchange_rate,  # Tasa de cambio actual
    }

    return render(request, 'index.html', context)

def report_due_students(request):
    form = ReportFilterForm(request.GET or None)
    due_students = []
    total_due = 0

    if form.is_valid():
        students = Student.objects.all()
        if form.cleaned_data.get('student_name'):
            students = students.filter(nombre__icontains=form.cleaned_data['student_name'])
        if form.cleaned_data.get('academic_year'):
            students = students.filter(anio_academico=form.cleaned_data['academic_year'])
        if form.cleaned_data.get('grade'):
            students = students.filter(grado=form.cleaned_data['grade'])
        if form.cleaned_data.get('section'):
            students = students.filter(grado__seccion=form.cleaned_data['section'])

        for student in students:
            total_paid = Payment.objects.filter(estudiante=student).aggregate(total_pagado=Sum('abono_usd'))['total_pagado'] or 0
            annual_fee = student.anio_academico.tarifa_mensual * student.anio_academico.numero_pagos
            discount = student.descuento_personalizado or 0
            discounted_annual_fee = annual_fee * (Decimal(1) - (discount / Decimal(100)))
            monto_de_mora = discounted_annual_fee - total_paid
            
            if monto_de_mora > 0:
                due_students.append({
                    'nombre': student.nombre,
                    'apellido': student.apellido,
                    'grado': student.grado,
                    'anio_academico': student.anio_academico,
                    'representante': student.representante,
                    'monto_de_mora': monto_de_mora,
                })

        total_due = len(due_students)

    context = {
        'form': form,
        'due_students': due_students,
        'total_due': total_due
    }
    return render(request, 'report_due_students.html', context)


from django.db.models import F

from decimal import Decimal

def report_statistics(request):
    form = ReportFilterForm(request.GET)
    payments_data = []
    
    if form.is_valid():
        # Empieza seleccionando todos los estudiantes
        students = Student.objects.all()

        # Aplicar los filtros
        if form.cleaned_data.get('student_name'):
            student_name = form.cleaned_data['student_name'].strip()  # Eliminamos espacios
            students = students.filter(nombre__icontains=student_name)

        if form.cleaned_data.get('academic_year'):
            academic_year = form.cleaned_data['academic_year']
            students = students.filter(anio_academico=academic_year)

        if form.cleaned_data.get('grade'):
            grade = form.cleaned_data['grade']
            students = students.filter(grado=grade)

        if form.cleaned_data.get('section'):
            section = form.cleaned_data['section']
            students = students.filter(grado__seccion=section)
        
        for student in students:
            academic_year = student.anio_academico
            monthly_fee = Decimal(academic_year.tarifa_mensual)
            total_annual_fee = monthly_fee * academic_year.numero_pagos
            discount = Decimal(student.descuento_personalizado or 0)
            discounted_annual_fee = total_annual_fee * (Decimal(1) - (discount / Decimal(100)))

            # Total pagado por el estudiante
            total_paid = Payment.objects.filter(estudiante=student).aggregate(total_pagado=Sum('abono_usd'))['total_pagado'] or Decimal(0)

            # Total pendiente considerando descuentos y pagos realizados
            total_pending = discounted_annual_fee - total_paid
            
            payments = Payment.objects.filter(estudiante=student)

            for payment in payments:
                discounted_monthly_fee = monthly_fee * (Decimal(1) - (discount / Decimal(100)))
                payments_data.append({
                    'estudiante__nombre': student.nombre + ' ' + student.apellido,
                    'año_académico__nombre': academic_year.nombre,
                    'mes': payment.mes,
                    'monto_con_descuento': discounted_monthly_fee,
                    'total_pagado': payment.abono_usd,
                    'monto_pendiente': discounted_monthly_fee - payment.abono_usd,
                })

            payments_data.append({
                'estudiante__nombre': f'Total Adeudado por {student.nombre} {student.apellido}',
                'año_académico__nombre': '',
                'mes': '',
                'monto_con_descuento': '',
                'total_pagado': '',
                'monto_pendiente': total_pending,
            })
    
    context = {
        'form': form,
        'payments_data': payments_data,
    }

    return render(request, 'report_statistics.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ReportReceiptForm
from .models import Receipt

def report_receipt(request):
    if request.method == 'POST':
        form = ReportReceiptForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recibo reportado con éxito.')
            return redirect('report_receipt')  # Redirige a la misma página o a otra según tu flujo.
        else:
            messages.error(request, 'Por favor, corrige los errores a continuación.')
    else:
        form = ReportReceiptForm()

    return render(request, 'report_receipt.html', {'form': form})


def create_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            # Recopilar los datos necesarios para el reporte
            students = Student.objects.all().select_related('representante')
            report_data = []

            for student in students:
                representative = student.representante
                payments = Payment.objects.filter(estudiante=student)

                # Convertir montos a string para evitar problemas de serialización
                payments_data = []
                for payment in payments:
                    payments_data.append({
                        'monto_bs': str(payment.monto_bs),
                        'monto_usd': str(payment.monto_usd),
                        'fecha_pago': payment.fecha_pago.strftime('%Y-%m-%d'),
                        'estado': payment.estado,
                    })

                student_data = {
                    'student_name': f"{student.nombre} {student.apellido}",
                    'grade': str(student.grado),
                    'representative_name': f"{representative.nombre} {representative.apellido}",
                    'representative_email': representative.email,
                    'payments': payments_data,
                }
                report_data.append(student_data)

            # Obtener el año académico (puedes ajustar esto según tu lógica)
            academic_year = AcademicYear.objects.first()  # Esto es un ejemplo, ajusta la lógica para obtener el año académico correcto

            # Crear un nuevo reporte
            report = form.save(commit=False)
            report.año_académico = academic_year  # Asignar el año académico
            report.datos = json.dumps(report_data)  # Serializar los datos a JSON
            report.save()

            return redirect('report_overview')
    else:
        form = ReportForm()

    return render(request, 'create_report.html', {'form': form})

# sigpcol/views.py
from django.shortcuts import render
from .models import Receipt

def list_receipts(request):
    receipts = Receipt.objects.all()
    return render(request, 'list_receipts.html', {'receipts': receipts})


def report_overview(request):
    reports = Report.objects.all()
    return render(request, 'report_overview.html', {'reports': reports})

def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, 'report_detail.html', {'report': report})

@login_required
def payment_detail(request, payment_id):
    """Vista para mostrar detalles del pago, incluyendo el monto pendiente."""
    payment = get_object_or_404(Payment, id=payment_id)
    context = {
        'payment': payment,
        'monto_pendiente': payment.monto_pendiente
    }
    return render(request, 'payment_detail.html', context)

@login_required
def emitir_factura(request, payment_id):
    """Vista para emitir la factura si el pago está aprobado."""
    payment = get_object_or_404(Payment, id=payment_id)

    if payment.estado == Payment.APROBADO:
        # Generar el archivo PDF de la factura
        pdf_path = generar_factura(payment)
        pdf_filename = os.path.basename(pdf_path)

        context = {
            'payment': payment,
            'pdf_filename': pdf_filename,
            'message': 'Factura emitida correctamente. Puedes descargarla a continuación.',
        }
        return render(request, 'factura_emitida.html', context)
    else:
        return JsonResponse({
            'error': 'No se puede emitir factura para un pago no aprobado.'
        }, status=400)        

def generar_factura(payment):
    """Lógica para generar la factura en formato PDF."""
    factura = {
        'representante': payment.representante.nombre,
        'estudiante': payment.estudiante.nombre,
        'monto_usd': payment.monto_usd,
        'monto_bs': payment.monto_bs,
        'fecha_pago': payment.fecha_pago,
        'numero_factura': f"FACT-{payment.id}-{payment.fecha_pago.strftime('%Y%m%d')}",
    }

    # Ruta para guardar el archivo PDF
    pdf_filename = f"factura_{factura['numero_factura']}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)

    # Asegurarse de que la carpeta donde se guardará el PDF exista
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    # Crear un canvas para el PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Añadir contenido al PDF
    c.drawString(100, height - 100, f"Factura N°: {factura['numero_factura']}")
    c.drawString(100, height - 150, f"Representante: {factura['representante']}")
    c.drawString(100, height - 200, f"Estudiante: {factura['estudiante']}")
    c.drawString(100, height - 250, f"Monto USD: {factura['monto_usd']}")
    c.drawString(100, height - 300, f"Monto BS: {factura['monto_bs']}")
    c.drawString(100, height - 350, f"Fecha de Pago: {factura['fecha_pago'].strftime('%d/%m/%Y')}")

    # Finalizar el PDF
    c.showPage()
    c.save()

    # Puedes devolver el nombre del archivo o la ruta completa si deseas manipularlo después
    return pdf_path

@login_required
def emitir_factura_por_representante(request):
    """Vista para filtrar pagos por representante y emitir factura."""
    form = RepresentativeFilterForm(request.GET or None)

    if request.method == "GET" and form.is_valid():
        payment = form.cleaned_data.get('payment')
        if payment:
            pdf_path = generar_factura(payment)
            pdf_filename = os.path.basename(pdf_path)
            context = {
                'payment': payment,
                'pdf_filename': pdf_filename,
                'message': 'Factura emitida correctamente. Puedes descargarla a continuación.',
            }
            return render(request, 'factura_emitida.html', context)

    return render(request, 'filtrar_representante.html', {'form': form})

from django.utils import timezone

def approve_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.estado = Payment.APROBADO
    payment.fecha_aprobacion = timezone.now()
    payment.save()
    return redirect('payment_list')

def reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.estado = Payment.RECHAZADO
    payment.fecha_aprobacion = timezone.now()
    payment.save()
    return redirect('payment_list')

def reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    payment.estado = Payment.RECHAZADO
    payment.save()
    return redirect('payment_list')

def student_account_status(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Filtrar pagos asociados al estudiante
    payments = Payment.objects.filter(estudiante=student)
    
    # Filtrar recibos asociados a los pagos del estudiante
    receipts = Receipt.objects.filter(payment__estudiante=student)
    
    context = {
        'student': student,
        'payments': payments,
        'receipts': receipts,
    }
    return render(request, 'student_account_status.html', context)

from django.shortcuts import render
from .models import Representative

def representative_list(request):
    representatives = Representative.objects.all()
    return render(request, 'representative_list.html', {'representatives': representatives})

from django.shortcuts import render, get_object_or_404, redirect
from .models import Representative
from .forms import RepresentativeForm

def edit_representative(request, representative_id):
    representative = get_object_or_404(Representative, id=representative_id)
    
    if request.method == 'POST':
        form = RepresentativeForm(request.POST, instance=representative)
        if form.is_valid():
            form.save()
            return redirect('representative_list')
    else:
        form = RepresentativeForm(instance=representative)
    
    context = {
        'form': form,
        'representative': representative,
    }
    
    return render(request, 'edit_representative.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from .models import Representative

def delete_representative(request, representative_id):
    representative = get_object_or_404(Representative, id=representative_id)
    
    if request.method == 'POST':
        representative.delete()
        return redirect('representative_list')
    
    context = {
        'representative': representative,
    }
    
    return render(request, 'delete_representative.html', context)

from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, Grade, AcademicYear

def promote_students(request):
    # Obtener el ciclo académico actual
    current_academic_year = AcademicYear.objects.latest('id')

    # Crear el nuevo ciclo académico
    current_years = current_academic_year.nombre.split('-')
    next_year_start = str(int(current_years[0].split()[-1]) + 1)
    next_year_end = str(int(current_years[1]) + 1)
    next_academic_year_nombre = f"Ciclo {next_year_start}-{next_year_end}"

    next_academic_year = AcademicYear.objects.create(
        nombre=next_academic_year_nombre,
        fecha_inicio=current_academic_year.fecha_inicio.replace(year=int(next_year_start)),
        fecha_final=current_academic_year.fecha_final.replace(year=int(next_year_end)),
        tarifa_mensual=current_academic_year.tarifa_mensual,
        descuento_pago_anticipado=current_academic_year.descuento_pago_anticipado,
        tasa_moneda=current_academic_year.tasa_moneda,
        numero_pagos=current_academic_year.numero_pagos
    )

    # Promover estudiantes de cada grado al siguiente
    grades = Grade.objects.all()
    for grade in grades:
        # Obtener el siguiente grado según el nombre (ajustar lógica según tus necesidades)
        next_grade_name = obtener_siguiente_grado(grade.nombre)
        next_grade = Grade.objects.filter(nombre=next_grade_name, seccion=grade.seccion).first()

        if next_grade:
            students_to_promote = Student.objects.filter(grado=grade, anio_academico=current_academic_year)
            for student in students_to_promote:
                Student.objects.create(
                    nombre=student.nombre,
                    apellido=student.apellido,
                    grado=next_grade,
                    anio_academico=next_academic_year,
                    descuento_personalizado=student.descuento_personalizado,
                    representante=student.representante
                )

    # Redirigir a la lista de estudiantes del nuevo año académico
    return redirect('student_list', academic_year_id=next_academic_year.id)



def obtener_siguiente_grado(nombre_grado_actual):
    # Define aquí la lógica para determinar el siguiente grado en base al nombre del grado actual
    # Esta lógica debe ser coherente con la nomenclatura de tus grados
    orden_grados = [
        "Primero primaria",
        "Segundo primaria",
        "Tercero primaria",
        "Cuarto primaria",
        "Quinto primaria",
        "Sexto primaria",
        "Primero secundaria",
        "Segundo secundaria",
        "Tercero secundaria",
        "Cuarto secundaria",
        "Quinto secundaria"
    ]

    if nombre_grado_actual in orden_grados:
        indice_actual = orden_grados.index(nombre_grado_actual)
        if indice_actual + 1 < len(orden_grados):
            return orden_grados[indice_actual + 1]
    return None  # Si no hay un grado superior, retorna None

def edit_promotion(request, cycle_id):
    # Obtener el año académico basado en el cycle_id
    academic_year = get_object_or_404(AcademicYear, pk=cycle_id)
    
    # Obtener todos los estudiantes en el nuevo ciclo académico promovido
    promoted_students = Student.objects.filter(anio_academico=academic_year)

    if request.method == 'POST':
        # Manejar la eliminación de los estudiantes seleccionados
        for student_id in request.POST.getlist('delete_students'):
            Student.objects.filter(pk=student_id).delete()

        # Manejar la adición de nuevos estudiantes
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()

    context = {
        'promoted_students': promoted_students,
        'form': StudentForm(),
        'academic_year': academic_year,
    }
    return render(request, 'edit_promotion.html', context)
