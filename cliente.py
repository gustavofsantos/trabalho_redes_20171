#!/usr/bin/python3
#! -*- coding: utf-8 -*-
"""
============================ REDES DE COMPUTADORES ============================
=                                                                             =
=                        Eduardo Model, Gustavo Santos                        =
=                    {efmodel, gfdsantos}@inf.ufpel.edu.br                    =
=                                    2017                                     =
=                                                                             =
========================== IMPLEMENTAÇÃO DO CLIENTE ===========================
"""
import socket
import pyaudio
import wave
import threading
import time
import subprocess

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
        imp_msg("Tipo de mensagem não identificado: {}".format(tipo), "erro")

class FinalizarTransmissao(Exception):
    pass

class ClienteTransmissao(threading.Thread):
    def __init__(self, ip_servidor, porta_servidor, musica):
        self.ip = ip_servidor
        self.porta = porta_servidor
        self.musica = musica
        threading.Thread.__init__(self)
        self.daemon = True
        self.pausado = False
        self.tocando = False
        self.parar_exec = False
        self.estado = threading.Condition()

    def run(self):
        # comunica com o servidor
        self.tocando = True
        try:
            imp_msg("Conectando com {}:{}".format(self.ip, self.porta))

            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.ip, self.porta))

            imp_msg("Conectado com {}:{}".format(self.ip, self.porta), "sucesso")

            imp_msg("Solicitando a música {}...".format(self.musica))
            self.socket_cliente.send("transmitir:{}".format(self.musica).encode())          

            # recebe informações da música
            dados_musica = self.socket_cliente.recv(1024).decode()
            bloco, formato, canais, taxa = dados_musica.split(",")

            bloco = int(bloco)
            formato = int(formato)
            canais = int(canais)
            taxa = int(taxa)

            # envia o sinal para iniciar a transmissão
            self.socket_cliente.send("ok".encode())
            imp_msg("ok", "sucesso")

            imp_msg("Abrindo canal para transmissão...")
            pa = pyaudio.PyAudio()
            stream = pa.open(format=formato, channels=canais, rate=taxa, output=True)

            # espera pelo primeiro bloco de dados
            dado = self.socket_cliente.recv(bloco)

            # escreve os bytes no buffer de execução de arquivos wav
            while len(dado) >= bloco:
                # fica no loop se a musica pausar
                while self.pausado:
                    if self.parar_exec:
                        stream.stop_stream()
                        stream.close()
                        pa.terminate()
                        imp_msg("Transmissão finalizada", "sucesso")
                        self.socket_cliente.send("sair".encode())
                        self.tocando = False
                        raise Exception

                # se parar 
                if self.parar_exec:
                    stream.stop_stream()
                    stream.close()
                    pa.terminate()
                    imp_msg("Transmissão finalizada", "sucesso")
                    self.socket_cliente.send("sair".encode())
                    self.tocando = False
                    raise Exception

                stream.write(dado)
                dado = self.socket_cliente.recv(bloco)
                #print("Recebeu ", len(dado))

            stream.stop_stream()
            stream.close()
            pa.terminate()
            imp_msg("Transmissão finalizada", "sucesso")
            self.socket_cliente.send("sair".encode())
            self.tocando = False
        except Exception as e:
            imp_msg("Erro na transmissão.\n{}".format(e), "erro")


    def pausar(self):
        """
        Pausar funciona como um botão, se a reprodução estiver pausada
        e o método pausar for executar, a reprodução começa novamente e
        se estiver reproduzindo e o pausar ser executado, a reprodução é
        pausada
        """
        with self.estado:
            if self.pausado == False:
                self.pausado = True
            else:
                self.pausado = False

    def parar(self):
        with self.estado:
            if self.parar_exec == False:
                self.parar_exec = True
            else:
                self.parar_exec = False

