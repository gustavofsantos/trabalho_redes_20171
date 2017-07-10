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


class Cliente():
	def __init__(self, ip_servidor, porta_servidor):
		self.ip_servidor = ip_servidor
		self.porta_servidor = porta_servidor

		imp_msg("Conectando com {}:{}".format(self.ip_servidor, self.porta_servidor))
		self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket_cliente.connect((self.ip_servidor, self.porta_servidor))
		imp_msg("Conectado com {}:{}".format(self.ip_servidor, self.porta_servidor), "sucesso")

		self.musicas = []

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

	def transmitir(self, musica):
		# comunica com o servidor
		try:
			self.socket_cliente.send("transmitir:{}".format(musica).encode())

			imp_msg("Solicitando a música {}...".format(musica))

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
				stream.write(dado)
				dado = self.socket_cliente.recv(bloco)
				#print("Recebeu ", len(dado))

			stream.stop_stream()
			#stream.close()
			#pa.close()
			imp_msg("Transmissão finalizada", "sucesso")
		except Exception as e:
			imp_msg("Erro na transmissão.", "erro")

	def executar(self):
		loop_while = True
		while loop_while:
			input_cliente = input("> ")
			
			if input_cliente == "sair":
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
						musica = self.musicas[int(input_cliente)]
						self.transmitir(musica)
					else:
						imp_msg("Música selecionada não existe.", "erro")
				else:
					imp_msg("Cache de musicas está vazio, faça uma listagem primeiro", "erro")

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