const fs = require('fs');
const path = require('path');
const Gpio = require('pigpio').Gpio;
const util = require('util');
const exec = util.promisify(require('child_process').exec);
const shortHash = require('short-hash');
const request = require('request-promise-native');
const Bravey = require("bravey");

const lightR = new Gpio(27, { mode: Gpio.OUTPUT });
const lightG = new Gpio(17, { mode: Gpio.OUTPUT });
const lightB = new Gpio(22, { mode: Gpio.OUTPUT });

async function play(sound) {
	const { stdout, stderr } = await exec('play sfx/' + sound);
	console.log('stdout:', stdout);
	console.log('stderr:', stderr);
}

async function say(text) {
	let hash = shortHash(text);
	let cmd  = `play speech-cache/${hash}.wav`;
	if (!fs.existsSync(path.join('speech-cache', hash + '.wav')))
		cmd = `pico2wave -w speech-cache/${hash}.wav "${text}" && ` + cmd;
		       //rm -f speech-cache/_${hash}.wav && ` + cmd;
		       //sox speech-cache/_${hash}.wav -r 48000 speech-cache/${hash}.wav &&
	console.log('Saying:', text);
	console.log(cmd);
	const { stdout, stderr } = await exec(cmd);
	console.log('stdout:', stdout);
	console.log('stderr:', stderr);
}

async function getJoke() {
	try {
		return await request({
			method: 'GET',
			url: 'https://icanhazdadjoke.com/',
			headers: {
				'User-Agent': 'Yousef Amar\'s personal home assistant (https://github.com/yousefamar/sanctum)'
			},
			json: true
		});
	} catch (e) {
		console.error('Error getting player info:', e);
	}
}

var nlp = new Bravey.Nlp.Fuzzy();
nlp.addDocument("Red alert", "red alert", { fromFullSentence: true, expandIntent: true });

var stream = fs.createReadStream('/home/amar/sanctum-listener');
stream.on('data', async d => {
	let input = d.toString();

	if (input.startsWith('#')) {
		input = input.substr(1).trim();
		console.log('Command:', input);
		switch (input) {
			case 'listening':
				lightB.pwmWrite(10);
				await play('computerbeep_10.mp3');
				break;
			case 'processing':
				lightB.pwmWrite(0);
				break;
			default:
				break;
		}
		return;
	}
	input = JSON.parse(input);
	if ('intent' in input.entities) {
		let i = input.entities.intent.findIndex(e => e.type === 'value' && e.value === 'joke');
		if (i >= 0) {
			let { joke } = await getJoke();
			await say(joke);
			return;
		}
	}
	let intent = nlp.test(input._text);
	switch (intent.intent) {
		case 'red alert':
				lightR.pwmWrite(10);
				await play('tos_red_alert_3.mp3');
				lightR.pwmWrite(0);
			break;
		default:
			break;
	}
	console.log(JSON.stringify(input, null, '  '));
});
