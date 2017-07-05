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

def main():
	imp_msg("Endereço IP do servidor: ")
	ip_servidor = input("> ")

	imp_msg("Número de porta do servidor: ")
	porta_servidor = int(input("> "))

	imp_msg("Conectando com {}:{}".format(ip_servidor, porta_servidor))
	socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_cliente.connect((ip_servidor, porta_servidor))
	imp_msg("Conectado com {}:{}".format(ip_servidor, porta_servidor), "sucesso")

	loop_while = True
	while loop_while:
		input_cliente = input("> ")
		socket_cliente.send(input_cliente.encode())
		if input_cliente == "sair":
			loop_while = False
		elif input_cliente == "transmitir":
			# recebe informações da música
			dados_musica = socket_cliente.recv(1024).decode()
			bloco, formato, canais, taxa = dados_musica.split(",")
			
			bloco = int(bloco)
			formato = int(formato)
			canais = int(canais)
			taxa = int(taxa)

			# envia o sinal para iniciar a transmissão
			socket_cliente.send("ok".encode())

			imp_msg("Abrindo canal para transmissão...")
			pa = pyaudio.PyAudio()
			stream = pa.open(format=formato, channels=canais, rate=taxa, output=True)

			# espera pelo primeiro bloco de dados
			dado = socket_cliente.recv(bloco)
			while len(dado) != 0:
				stream.write(dado)
				dado = socket_cliente.recv(bloco)

			stream.stop_stream()
			stream.close()
			pa.close()

	socket_cliente.close()

if __name__ == '__main__':
	main()