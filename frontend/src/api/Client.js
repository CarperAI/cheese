class Client {
	constructor(id) {
		this.id = id;
		this.socket = null;
		this.listeners = {
			error: this.#handleError
		};
	}

	#handleError(error) {
		console.error(error);
		this.socket.close();
		this.socket = null;
	}

	#assertConnected() {
		if (this.socket == null) {
			throw Error('Client not connected!');
		}
	}

	connect() {
		this.socket = new WebSocket('ws://localhost:8000/client/' + this.id);
		this.socket.addEventListener('open', () => {
			console.log('Connected to backend.');
		});
		this.socket.addEventListener('message', (event) => {
			const { type, payload } = JSON.parse(event.data || '{}');
			this.listeners[type]?.(payload);
		});
	}

	listen(type, callback) {
		if (type === 'error') {
			const userCallback = callback;
			callback = (error) => {
				this.#handleError(error);
				userCallback(error);
			};
		}
		this.listeners[type] = callback;
	}

	complete(payload) {
		this.#assertConnected();
		this.socket.send(
			JSON.stringify({
				type: 'complete',
				payload
			})
		);
	}

	ready() {
		this.#assertConnected();
		this.socket.send(
			JSON.stringify({
				type: 'ready'
			})
		);
	}
}

export default Client;
