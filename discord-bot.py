from threading import Thread
from scapy.all import sniff, get_windows_if_list, UDP
from amongUsParser.amongUsParser.gameEngine import gameState
import janus, discord
import re, time, os, asyncio, sys

## Token instructions from https://realpython.com/how-to-make-a-discord-bot-python/

## Fill in your own data here once you have made your bot
TOKEN = "" ## Your bot token
GUILD = "" ## Your guild name
ALIVE_VOICE_CHANNEL = "" ## Name of the voice channel for alive users
DEAD_VOICE_CHANNEL = "" ## Name of the voice channel for dead users

if not len(TOKEN):
	print("YOU NEED TO FILL IN YOUR BOT INFORMATION")
	sys.exit()
	

def strip(stripString):
	return re.sub(b"[^a-zA-Z0-9]+", b"", stripString)

class Bot(discord.Client):
	def __init__(self, q):
		super().__init__()
		self.q = q

		self.guild = False
		self.aliveChannel = False
		self.deadChannel = False
		self.channels = [ALIVE_VOICE_CHANNEL, DEAD_VOICE_CHANNEL]
		self.vcUsers = {}

		self.queue_task = self.loop.create_task(self.getQueueMsgs())

	async def getQueueMsgs(self):
		while 1:
			try:
				command = await self.q.get()
				if command:
					if command['type'] == "Reset":
						## Un-mute everyone
						await self.setAllAlive()
					if command['type'] == "Murdered":
						## Mute Player
						await self.setDead(command['name'])
					if command['type'] == "Exiled":
						## Mute Player
						await self.setDead(command['name'])
					if command['type'] == "JoinedGame":
						print("Joined Game!")
				self.q.task_done()
			except BaseException as e:
				print("GQM ERROR", str(e))

	async def setAllAlive(self):
		try:
			tasks = []
			for member in self.vcUsers.values():
				tasks.append(member.edit(voice_channel=self.aliveChannel)) ## bring back to life
			if len(tasks):
				await asyncio.wait(tasks)
		except BaseException as e:
			print("SAA ERROR", str(e))

	async def setDead(self, username):
		try:
			tasks = []
			for member in self.vcUsers.values():
				if strip(member.name.encode())[:10].lower() == strip(username)[:10].lower(): ## check first 10 chars for match. Strip chars that cant be set in game
					tasks.append(member.edit(voice_channel=self.deadChannel)) ## Send to heck
			if len(tasks):
				await asyncio.wait(tasks)
		except:
			print("SD ERROR", str(e))

	async def on_ready(self):
		for guild in self.guilds:
			if guild.name == GUILD:
				break

		self.guild = guild

		print(
			f'{self.user} is connected to the following guild:\n'
			f'{guild.name}(id: {guild.id})'
		)
		self.aliveChannel = discord.utils.get(guild.channels, name=ALIVE_VOICE_CHANNEL, type=discord.ChannelType.voice)

		self.deadChannel = discord.utils.get(guild.channels, name=DEAD_VOICE_CHANNEL, type=discord.ChannelType.voice)

		print("Alive Channel:", self.aliveChannel)
		print("Dead Channel:", self.deadChannel)
		print()

		memberIds = list(self.aliveChannel.voice_states.keys()) +  list(self.deadChannel.voice_states.keys())
		for mid in memberIds:
			try:
				self.vcUsers[mid]
			except:
				user = await self.guild.fetch_member(mid)
				self.vcUsers[mid] = user
		print("Ready to join games!")
		print()

	async def on_voice_state_update(self, member, before, after):
		if before.channel != after.channel: ## Channel changed
			try:
				beforeChannel = before.channel.name
			except:
				beforeChannel = False
			try:
				afterChannel = after.channel.name
			except:
				afterChannel = False

			if beforeChannel in self.channels or afterChannel in self.channels: ## To/From target channel
				if not (beforeChannel in self.channels and afterChannel in self.channels): ## Skip switching betweeen the two, only care about leaving / joining the pair

					if afterChannel in self.channels: ## join
						print("joined", member.name)
						self.vcUsers[member.id] = member

					if beforeChannel in self.channels: ## leave
						print("left", member.name)
						del self.vcUsers[member.id]


class interweave:
	def __init__(self, q):
		self.q = q
		self.game = gameState(self.callbacks())

	def pkt_callback(self, packet):
		self.game.proc(packet[UDP].payload.load, packet.time)


	def callbacks(self):
		return {
			'Reset': self.reset_callback,
			'Murdered': self.murdered_callback,
			'Exiled': self.exiled_callback,
			'JoinedGame': self.joinedGame_callback
		}
	
	def joinedGame_callback(self, ddict):
		msg = {'type': 'JoinedGame'}
		self.q.put(msg)

	def reset_callback(self, ddict):
		msg = {'type': 'Reset'}
		self.q.put(msg)

	def murdered_callback(self, ddict):
		msg = {'type': 'Murdered', 'name': ddict['player'].name}
		self.q.put(msg)

	def exiled_callback(self, ddict):
		msg = {'type': 'Exiled', 'name': ddict['player'].name}
		self.q.put(msg)

def pickInterface():
	if os.name == 'nt': ## windows friendly name method
		interfaces = get_windows_if_list()
		i = 0
		for interface in interfaces:
			print(i, interface['name'])
			i += 1
		return interfaces[int(input("Pick a number: "))]['name']
	else:
		interfaces = get_if_list()
		i = 0
		for interface in interfaces:
			print(i, interface)
			i += 1
		return interfaces[int(input("Pick a number: "))]

def sniffThread(q, interface, loop):
	asyncio.set_event_loop(loop)
	handler = interweave(q)
	sniff(iface=interface, prn=handler.pkt_callback, filter="port 22023 or port 22323 or port 22123 or port 22423 or port 22523 or port 22623 or port 22723 or port 22823 or port 22923", store=0)

def discordThread(q, loop):
	asyncio.set_event_loop(loop)
	bot = Bot(q)
	print("running bot")
	bot.run(TOKEN)

def main():
	interface = pickInterface()
	loop = asyncio.get_event_loop()
	queue = janus.Queue()
	
	sniffWorker = Thread(target=sniffThread, args=(queue.sync_q,interface, loop), daemon=True)
	discordWorker = Thread(target=discordThread, args=(queue.async_q,loop), daemon=True)

	sniffWorker.start()
	discordWorker.start()
	while 1:
		time.sleep(0.5)
	

if __name__ == "__main__":
	main()