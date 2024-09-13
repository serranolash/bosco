# sigpcol/admin.py
from django.contrib import admin
from .models import User, Role, AcademicYear, Discount, Student, Representative,Grade, Payment, BillingInfo, Report, Receipt



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    pass


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    pass

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    pass

@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    pass
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    pass
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass
@admin.register(BillingInfo)
class PaymentAdmin(admin.ModelAdmin):
    pass
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_generado', 'tipo_reporte', 'año_académico')
    
@admin.register(Receipt)
class PaymentAdmin(admin.ModelAdmin):
    pass    