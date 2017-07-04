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

def imp_msg(msg, tipo="aviso"):
	"""
	tipo: aviso, erro, sucesso
	"""
	if tipo == "aviso":
		print("\n[!] {}\n".format(msg))
	elif tipo == "erro":
		print("\n[-] {}\n".format(msg))
	elif tipo == "sucesso":
		print("\n[+] {}\n".format(msg))
	else:
		imp_msg("Tipo de mensagem não identificado: {}".format(tipo), "erro")

def main():
	imp_msg("Endereço IP do servidor: ")
	ip_servidor = input("> ")

	imp_msg("Número de porta do servidor: ")
	porta_servidor = int(input("> "))

	socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket_cliente.connect((ip_servidor, porta_servidor))

	loop_while = True
	while loop_while:
		input_cliente = input("> ")
		socket_cliente.send(input_cliente.encode())
		if input_cliente == "sair":
			loop_while = False

	socket_cliente.close()

if __name__ == '__main__':
	main()