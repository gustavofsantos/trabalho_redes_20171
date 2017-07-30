#!/usr/bin/spython3
#! -*- coding: utf-8 -*-
"""
============================ REDES DE COMPUTADORES ============================
=                                                                             =
=                        Eduardo Model, Gustavo Santos                        =
=                    {efmodel, gfdsantos}@inf.ufpel.edu.br                    =
=                                    2017                                     =
=                                                                             =
========================== IMPLEMENTAÇÃO DO SERVIDOR ==========================

    Cada cliente funciona como uma thread no servidor, assim é possível
    aceitar diversos clientes conectados e efetuando transmissões cada

"""
import socket
import threading
import pyaudio
import wave
import os
import sys


def imp_msg(msg, tipo="aviso"):
    """
    tipo: aviso, erro, sucesso
    """
    if tipo == "aviso":
        print("\n[!] {}".format(msg))
    elif tipo == "erro":
        print("\n[-] {}".format(msg))
    elif tipo == "sucesso":
        print("\n[+] {}".format(msg))
    else:
        imp_msg("Tipo de mensagem não identificado: {}\n".format(tipo), "erro")


class Cliente(threading.Thread):
    """Classe que implementa um cliente conectado ao servidor"""
    def __init__(self, cliente):
        threading.Thread.__init__(self)
        self.cliente = cliente
        self.conexao_cliente, self.end_cliente = self.cliente

    def novo_usuario(self, usuario, senha):
        # carregar a lista de usuarios

        # insere o novo usuario

        # libera para fazer o login
        pass

    def login_usuario(self, usuario, senha):
        # solicita a senha do usuario

        # carrega o ambiente do usuario
        pass

    def listar_musicas_diretorio(self):
        musicas = []
        # lista as músicas do diretório músicas
        for (d_caminho, d_nome, d_arquivos) in os.walk("musicas"):
            for d_arquivo in d_arquivos:
                musicas.append(d_arquivo.split('.')[0])

        s_musicas = ",".join(musicas)

        imp_msg("Comunicando com o cliente {}.".format(self.end_cliente))
        self.conexao_cliente.send(s_musicas.encode())
        imp_msg("{} bytes enviados para {}.".format(
            len(s_musicas), self.end_cliente))

    def transmitir(self, musica, comando):
        if comando == "tocar":
            bloco = 1024
            imp_msg("Iniciando transmissão...")
            try:
                arquivo = musica
                w_arquivo = wave.open(arquivo, "rb")
                pa = pyaudio.PyAudio()

                # abre o canal de transmissão
                stream = pa.open(
                    format=pa.get_format_from_width(w_arquivo.getsampwidth()),
                    channels=w_arquivo.getnchannels(),
                    rate=w_arquivo.getframerate(),
                    output=True)

                # codifica as informações da musica
                # bloco, formato, canais, taxa
                info = "{},{},{},{}".format(bloco, pa.get_format_from_width(
                    w_arquivo.getsampwidth()), w_arquivo.getnchannels(), w_arquivo.getframerate())

                # envia as informações da música
                self.conexao_cliente.send(info.encode())

                # espera pela confirmação do cliente
                input_cliente = self.conexao_cliente.recv(1024).decode()

                # se o cliente confirmar os dados da transmissão, então ela é iniciada
                if input_cliente == "ok":
                    imp_msg("Transmitindo a musica {} para {}.".format(
                        arquivo.split('/')[1], self.end_cliente))

                    # primeira amostra
                    tell_i = w_arquivo.tell()
                    dado = w_arquivo.readframes(bloco)
                    bs = True

                    # envia o arquivo de audio
                    while bs:
                        self.conexao_cliente.send(dado)
                        tell_i = w_arquivo.tell()
                        dado = w_arquivo.readframes(bloco)
                        tell = w_arquivo.tell()
                        if tell == tell_i:
                            bs = False

                    self.conexao_cliente.send('a'.encode())
                    imp_msg("Transmissão de {} finalizada.".format(
                        arquivo.split('/')[1]), "sucesso")
                else:
                    imp_msg(
                        "Cliente não confirmou os dados da música para transmissão", "erro")

            except Exception as e:
                imp_msg("Erro na transmissão", "erro")

    def run(self):
        """método que roda a conexão com o cliente na thread"""

        imp_msg("Novo cliente {}".format(self.end_cliente))

        self.loop_while = True
        self.transmitindo = False

        while self.loop_while:
            input_cliente = self.conexao_cliente.recv(1024).decode()
            imp_msg("${}: {}".format(self.end_cliente, input_cliente))

            if len(input_cliente.split(":")) > 1:
                comando, argumento = input_cliente.split(":")
            else:
                comando = input_cliente

            if comando == "sair":
                self.loop_while = False
                # finalizar o cliente
            elif comando == "login":
                # executa o login do usuário
                imp_msg("Não implementado", "erro")
                # usuario, senha = argumento.split(",")
                # self.login_usuario(usuario, senha)
            elif comando == "novo":
                imp_msg("Não implementado", "erro")
                # usuario, senha = argumento.split(",")
                # self.novo_usuario(usuario, senha)
            elif comando == "listar":
                # envia ao cliente uma listagem das musicas contidas no diretório de músicas
                self.listar_musicas_diretorio()
            elif comando == "transmitir":
                # transmite a musica selecionada ao cliente que a requisitou
                self.transmitindo = True
                self.transmitir("musicas/{}.wav".format(argumento), "tocar")  
            elif comando == "pausar":
                if self.transmitindo == True:
                    imp_msg("Pausar a música {}".format(argumento))
                else:
                    imp_msg("Servidor não está transmitindo para o cliente {}".format(self.end_cliente))

        self.conexao_cliente.close()
        imp_msg("Conexão fechada de {}".format(self.end_cliente))


def main():
    # encapsula o servidor dentro de um bloco de excessão para capturar erros
    try:
        # define o endereço do servidor
        ip_servidor = socket.gethostbyname(socket.gethostname())
        porta = 9992
        servidor_vivo = False

        while not servidor_vivo:
            try:
                imp_msg("Servidor iniciando em {}:{}...".format(ip_servidor, porta))
                # cria o socket do servidor e o coloca para escutar
                socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_servidor.bind((ip_servidor, porta))
                socket_servidor.listen(3)
                servidor_vivo = True
            except Exception as e:
                imp_msg("Erro ao iniciar o servidor na porta {}".format(porta))
                porta += 1

        imp_msg("Aguardando conexões. Pressione Ctrl+C para parar.", "sucesso")

        while True:
            conexao_cliente, end_cliente = socket_servidor.accept()
            try:
                if conexao_cliente != None:
                    t_cliente = Cliente((conexao_cliente, end_cliente))
                    t_cliente.start()
                    t_cliente.join(1)
                else:
                    print("deu ruim")
            except:
                imp_msg("Falha na conexão com o cliente {}".format(
                    end_cliente), "erro")

    except KeyboardInterrupt as erro:
        imp_msg("Saindo...")
        sys.exit(1)

if __name__ == '__main__':
    main()
