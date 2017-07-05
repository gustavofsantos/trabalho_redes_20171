"""
============================ REDES DE COMPUTADORES ============================
=                                                                             =
=                        Eduardo Model, Gustavo Santos                        =
=                    {efmodel, gfdsantos}@inf.ufpel.edu.br                    =
=                                    2017                                     =
=                                                                             =
========================== IMPLEMENTAÇÃO DO SERVIDOR ==========================
"""
import socket
import threading
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
		imp_msg("Tipo de mensagem não identificado: {}\n".format(tipo), "erro")


class Cliente(threading.Thread):
	def __init__(self, cliente):
		threading.Thread.__init__(self)
		self.cliente = cliente

	def run(self):
		"""método que roda a conexão com o cliente na thread"""	
		bloco = 1024

		conexao_cliente, end_cliente = self.cliente
		imp_msg("Novo cliente {}".format(end_cliente))
		
		loop_while = True

		while loop_while:
			input_cliente = conexao_cliente.recv(1024).decode()
			imp_msg("${}: {}".format(end_cliente, input_cliente))
			if input_cliente == "sair":
				loop_while = False
			elif input_cliente == "transmitir":
				imp_msg("Iniciando transmissão...")
				try:
					arquivo = "musicas/Thunderstruck.wav"
					w_arquivo = wave.open(arquivo, "rb")
					pa = pyaudio.PyAudio()

					stream = pa.open(
						format=pa.get_format_from_width(w_arquivo.getsampwidth()),
						channels=w_arquivo.getnchannels(),
						rate=w_arquivo.getframerate(),
						output=True)

					# codifica as informações da musica
					# bloco, formato, canais, taxa
					info = "{},{},{},{}".format(bloco, pa.get_format_from_width(w_arquivo.getsampwidth()), w_arquivo.getnchannels(), w_arquivo.getframerate())

					# envia as informações da música
					conexao_cliente.send(info.encode())

					# espera pela confirmação do cliente
					input_cliente = conexao_cliente.recv(1024).decode()

					if input_cliente == "ok":
						imp_msg("Transmitindo a musica {}".format(arquivo.split('/')[1]))

						# primeira amostra
						dado = w_arquivo.readframes(bloco)

						# envia o arquivo de audio
						while dado:
							conexao_cliente.send(dado)
							dado = w_arquivo.readframes(bloco)

						conexao_cliente.send(''.encode())
					else:
						imp_msg("Cliente não confirmou os dados da música para transmissão", "erro")

				except Exception as e:
					imp_msg("Erro na transmissão", "erro")
					print(e)

		conexao_cliente.close()
		imp_msg("Conexão fechada de {}".format(end_cliente))


def main():
	# encapsula o servidor dentro de um bloco de excessão para capturar erros
	try:
		# define o endereço do servidor
		ip_servidor = socket.gethostbyname(socket.gethostname())
		porta = 9999

		imp_msg("Servidor iniciando em {}:{}...".format(ip_servidor, porta))

		# cria o socket do servidor e o coloca para escutar
		socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		socket_servidor.bind((ip_servidor, porta))
		socket_servidor.listen(3)

		imp_msg("Aguardando conexões. Pressione Ctrl+C para parar.", "sucesso")

		while True:
			conexao_cliente, end_cliente = socket_servidor.accept()
			try:
				if conexao_cliente != None:
					t_cliente = Cliente((conexao_cliente, end_cliente))
					t_cliente.start()
					#t_cliente.join()
				else:
					print("deu ruim")
			except:
				imp_msg("Falha na conexão com o cliente {}".format(end_cliente), "erro")
			
	except KeyboardInterrupt as erro:
		sys.exit(1)

if __name__ == '__main__':
	main()
