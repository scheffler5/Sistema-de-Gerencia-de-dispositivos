
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CategoriasAtend(models.Model):
    nome = models.TextField()  # This field type is a guess.

    def __str__(self):
        return self.nome
    
    class Meta:
        managed = False
        db_table = 'categorias_atend'


class Chamados(models.Model):

    class SituacaoChoices(models.TextChoices):
        FEITO = 'FEITO', 'Feito'
        NAO_FEITO = 'NAO FEITO', 'Não Feito'
        ATRASADO = 'ATRASADO', 'Atrasado'
        PENDENTE = 'PENDENTE', 'Pendente'

    setores = models.ForeignKey('Setores', models.DO_NOTHING)
    usuario = models.ForeignKey('Usuarios', models.DO_NOTHING)
    dispositivos = models.ForeignKey('Dispositivos', models.DO_NOTHING)
    data_dia = models.DateField(blank=True, null=True)
    data_chamado = models.DateTimeField()
    data_finalizacao = models.DateTimeField()
    descricao_problema = models.TextField()
    nivel_atendimento_cliente = models.IntegerField()
    titulo = models.CharField(max_length=45)
    categoria = models.ForeignKey(
        'CategoriasAtend', 
        models.DO_NOTHING, 
        db_column='categoria_atend_id',  
        blank=True, 
        null=True
    )
    situacao = models.CharField(
        max_length=10,
        choices=SituacaoChoices.choices,
        default=SituacaoChoices.NAO_FEITO,
        blank=True, null=True # Adicione isto se a coluna no banco pode ser nula
    )

    @property
    def duracao(self):
        """Calcula a duração do chamado (tempo final - tempo inicial)."""
        if self.data_finalizacao and self.data_chamado:
            return self.data_finalizacao - self.data_chamado
        return None


    class Meta:
        managed = False
        db_table = 'chamados'


class Computadores(models.Model):
    nome = models.CharField(max_length=250)
    modelo = models.CharField(max_length=200)
    endereco_mac = models.CharField(unique=True, max_length=17)
    marca_processador = models.CharField(max_length=200)
    frequencia_processador = models.DecimalField(max_digits=4, decimal_places=2)
    velocidade_memoria = models.IntegerField()
    tamanho_memoria = models.IntegerField()
    tipo_armazenamento = models.TextField()  # This field type is a guess.
    tamanho_armazenamento = models.IntegerField()
    versao_so = models.CharField(max_length=100)
    ativo = models.BooleanField()
    potencia_fonte = models.IntegerField()
    ip_dispositivo = models.GenericIPAddressField(unique=True)
    data_instalacao = models.DateField()
    setor = models.ForeignKey('Setores', models.DO_NOTHING)

    def __str__(self):
        return self.nome
    
    class Meta:
        managed = False
        db_table = 'computadores'


