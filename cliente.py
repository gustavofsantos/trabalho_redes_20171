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
import sys
import random

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

def imp_ajuda():
    print('''
        Antes de tentar a transmissão de qualquer música, é preciso
        atualizar o cache local de músicas que estão disponíveis no
        servidor de transmissão.

        COMANDO     DESCRIÇÃO
        -----------------------------------------------------------
        listar      Faz uma requisição ao servidor conectado soli-
                    citando a listagem de músicas disponíveis. O
                    comando listar cria uma lista de reprodução
                    automaticamente com as músicas disponíveis no
                    servidor

        transmitir  Inicia uma transmissão de uma música contida no
                    cache local de músicas.

        pausar      Pausa a transmissão e a reprodução da música se
                    a transmissão está sendo executada ou continua a 
                    reprodução e a transmissão da música se esta se 
                    encontrar pausada.

        parar       Para a transmissão e a execução da música.

        prox        Solicita a próxima música na lista de reprodu-
                    ção (cache de músicas).

        ant         Solicita a música anterior na lista de reprodu-
                    ção (cache de músicas).

        aleat       Habilita/desabilita o modo de reprodução aleató-
                    rio.

        ajuda       Imprime esta mensagem de ajuda.

        sair        Finaliza a execução do programa.
        ''')

def imp_ajuda1():
    print('''
        COMANDO     DESCRIÇÃO
        -----------------------------------------------------------
        ajuda       Imprime esta mensagem de ajuda.

        conectar    Conecta a um servidor de transmissão usando o
                    número de IP e o número de porta.

        sair        Finaliza a execução do programa.
        ''')

class FinalizarTransmissao(Exception):
    pass

class ClienteTransmissao(threading.Thread):
    def __init__(self, ip_servidor, porta_servidor, musica, musicas, modo='normal'):
        self.ip = ip_servidor
        self.porta = porta_servidor
        self.musica = musica
        self.musicas = musicas
        self.modo = modo
        threading.Thread.__init__(self)
        self.daemon = True
        self.pausado = False
        self.tocando = False
        self.parar_exec = False
        self.estado = threading.Condition()

    def run(self):
        """
        Método que executa quando o método start() da classe pai é executado. Este
        método é responsável por lidar com a transmissão de dados do servidor para
        este cliente.
        """
        # comunica com o servidor
        self.tocando = True
        _musica = self.musica
        try:
            while 1:
                imp_msg("Conectando com {}:{}".format(self.ip, self.porta))

                self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_cliente.connect((self.ip, self.porta))

                imp_msg("Conectado com {}:{}".format(self.ip, self.porta), "sucesso")

                imp_msg("Solicitando a música {}...".format(_musica))
                self.socket_cliente.send("transmitir:{}".format(_musica).encode())          

                # recebe informações da música
                dados_musica = self.socket_cliente.recv(1024).decode()
                bloco, formato, canais, taxa = dados_musica.split(",")

                bloco = int(bloco)
                formato = int(formato)
                canais = int(canais)
                taxa = int(taxa)

                # envia o sinal para iniciar a transmissão
                self.socket_cliente.send("ok".encode())

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
                            raise FinalizarTransmissao

                    # se parar 
                    if self.parar_exec:
                        stream.stop_stream()
                        stream.close()
                        pa.terminate()
                        imp_msg("Transmissão finalizada", "sucesso")
                        self.socket_cliente.send("sair".encode())
                        self.tocando = False
                        raise FinalizarTransmissao

                    try:
                        stream.write(dado)
                        dado = self.socket_cliente.recv(bloco)
                    except KeyboardInterrupt as e:
                        imp_msg("Transmissão abortada")
                    except FinalizarTransmissao as e:
                        imp_msg("Transmissão finalizada antes do fim")
                    except Exception as e:
                        #imp_msg("Erro na transmissão.", "erro")
                        pass

                stream.stop_stream()
                stream.close()
                pa.terminate()
                imp_msg("Transmissão finalizada", "sucesso")
                self.socket_cliente.send("sair".encode())
                self.tocando = False

                # seleciona nova música para tocar em sequencia
                _id_atual = self.musicas.index(_musica)
                if self.modo == 'normal':
                    _prox_id = _id_atual + 1 if _id_atual < len(self.musicas) - 1 else 0
                    _musica = self.musicas[_prox_id]
                elif self.modo == 'aleat':
                    _musicas = [m for m in self.musicas if m != self.musica]
                    _musica = random.choice(_musicas)


        except KeyboardInterrupt as ki:
            # outras excessões
            stream.stop_stream()
            stream.close()
            pa.terminate()
            imp_msg("Transmissão finalizada", "sucesso")
            self.socket_cliente.send("sair".encode())
            self.tocando = False
        except FinalizarTransmissao as fe:
            imp_msg("Transmissão finalizada.", 'sucesso')
            print()
        except Exception as e:
            imp_msg("Erro na transmissão.", "erro")
            print(e)
            print()


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
        """
        Parar funciona como um botão, se estiver reproduzindo, a thread
        de transmissão é morta, senão, nada acontece
        """
        with self.estado:
            if self.parar_exec == False:
                self.parar_exec = True
            else:
                self.parar_exec = False

