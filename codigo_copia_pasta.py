import time
import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

PASTA_MONITORADA = r"C:\Arquivo Empresas\Upload Drive"
PASTA_GOOGLE_DRIVE = r"I:\Meu Drive\Upload Drive"

class MonitorPasta(FileSystemEventHandler):
    def __init__(self):
        self.arquivos_processados = set()
        super().__init__()

    def on_created(self, event):
        """Lida com criação de arquivos e pastas"""
        if event.is_directory:
            print(f"📂 Pasta criada: {event.src_path}")
            self.copiar_estrutura_pastas(event.src_path)
        else:
            print(f"📄 Arquivo criado: {event.src_path}")
            self.processar_arquivo(event.src_path)
    
    def on_modified(self, event):
        """Lida com modificação de arquivos"""
        if not event.is_directory:
            print(f"📄 Arquivo modificado: {event.src_path}")
            self.processar_arquivo(event.src_path)
    
    def on_moved(self, event):
        """Lida com movimentação de arquivos e pastas"""
        if event.is_directory:
            print(f"📂 Pasta movida: {event.src_path} -> {event.dest_path}")
            self.copiar_estrutura_pastas(event.dest_path)
        else:
            print(f"📄 Arquivo movido: {event.src_path} -> {event.dest_path}")
            self.processar_arquivo(event.dest_path)

    def copiar_estrutura_pastas(self, caminho_pasta):
        """Copia a estrutura de pastas para o destino"""
        try:
            # Calcula o caminho relativo
            caminho_relativo = os.path.relpath(caminho_pasta, PASTA_MONITORADA)
            destino_pasta = os.path.join(PASTA_GOOGLE_DRIVE, caminho_relativo)
            
            # Cria a pasta no destino
            os.makedirs(destino_pasta, exist_ok=True)
            print(f"📂 Estrutura de pasta criada: {caminho_relativo}")
            
            # Agora copia todos os arquivos desta pasta
            for item in os.listdir(caminho_pasta):
                caminho_item = os.path.join(caminho_pasta, item)
                if os.path.isfile(caminho_item):
                    self.processar_arquivo(caminho_item)
                    
        except Exception as e:
            print(f"❌ Erro ao copiar estrutura de pastas {caminho_pasta}: {e}")

    def processar_arquivo(self, caminho_arquivo):
        """Processa e copia um arquivo individual"""
        try:
            # Verifica se é um arquivo válido
            if not os.path.isfile(caminho_arquivo):
                return
                
            nome_arquivo = os.path.basename(caminho_arquivo)
            
            # Ignora arquivos temporários e ocultos
            if (nome_arquivo.startswith('~') or 
                nome_arquivo.startswith('.') or 
                nome_arquivo.startswith('__')):
                return
            
            # Verifica se já processamos este arquivo recentemente
            if caminho_arquivo in self.arquivos_processados:
                return
            
            # Aguarda para garantir que o arquivo está completamente escrito
            print(f"⏳ Aguardando estabilização do arquivo: {nome_arquivo}")
            if not self.aguardar_arquivo_pronto(caminho_arquivo):
                print(f"❌ Arquivo não estabilizou: {nome_arquivo}")
                return
            
            # Calcula o caminho relativo para manter a estrutura de pastas
            caminho_relativo = os.path.relpath(caminho_arquivo, PASTA_MONITORADA)
            destino_completo = os.path.join(PASTA_GOOGLE_DRIVE, caminho_relativo)
            
            # Cria a pasta de destino se não existir
            pasta_destino = os.path.dirname(destino_completo)
            os.makedirs(pasta_destino, exist_ok=True)
            
            # Verifica se precisa copiar (comparando datas de modificação)
            if self.precisa_copiar(caminho_arquivo, destino_completo):
                print(f"🔄 Copiando: {caminho_relativo}")
                print(f"   De: {caminho_arquivo}")
                print(f"   Para: {destino_completo}")
                
                shutil.copy2(caminho_arquivo, destino_completo)
                self.arquivos_processados.add(caminho_arquivo)
                
                print(f"✅ COPIADO COM SUCESSO: {caminho_relativo}")
                print(f"   Horário: {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"📋 Arquivo já está atualizado: {caminho_relativo}")
                self.arquivos_processados.add(caminho_arquivo)
            
        except Exception as e:
            print(f"❌ ERRO ao processar {caminho_arquivo}: {str(e)}")

    def aguardar_arquivo_pronto(self, caminho_arquivo, timeout=10):
        """Aguarda até que o arquivo esteja pronto para cópia"""
        for i in range(timeout):
            try:
                # Tenta abrir o arquivo em modo leitura
                with open(caminho_arquivo, 'rb'):
                    pass
                
                # Verifica se o tamanho se estabilizou
                tamanho_atual = os.path.getsize(caminho_arquivo)
                time.sleep(0.5)
                tamanho_final = os.path.getsize(caminho_arquivo)
                
                if tamanho_atual == tamanho_final and tamanho_atual > 0:
                    return True
                    
            except (IOError, OSError):
                # Arquivo ainda está sendo escrito
                time.sleep(1)
                continue
        return False

    def precisa_copiar(self, origem, destino):
        """Verifica se o arquivo precisa ser copiado"""
        if not os.path.exists(destino):
            return True
            
        # Compara datas de modificação
        mod_origem = os.path.getmtime(origem)
        mod_destino = os.path.getmtime(destino)
        
        return mod_origem > mod_destino

def sincronizar_estrutura_completa():
    """Sincroniza toda a estrutura de pastas e arquivos existentes"""
    print("🔍 Sincronizando estrutura completa...")
    
    try:
        # Primeiro, cria toda a estrutura de pastas
        for root, dirs, files in os.walk(PASTA_MONITORADA):
            for dir_name in dirs:
                caminho_pasta = os.path.join(root, dir_name)
                caminho_relativo = os.path.relpath(caminho_pasta, PASTA_MONITORADA)
                destino_pasta = os.path.join(PASTA_GOOGLE_DRIVE, caminho_relativo)
                os.makedirs(destino_pasta, exist_ok=True)
                print(f"📂 Criada pasta: {caminho_relativo}")
        
        # Depois, copia todos os arquivos
        event_handler = MonitorPasta()
        for root, dirs, files in os.walk(PASTA_MONITORADA):
            for arquivo in files:
                caminho_completo = os.path.join(root, arquivo)
                print(f"📋 Sincronizando arquivo: {os.path.relpath(caminho_completo, PASTA_MONITORADA)}")
                event_handler.processar_arquivo(caminho_completo)
                
    except Exception as e:
        print(f"❌ Erro na sincronização inicial: {e}")

# ===== INICIALIZAÇÃO =====
print("=" * 60)
print("🔄 SISTEMA DE SINCRONIZAÇÃO COM GOOGLE DRIVE - ESTRUTURA COMPLETA")
print("=" * 60)

# Verificações iniciais
print("📋 Verificando configurações...")
print(f"📍 Pasta monitorada: {PASTA_MONITORADA}")
print(f"   Existe: {os.path.exists(PASTA_MONITORADA)}")

if not os.path.exists(PASTA_MONITORADA):
    print("❌ ERRO: Pasta monitorada não existe!")
    exit(1)

print(f"📍 Pasta do Drive: {PASTA_GOOGLE_DRIVE}")
print(f"   Existe: {os.path.exists(PASTA_GOOGLE_DRIVE)}")

# Cria a pasta base do Drive se não existir
os.makedirs(PASTA_GOOGLE_DRIVE, exist_ok=True)
print("✅ Pasta base do Drive verificada/criada")

# Sincroniza a estrutura completa existente
sincronizar_estrutura_completa()

# Inicializa e inicia o monitor
print("\n🎯 Iniciando monitoramento em tempo real...")
event_handler = MonitorPasta()
observer = Observer()
observer.schedule(event_handler, PASTA_MONITORADA, recursive=True)
observer.start()

print(f"\n✅ MONITORAMENTO ATIVO")
print(f"📁 Monitorando: {PASTA_MONITORADA}")
print(f"💾 Copiando para: {PASTA_GOOGLE_DRIVE}")
print("📝 Estrutura completa de subpastas será mantida")
print("\n💡 Funcionalidades:")
print("   - Criação de pastas é replicada automaticamente")
print("   - Arquivos em subpastas mantêm a estrutura original")
print("   - Modificações em arquivos são sincronizadas")
print("   - Movimentação de pastas/arquivos é tratada")
print("   - Pressione Ctrl+C para parar\n")

# Loop principal
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Parando monitoramento...")
    observer.stop()

observer.join()
print("✅ Monitoramento finalizado.")