class Dispositivos(models.Model):
    computadores = models.OneToOneField('Computadores', models.DO_NOTHING, blank=True, null=True)
    roteadores = models.OneToOneField('Roteadores', models.DO_NOTHING, blank=True, null=True)
    servidores = models.OneToOneField('Servidores', models.DO_NOTHING, blank=True, null=True)
    impressoras = models.OneToOneField('Impressoras', models.DO_NOTHING, blank=True, null=True)

    @property
    def nome_descritivo(self):
        """
        Retorna um nome amigável para o dispositivo,
        verificando qual relação não é nula.
        """
        if self.computadores:
            return f"Computador: {self.computadores.nome}"
        if self.servidores:
            return f"Servidor: {self.servidores.modelo} (ST: {self.servidores.service_tag})"
        if self.roteadores:
            return f"Roteador: {self.roteadores.modelo} (MAC: {self.roteadores.endereco_mac})"
        if self.impressoras:
            return f"Impressora: {self.impressoras.nome_impressora} (Serial: {self.impressoras.serial})"
        return f"Dispositivo ID {self.id} (Tipo desconhecido)"
    def __str__(self):
        return self.nome_descritivo
    class Meta:
        managed = False
        db_table = 'dispositivos'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class EmailsAntigos(models.Model):
    nome_email = models.CharField(max_length=100)
    tamanho_email = models.IntegerField()
    senha = models.CharField(max_length=45)
    setores = models.ForeignKey('Setores', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'emails_antigos'


class EmailsNovos(models.Model):
    nome_email = models.CharField(max_length=100)
    tamanho_email = models.IntegerField()
    senha = models.CharField(max_length=45)
    setores = models.ForeignKey('Setores', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'emails_novos'


class Hosts(models.Model):
    nome_host = models.CharField(max_length=100)
    ip_host = models.GenericIPAddressField(unique=True)

    def __str__(self):
        return self.nome_host
    
    class Meta:
        managed = False
        db_table = 'hosts'


class Impressoras(models.Model):
    modelo = models.CharField(max_length=45)
    toner = models.CharField(max_length=45)
    nome_impressora = models.CharField(max_length=150)
    proprietario = models.CharField(max_length=100)
    serial = models.CharField(unique=True, max_length=100)
    tipo_conexao = models.TextField()  # This field type is a guess.
    ip_dispositivo = models.GenericIPAddressField(unique=True, blank=True, null=True)
    setor = models.ForeignKey('Setores', models.DO_NOTHING)
    instalacao = models.DateField(blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'impressoras'


class LoginUsuarioPc(models.Model):
    nome_user = models.CharField(max_length=100)
    senha = models.CharField(max_length=100)
    computadores = models.ForeignKey(Computadores, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'login_usuario_pc'


class PastaPublica(models.Model):
    nome_user = models.CharField(max_length=100)
    senha = models.CharField(max_length=45)
    setores = models.ForeignKey('Setores', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pasta_publica'


class PlanoManuPrevent(models.Model):
    class SituacaoChoices(models.TextChoices):
        FEITO = 'FEITO', 'Feito'
        NAO_FEITO = 'NAO FEITO', 'Não Feito'
        ATRASADO = 'ATRASADO', 'Atrasado'

    data_manu = models.DateField()
    descricao = models.TextField()
    situacao = models.CharField(
        max_length=10,
        choices=SituacaoChoices.choices,
        default=SituacaoChoices.NAO_FEITO
    )
    
    dispositivos = models.ForeignKey(Dispositivos, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'plano_manu_prevent'


class Roteadores(models.Model):
    marca = models.CharField(max_length=45)
    modelo = models.CharField(max_length=45)
    endereco_mac = models.CharField(unique=True, max_length=17)
    ip_dispositivo = models.GenericIPAddressField(unique=True)
    data_instalacao = models.DateField()
    setor = models.ForeignKey('Setores', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'roteadores'


class Servidores(models.Model):
    modelo = models.CharField(max_length=200)
    marca = models.CharField(max_length=200)
    endereco_mac = models.CharField(unique=True, max_length=17)
    marca_processador = models.CharField(max_length=200)
    frequencia_processador = models.DecimalField(max_digits=4, decimal_places=2)
    velocidade_memoria = models.IntegerField()
    tamanho_memoria = models.IntegerField()
    tipo_armazenamento = models.TextField()  # This field type is a guess.
    tamanho_armazenamento = models.IntegerField()
    versao_so = models.CharField(max_length=100)
    ativo = models.BooleanField()
    express_code = models.CharField(max_length=100)
    service_tag = models.CharField(unique=True, max_length=45)
    ip_dispositivo = models.GenericIPAddressField(unique=True)
    data_instalacao = models.DateField()
    setor = models.ForeignKey('Setores', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'servidores'


class Setores(models.Model):
    nome = models.CharField(max_length=180)

    def __str__(self):
        # Esta linha diz ao Django: "Quando precisar mostrar um objeto Setor como texto,
        # use o valor do seu campo 'nome'."
        return self.nome

    class Meta:
        managed = False
        db_table = 'setores'


class Treinamentos(models.Model):
    setores = models.ForeignKey('Setores', models.DO_NOTHING, db_column='setor_id')
    descricao = models.TextField()
    data_trei = models.DateField(blank=True, null=True)
    data_ts_treinamento = models.DateTimeField()
    data_finalizacao = models.DateTimeField()
    titulo = models.CharField(max_length=45)

    @property
    def duracao(self):
        """Calcula a duração do registro do treinamento."""
        if self.data_finalizacao and self.data_ts_treinamento:
            return self.data_finalizacao - self.data_ts_treinamento
        return None

    class Meta:
        managed = False
        db_table = 'treinamentos'


class Usuarios(models.Model):
    nome = models.CharField(max_length=180)
    senha_hash = models.CharField(max_length=255)
    funcao = models.CharField(max_length=150)
    data_cadastro = models.DateField(auto_now_add=True)
    cpf = models.CharField(unique=True, max_length=11)

    def __str__(self):
        return self.nome
    
    class Meta:
        managed = False
        db_table = 'usuarios'

# Em dispositivos/models.py

class MonitoramentoHardware(models.Model):
    computadores = models.ForeignKey(Computadores, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_percent = models.FloatField()
    memory_percent = models.FloatField()
    disk_percent = models.FloatField()

    class Meta:
        managed = False # Mantenha como False se você for criar a tabela manualmente
        db_table = 'monitoramento_hardware'