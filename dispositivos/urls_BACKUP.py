from django.urls import path
from . import views

app_name = 'dispositivos'

urlpatterns = [
    # Rotas Principais e de Login
    path('login/', views.login_view, name='login'),
    path('', views.dashboard_view, name='dashboard'),
    
    # Rota do Inventário (o nome do caminho é 'inventario/')
    path('inventario/', views.inventario_view, name='inventario_geral'),
    
    # Rotas de Usuários
    path('usuarios/', views.listar_usuarios, name='lista_usuarios'),
    path('usuarios/novo/', views.cadastrar_usuario_view, name='cadastrar_usuario'),
    
    # Rotas de Módulos (Pastas, Hosts, Emails)
    path('pastas-publicas/', views.listar_pastas_publicas_view, name='lista_pastas_publicas'),
    path('pastas-publicas/nova/', views.cadastrar_pasta_publica_view, name='cadastrar_pasta_publica'),
    path('logins-pc/', views.listar_logins_pc_view, name='lista_logins_pc'),
    path('logins-pc/novo/', views.cadastrar_login_pc_view, name='cadastrar_login_pc'),
    path('hosts/', views.listar_hosts_view, name='lista_hosts'),
    path('hosts/novo/', views.cadastrar_host_view, name='cadastrar_host'),
    path('emails/novos/', views.listar_emails_novos_view, name='lista_emails_novos'),
    path('emails/novos/novo/', views.cadastrar_email_novo_view, name='cadastrar_email_novo'),
    path('emails/antigos/', views.listar_emails_antigos_view, name='lista_emails_antigos'),
    path('emails/antigos/novo/', views.cadastrar_email_antigo_view, name='cadastrar_email_antigo'),

    # Rotas de Treinamentos
    path('treinamentos/', views.listar_treinamentos, name='lista_treinamentos'),
    path('treinamentos/novo/', views.criar_treinamento_view, name='cria_treinamento'),
    
    # Rotas de Planos de Manutenção
    path('planos/', views.plano_manutencao_view, name='lista_planos'),
    path('planos/novo/', views.cadastrar_plano_view, name='cadastrar_plano'),
    
    # Rotas de Chamados
    path('chamados/', views.listar_chamados, name='lista_chamados'),
    path('chamados/novo/', views.cadastrar_chamado_view, name='cadastrar_chamado'),
    
    # Rota de Informações Gerais (Abas)
    path('informacoes/', views.visualizacao_geral, name='visualizacao_geral'),
    
    # ROTAS DE API
    path('api/get_device_details/', views.api_get_device_details, name='api_get_device_details'),
    path('api/save_device/', views.api_save_device, name='api_save_device'),
    path('api/planos_calendario/', views.api_planos_manutencao, name='api_planos_calendario'),
]