class Cliente():
    def __init__(self, ip_servidor, porta_servidor):
        self.ip_servidor = ip_servidor
        self.porta_servidor = porta_servidor

        imp_msg("Conectando com {}:{}".format(self.ip_servidor, self.porta_servidor))
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_cliente.connect((self.ip_servidor, self.porta_servidor))
        imp_msg("Conectado com {}:{}".format(self.ip_servidor, self.porta_servidor), "sucesso")

        self.musicas = []
        self.musica_atual = 0

    def listar(self):
        # comunica com o servidor
        self.socket_cliente.send("listar".encode())
        self.musicas = self.socket_cliente.recv(2048).decode().split(",")

        print("### MÚSICAS DISPONÍVEIS ###")
        cont = 0
        for musica in self.musicas:
            print("\t[{}] {}".format(cont, musica))
            cont = cont + 1

    def novo_usuario(self, usuario, senha):
        msg = "novo:{},{}".format(usuario, senha)
        self.socket_cliente.send(msg.encode())

    def transmitir(self, musica, modo):
        ct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, musica)
        ct.start()
        ct.join(1)


    def executar(self):
        loop_while = True
        while loop_while:
            input_cliente = input("> ")
            
            if input_cliente == "sair":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
                except:
                    pass
                    
                self.socket_cliente.send("sair".encode())
                loop_while = False

            elif input_cliente == "novo":
                # cria novo usuário
                imp_msg("Não implementado", "erro")
                # usuario = input("Nome de usuario: ")
                # senha = input("Senha do usuario: ")
                # self.novo_usuario(usuario, senha)

            elif input_cliente == "login":
                imp_msg("Não implementado", "erro")

            elif input_cliente == "listar":
                self.listar()

            elif input_cliente == "transmitir":
                print("Entre com o ID da música (número):")
                input_cliente = input("> ")
                if len(self.musicas) > 0:
                    # testa se o cliente está selecionando uma música invalida
                    if 0 <= int(input_cliente) < len(self.musicas):
                        self.musica_atual = self.musicas[int(input_cliente)]

                        try:
                            self.ct.parar()
                            self.ct = None
                            subprocess.run(["aconnect", "-x"])

                            nct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, self.musica_atual)

                            self.ct = nct
                            self.ct.start()
                            self.ct.join(1)
                        except:
                            self.ct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, self.musica_atual)
                            self.ct.start()
                            self.ct.join(1)

                    else:
                        imp_msg("Música selecionada não existe.", "erro")
                else:
                    imp_msg("Cache de musicas está vazio, faça uma listagem primeiro", "erro")
            elif input_cliente == "pausar":
                try:
                    if self.ct.isAlive():
                        self.ct.pausar()
                    else:
                        imp_msg("Thread de transmissão não está executando.")
                except:
                    imp_msg("Nenhuma transmissão iniciada.", "erro")
            elif input_cliente == "parar":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
                    else:
                        imp_msg("Thread de transmissão não está executando.")
                except:
                    imp_msg("Nenhuma transmissão iniciada.", 'erro')
            elif input_cliente == "prox":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
                        print("conseguiu parar")
                        atual = self.musicas.index(self.musica_atual)

                        prox = atual + 1 if atual < len(self.musicas) - 1 else 0
                        
                        prox_musica = self.musicas[prox]
                        
                        nct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, prox_musica)

                        self.ct = nct
                        self.ct.start()
                        self.ct.join(1)

                        self.musica_atual = prox_musica
                    else:
                        imp_msg("Thread de transmissão não está executando.")
                except Exception as e:
                    imp_msg("Erro ao trocar de musica")
            elif input_cliente == "ant":
                pass

        self.socket_cliente.close()


def main():
    imp_msg("Endereço IP do servidor: ")
    ip_servidor = input("> ")

    imp_msg("Número de porta do servidor: ")
    porta_servidor = int(input("> "))

    cliente = Cliente(ip_servidor, porta_servidor)
    cliente.executar()

if __name__ == '__main__':
    main()