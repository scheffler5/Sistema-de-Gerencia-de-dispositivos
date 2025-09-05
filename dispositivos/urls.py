from django.urls import path
from . import views

app_name = 'dispositivos'

urlpatterns = [
    # Rotas Principais e de Login
    path('login/', views.login_view, name='login'),
    path('', views.dashboard_view, name='dashboard'),
    
    # Rota do Inventário
    path('inventario/', views.inventario_view, name='inventario_geral'),
    path('inventario/selecionar-tipo/', views.selecionar_tipo_dispositivo_view, name='selecionar_tipo_dispositivo'),
    path('inventario/novo/<str:tipo>/', views.dispositivo_form_view, name='cadastrar_dispositivo_tipo'),
    path('inventario/editar/<str:tipo>/<path:identificador>/', views.dispositivo_form_view, name='editar_dispositivo'),
    
    # Rotas de Usuários
    path('usuarios/', views.listar_usuarios_view, name='lista_usuarios'),
    path('usuarios/novo/', views.usuario_form_view, name='cadastrar_usuario'),
    path('usuarios/editar/<int:pk>/', views.usuario_form_view, name='editar_usuario'),
    
    # Rotas de Módulos (Pastas, Hosts, Emails)
    path('pastas-publicas/', views.listar_pastas_publicas_view, name='lista_pastas_publicas'),
    path('pastas-publicas/nova/', views.pasta_publica_form_view, name='cadastrar_pasta_publica'),
    path('pastas-publicas/editar/<int:pk>/', views.pasta_publica_form_view, name='editar_pasta_publica'),

    
    path('logins-pc/', views.listar_logins_pc_view, name='lista_logins_pc'),
    path('logins-pc/novo/', views.login_pc_form_view, name='cadastrar_login_pc'),
    path('logins-pc/editar/<int:pk>/', views.login_pc_form_view, name='editar_login_pc'),



    path('hosts/', views.listar_hosts_view, name='lista_hosts'),
    path('hosts/novo/', views.host_form_view, name='cadastrar_host'),
    path('hosts/editar/<int:pk>/', views.host_form_view, name='editar_host'),

    path('emails/novos/', views.listar_emails_novos_view, name='lista_emails_novos'),
    path('emails/novos/novo/', views.email_novo_form_view, name='cadastrar_email_novo'),
    path('emails/novos/editar/<int:pk>/', views.email_novo_form_view, name='editar_email_novo'),

    path('emails/antigos/', views.listar_emails_antigos_view, name='lista_emails_antigos'),
    path('emails/antigos/novo/', views.email_antigo_form_view, name='cadastrar_email_antigo'),
    path('emails/antigos/editar/<int:pk>/', views.email_antigo_form_view, name='editar_email_antigo'),

    # Rotas de Treinamentos
    path('treinamentos/', views.listar_treinamentos, name='lista_treinamentos'),
    #path('treinamentos/novo/', views.criar_treinamento_view, name='cria_treinamento'),
    path('treinamentos/novo/', views.treinamento_form_view, name='cadastrar_treinamento'),
    path('treinamentos/editar/<int:pk>/', views.treinamento_form_view, name='editar_treinamento'),


    
    # Rotas de Chamados
    path('chamados/', views.listar_chamados, name='lista_chamados'),
    path('chamados/novo/', views.chamado_form_view, name='cadastrar_chamado'),
    path('chamados/editar/<int:pk>/', views.chamado_form_view, name='editar_chamado'),
    
    # Rota de Informações Gerais (Abas)
    path('informacoes/', views.visualizacao_geral, name='visualizacao_geral'),
    
    # --- ROTAS DE API (As importantes para o modal) ---
    path('inventario/novo/', views.dispositivo_form_view, {'tipo': 'computador'}, name='cadastrar_dispositivo'),
    # Rota para o formulário de edição (tipo e id vêm da URL)
    path('inventario/editar/<str:tipo>/<path:identificador>/', views.dispositivo_form_view, name='editar_dispositivo'),
    

    path('api/get_device_details/', views.api_get_device_details, name='api_get_device_details'),
    path('api/save_device/', views.api_save_device, name='api_save_device'),
    path('api/planos_calendario/', views.api_planos_manutencao, name='api_planos_calendario'),


   # Rotas de Planos de Manutenção
    path('planos/', views.plano_manutencao_view, name='lista_planos'),
    path('planos/novo/', views.plano_manutencao_form_view, name='cadastrar_plano'),
    path('planos/editar/<int:pk>/', views.plano_manutencao_form_view, name='editar_plano'),
    path('planos/calendario/', views.plano_manutencao_view, name='calendario_planos'),

    path('relatorios/', views.relatorios_view, name='relatorios'),
    path('api/relatorio/', views.api_relatorio_view, name='api_relatorio'),
    path('relatorios/chamados/', views.relatorios_chamados_view, name='relatorios_chamados'),
    path('relatorios/computadores/', views.relatorios_computadores_view, name='relatorios_computadores'),
    path('relatorios/impressoras/', views.relatorios_impressoras_view, name='relatorios_impressoras'),
    path('relatorios/manutencoes/', views.relatorios_manutencoes_view, name='relatorios_manutencoes'),
    path('relatorios/roteadores/', views.relatorios_roteadores_view, name='relatorios_roteadores'),
    path('relatorios/servidores/', views.relatorios_servidores_view, name='relatorios_servidores'),
    path('relatorios/treinamentos/', views.relatorios_treinamentos_view, name='relatorios_treinamentos'),



    path('api/receive_monitoring/', views.api_receive_monitoring, name='api_receive_monitoring'),

    path('api/listar-computadores/', views.api_listar_computadores_view, name='api_listar_computadores'),
    path('api/monitoring-history/<int:computador_id>/', views.api_monitoring_history_view, name='api_monitoring_history'),

    path('exportar/', views.exportacao_relatorios_view, name='exportacao_relatorios'),
    path('api/preview-relatorio/', views.api_gerar_preview_relatorio, name='api_preview_relatorio'),
    path('exportar/pdf/', views.exportacao_relatorios_view, name='exportar_relatorio_pdf'),
    path('exportar/gerar-pdf-do-html/', views.exportar_html_para_pdf, name='exportar_html_para_pdf'),

]