class Cliente():
    def __init__(self, ip_servidor, porta_servidor):
        self.ip_servidor = ip_servidor
        self.porta_servidor = porta_servidor

        try:
            imp_msg("Conectando com {}:{}...".format(self.ip_servidor, self.porta_servidor))
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.ip_servidor, self.porta_servidor))
            imp_msg("Conectado com {}:{}".format(self.ip_servidor, self.porta_servidor), "sucesso")
        except ConnectionRefusedError as e:
            imp_msg("Erro ao conectar com o servidor.", 'erro')
            sys.exit(1)

        self.musicas = []
        self.musica_atual = 0
        self.aleatorio = False

    def listar(self):
        # comunica com o servidor
        self.socket_cliente.send("listar".encode())
        self.musicas = self.socket_cliente.recv(2048).decode().split(",")

        print('''
        MÚSICAS DISPONÍVEIS
        -----------------------------------------------------------
        ID      NOME
        -----------------------------------------------------------''')
        cont = 0
        for musica in self.musicas:
            print("\t{}\t{}".format(cont, musica))
            cont = cont + 1
        print("\t-----------------------------------------------------------\n")

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
            input_cliente = ''
            try:
                input_cliente = input("> ")
            except KeyboardInterrupt as e:
                # pega ctrl+c
                fim = input("Finalizar [s | n]? ")
                if fim == 's':
                    # tenta parar a transmissão, se estiver transmitindo
                    try:
                        if self.ct.isAlive():
                            self.ct.parar()
                    except:
                        pass

                    self.socket_cliente.send("sair".encode())
                    self.socket_cliente.close()
                    sys.exit(1)
                elif fim == 'n':
                    pass
            
            if input_cliente == "sair":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
                except:
                    pass
                
                self.socket_cliente.send("sair".encode())
                loop_while = False
                self.socket_cliente.close()

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
                            modo = 'aleat' if self.aleatorio else 'normal'
                            self.ct.parar()
                            self.ct = None

                            nct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, self.musica_atual, self.musicas, modo)

                            self.ct = nct
                            self.ct.start()
                            self.ct.join(1)
                        except:
                            self.ct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, self.musica_atual, self.musicas, modo)
                            self.ct.start()
                            self.ct.join(1)
                    else:
                        imp_msg("Música selecionada não existe.", "erro")
                else:
                    imp_msg("Cache de musicas está vazio, faça uma listagem primeiro", "erro")
                    print("    Para fazer uma listagem, digite no prompt:")
                    print("    > listar")
            elif input_cliente == "pausar":
                try:
                    if self.ct.isAlive():
                        self.ct.pausar()
                    else:
                        imp_msg("Thread de transmissão não está executando.", "erro")
                except:
                    imp_msg("Nenhuma transmissão iniciada.", "erro")
            elif input_cliente == "parar":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
                    else:
                        imp_msg("Thread de transmissão não está executando.", "erro")
                except:
                    imp_msg("Nenhuma transmissão iniciada.", 'erro')
            elif input_cliente == "prox":
                try:
                    if self.ct.isAlive():
                        self.ct.parar()
    
                        atual = self.musicas.index(self.musica_atual)
                        if  not self.aleatorio:
                            prox = atual + 1 if atual < len(self.musicas) - 1 else 0
                            
                            prox_musica = self.musicas[prox]
                        else:
                            # monta uma lista com as musicas em cache menos a musica atual
                            _musicas = [musica for musica in self.musicas if musica != self.musica_atual]
                            prox_musica = random.choice(_musicas)
                        
                        modo = 'aleat' if self.aleatorio else 'normal'
                        nct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, prox_musica, self.musicas, modo)

                        self.ct = nct
                        self.ct.start()
                        self.ct.join(1)

                        self.musica_atual = prox_musica
                    else:
                        imp_msg("Thread de transmissão não está executando.", "erro")
                except Exception as e:
                    imp_msg("Erro ao trocar de musica", "erro")
                    imp_msg(e)
                    print()
            elif input_cliente == "ant":
                try:
                    if self.ct.isAlive():
                        # para a transmissão atual
                        self.ct.parar()

                        # seleciona a música atual
                        atual = self.musicas.index(self.musica_atual)

                        # troca para a faixa anterior
                        if not self.aleatorio:
                            prox = atual - 1 if atual > 0 else len(self.musicas) - 1
                            prox_musica = self.musicas[prox]
                        else:
                            _musicas = [musica for musica in self.musicas if musica != self.musica_atual]
                            prox_musica = random.choice(_musicas)

                        # lança um novo cliente de transmissão
                        modo = 'aleat' if self.aleatorio else 'normal'
                        nct = ClienteTransmissao(self.ip_servidor, self.porta_servidor, prox_musica, self.musicas, modo)

                        self.ct = nct
                        self.ct.start()
                        self.ct.join(1)

                        self.musica_atual = prox_musica

                except Exception as e:
                    imp_msg("Erro ao trocar de música", "erro")
                    imp_msg(e)
                    print()
            elif input_cliente == "aleat":
                self.aleatorio = not self.aleatorio
                if self.aleatorio:
                    imp_msg("Modo aleatório ligado", "sucesso")
                else:
                    imp_msg("Modo aleatório desligado", "sucesso")
            elif input_cliente == "ajuda":
                imp_ajuda()
        
def main():
    imp_msg("Entre com 'ajuda' para obter ajuda na execução.")
    executar = True

    while executar:
        try:
            input_cliente = input("> ")
        except KeyboardInterrupt as e:
            fim = input("Finalizar [s | n]? ")
            if fim == 's':
                sys.exit(1)
            elif fim == 'n':
                pass

        if input_cliente == "conectar":
            imp_msg("Endereço IP do servidor: ")
            ip_servidor = input("> ")

            imp_msg("Número de porta do servidor: ")
            porta_servidor = int(input("> "))

            # Inicia a conexão com o servidor e executa o modo COMANDO
            cliente = Cliente(ip_servidor, porta_servidor)
            cliente.executar()
            executar = False
        elif input_cliente == "ajuda":
            imp_ajuda1()
        elif input_cliente == "sair":
            executar = False

if __name__ == '__main__':
    main()