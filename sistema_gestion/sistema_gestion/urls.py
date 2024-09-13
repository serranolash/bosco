"""
URL configuration for sistema_gestion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# sigpcol/urls.py
from django.contrib import admin
from django.urls import path, include
from sigpcol import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('create_academic_year/', views.create_academic_year, name='create_academic_year'),
    path('create_grade/', views.create_grade, name='create_grade'),
    path('create_student/', views.create_student, name='create_student'),
    path('create_representative/', views.create_representative, name='create_representative'),
    path('create_payment/', views.create_payment, name='create_payment'),
    path('create_discount/', views.create_discount, name='create_discount'),
    path('student_list/<int:academic_year_id>/', views.student_list, name='student_list'),
    path('student_list/', views.select_academic_year, name='select_academic_year'),  # Nueva URL para seleccionar año académico
    path('payment_list/', views.payment_list, name='payment_list'),
    path('report_due_students/', views.report_due_students, name='report_due_students'),
    path('report_statistics/', views.report_statistics, name='report_statistics'),
    #path('report/payment/', views.report_payment, name='report_payment'),
    path('report/receipt/', views.report_receipt, name='report_receipt'),
    path('report_receipt/', views.report_receipt, name='report_receipt'),
    path('report/', views.report_overview, name='report_overview'),
    path('report/<int:report_id>/', views.report_detail, name='report_detail'),
    path('create_report/', views.create_report, name='create_report'),
    path('payment_detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('emitir_factura/<int:payment_id>/', views.emitir_factura, name='emitir_factura'),
    path('filtrar_representante/', views.emitir_factura_por_representante, name='emitir_factura_por_representante'),
    path('report_statistics/', views.report_statistics, name='report_statistics'),
    path('approve_payment/<int:payment_id>/', views.approve_payment, name='approve_payment'),
    path('reject_payment/<int:payment_id>/', views.reject_payment, name='reject_payment'),
    path('student/<int:student_id>/account-status/', views.student_account_status, name='student_account_status'),
    path('discounts/', views.discount_list, name='discount_list'),
    path('admin_user_accounts/', views.administrar_cuentas, name='admin_user_accounts'),
    path('password_reset/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('password_reset_confirm/<uidb64>/<token>/', views.MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('backup_database/', views.backup_database, name='backup_database'),
    path('restore_database/', views.restore_database, name='restore_database'),
    path('enviar_resumen_estado_cuenta/<int:student_id>/', views.enviar_resumen_estado_cuenta, name='enviar_resumen_estado_cuenta'),
    path('upload_users/', views.upload_users, name='upload_users'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('create_user/', views.create_user, name='create_user'),
    path('user_list/', views.user_list, name='user_list'),
    path('representatives/', views.representative_list, name='representative_list'),
    path('edit_representative/<int:representative_id>/', views.edit_representative, name='edit_representative'),
    path('delete_representative/<int:representative_id>/', views.delete_representative, name='delete_representative'),
    path('promote_students/', views.promote_students, name='promote_students'),
    path('edit_promotion/<int:cycle_id>/', views.edit_promotion, name='edit_promotion'),
    path('list_receipts/', views.list_receipts, name='list_receipts'),

    
    
]   + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
